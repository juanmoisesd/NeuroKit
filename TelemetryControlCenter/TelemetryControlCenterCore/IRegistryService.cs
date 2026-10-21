namespace TelemetryControlCenterCore
{
    public interface IRegistryService
    {
        object? GetValue(string path, string valueName);
        void SetValue(string path, string valueName, object value, RegistryKind kind);
        void DeleteValue(string path, string valueName);
    }
}
