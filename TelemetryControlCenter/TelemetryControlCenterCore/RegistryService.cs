using System;
using Microsoft.Win32;
using System.Runtime.Versioning;

namespace TelemetryControlCenterCore
{
    [SupportedOSPlatform("windows")]
    public class RegistryService : IRegistryService
    {
        public object? GetValue(string path, string valueName)
        {
            try
            {
                var (hive, subKey) = ParsePath(path);
                using var key = hive.OpenSubKey(subKey);
                return key?.GetValue(valueName);
            }
            catch
            {
                return null;
            }
        }

        public void SetValue(string path, string valueName, object value, RegistryKind kind)
        {
            var (hive, subKey) = ParsePath(path);
            using var key = hive.CreateSubKey(subKey);

            RegistryValueKind regKind = kind switch
            {
                RegistryKind.DWord => RegistryValueKind.DWord,
                RegistryKind.String => RegistryValueKind.String,
                _ => RegistryValueKind.Unknown
            };

            key?.SetValue(valueName, value, regKind);
        }

        public void DeleteValue(string path, string valueName)
        {
            try
            {
                var (hive, subKey) = ParsePath(path);
                using var key = hive.OpenSubKey(subKey, writable: true);
                key?.DeleteValue(valueName, throwOnMissingValue: false);
            }
            catch
            {
                // Ignore if it fails to delete (e.g., doesn't exist)
            }
        }

        private (RegistryKey hive, string subKey) ParsePath(string fullPath)
        {
            int firstSlash = fullPath.IndexOf('\\');
            if (firstSlash == -1) throw new ArgumentException("Ruta de registro inválida.");

            string root = fullPath.Substring(0, firstSlash).ToUpperInvariant();
            string subPath = fullPath.Substring(firstSlash + 1);

            RegistryKey hive = root switch
            {
                "HKEY_LOCAL_MACHINE" => Registry.LocalMachine,
                "HKLM" => Registry.LocalMachine,
                "HKEY_CURRENT_USER" => Registry.CurrentUser,
                "HKCU" => Registry.CurrentUser,
                _ => throw new ArgumentException($"Root key no soportada: {root}")
            };

            return (hive, subPath);
        }
    }
}
