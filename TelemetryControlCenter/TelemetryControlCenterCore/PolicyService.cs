using System;
using System.Collections.Generic;
using System.Linq;

namespace TelemetryControlCenterCore
{
    public class PolicyService : IPolicyService
    {
        private readonly IRegistryService _registryService;
        private readonly Dictionary<string, object?> _backupStore = new();

        public PolicyService(IRegistryService registryService)
        {
            _registryService = registryService;
        }

        public List<PolicyItem> GetAvailablePolicies()
        {
            return new List<PolicyItem>
            {
                // Telemetría
                new PolicyItem
                {
                    Id = "TelemetryLevel",
                    Name = "Deshabilitar Telemetría Principal",
                    Category = "Telemetría",
                    RecommendedValue = 0,
                    TechnicalJustification = "Reduce la recolección de datos de diagnóstico al mínimo indispensable.",
                    EditionLimitations = "En ediciones Home/Pro, el valor 0 equivale a 'Básico' (1).",
                    RegistryPath = @"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                    RegistryValueName = "AllowTelemetry",
                    RegistryType = RegistryKind.DWord
                },
                new PolicyItem
                {
                    Id = "DisableCEIP",
                    Name = "Deshabilitar CEIP",
                    Category = "Telemetría",
                    RecommendedValue = 0,
                    TechnicalJustification = "Evita participar en el Programa para la mejora de la experiencia del usuario (CEIP).",
                    EditionLimitations = "Todas",
                    RegistryPath = @"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\SQMClient\Windows",
                    RegistryValueName = "CEIPEnable",
                    RegistryType = RegistryKind.DWord
                },
                // Publicidad
                new PolicyItem
                {
                    Id = "DisableTailoredExperiences",
                    Name = "Deshabilitar Experiencias Personalizadas",
                    Category = "Publicidad",
                    RecommendedValue = 0,
                    TechnicalJustification = "Evita que Microsoft use datos de diagnóstico para ofrecer consejos y anuncios personalizados.",
                    EditionLimitations = "Todas",
                    RegistryPath = @"HKEY_CURRENT_USER\Software\Policies\Microsoft\Windows\CloudContent",
                    RegistryValueName = "DisableTailoredExperiencesWithDiagnosticData",
                    RegistryType = RegistryKind.DWord
                },
                new PolicyItem
                {
                    Id = "DisableConsumerFeatures",
                    Name = "Deshabilitar Instalación Automática de Apps Patrocinadas",
                    Category = "Publicidad",
                    RecommendedValue = 1,
                    TechnicalJustification = "Impide la instalación automática de juegos y aplicaciones de terceros tras iniciar sesión o actualizar.",
                    EditionLimitations = "Solo Enterprise y Education",
                    RegistryPath = @"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\CloudContent",
                    RegistryValueName = "DisableWindowsConsumerFeatures",
                    RegistryType = RegistryKind.DWord
                },
                // Privacidad
                new PolicyItem
                {
                    Id = "DisableCortana",
                    Name = "Deshabilitar Cortana",
                    Category = "Privacidad",
                    RecommendedValue = 0,
                    TechnicalJustification = "Desactiva el asistente virtual Cortana y la recolección de datos por voz.",
                    EditionLimitations = "Pro, Enterprise, Education",
                    RegistryPath = @"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                    RegistryValueName = "AllowCortana",
                    RegistryType = RegistryKind.DWord
                },
                new PolicyItem
                {
                    Id = "DisableWebSearch",
                    Name = "Deshabilitar Búsqueda Web en Menú Inicio",
                    Category = "Privacidad",
                    RecommendedValue = 1,
                    TechnicalJustification = "Evita que las búsquedas locales del menú inicio se envíen a Bing.",
                    EditionLimitations = "Todas",
                    RegistryPath = @"HKEY_CURRENT_USER\Software\Policies\Microsoft\Windows\Explorer",
                    RegistryValueName = "DisableSearchBoxSuggestions",
                    RegistryType = RegistryKind.DWord
                }
            };
        }

        public void ScanPolicies(List<PolicyItem> policies)
        {
            foreach (var policy in policies)
            {
                policy.CurrentValue = _registryService.GetValue(policy.RegistryPath, policy.RegistryValueName);
            }
        }

        public bool ApplyPolicy(PolicyItem policy)
        {
            try
            {
                // Backup current value ONLY if not already backed up
                if (!_backupStore.ContainsKey(policy.Id))
                {
                    var currentValue = _registryService.GetValue(policy.RegistryPath, policy.RegistryValueName);
                    _backupStore[policy.Id] = currentValue;
                }

                // Apply new value
                _registryService.SetValue(policy.RegistryPath, policy.RegistryValueName, policy.RecommendedValue, policy.RegistryType);
                policy.CurrentValue = policy.RecommendedValue;
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        public bool RollbackPolicy(PolicyItem policy)
        {
            try
            {
                if (!_backupStore.ContainsKey(policy.Id)) return false;

                var previousValue = _backupStore[policy.Id];
                if (previousValue == null)
                {
                    _registryService.DeleteValue(policy.RegistryPath, policy.RegistryValueName);
                }
                else
                {
                    _registryService.SetValue(policy.RegistryPath, policy.RegistryValueName, previousValue, policy.RegistryType);
                }

                policy.CurrentValue = previousValue;
                _backupStore.Remove(policy.Id);
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}
