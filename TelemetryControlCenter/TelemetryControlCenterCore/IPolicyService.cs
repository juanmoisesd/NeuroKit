using System.Collections.Generic;

namespace TelemetryControlCenterCore
{
    public interface IPolicyService
    {
        List<PolicyItem> GetAvailablePolicies();
        void ScanPolicies(List<PolicyItem> policies);
        bool ApplyPolicy(PolicyItem policy);
        bool RollbackPolicy(PolicyItem policy);
    }
}
