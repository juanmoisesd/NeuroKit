namespace TelemetryControlCenterCore
{
    public class PolicyItem
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public object? CurrentValue { get; set; }
        public object RecommendedValue { get; set; } = null!;
        public string TechnicalJustification { get; set; } = string.Empty;
        public string EditionLimitations { get; set; } = string.Empty;

        public string RegistryPath { get; set; } = string.Empty;
        public string RegistryValueName { get; set; } = string.Empty;
        public RegistryKind RegistryType { get; set; } = RegistryKind.DWord;

        public bool IsOptimal => CurrentValue != null && CurrentValue.Equals(RecommendedValue);
    }

    public enum RegistryKind
    {
        DWord,
        String
    }
}
