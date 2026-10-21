using System.Collections.Generic;
using System.Linq;
using Moq;
using Xunit;
using TelemetryControlCenterCore;

namespace TelemetryControlCenterTests
{
    public class PolicyServiceTests
    {
        [Fact]
        public void ScanPolicies_ShouldPopulateCurrentValues()
        {
            // Arrange
            var mockRegistry = new Mock<IRegistryService>();
            mockRegistry.Setup(r => r.GetValue(It.IsAny<string>(), It.IsAny<string>()))
                        .Returns(1);

            var service = new PolicyService(mockRegistry.Object);
            var policies = service.GetAvailablePolicies().Take(1).ToList();

            // Act
            service.ScanPolicies(policies);

            // Assert
            Assert.Equal(1, policies[0].CurrentValue);
        }

        [Fact]
        public void ApplyPolicy_ShouldBackupAndApplyNewValue()
        {
            // Arrange
            var mockRegistry = new Mock<IRegistryService>();
            mockRegistry.Setup(r => r.GetValue(It.IsAny<string>(), It.IsAny<string>()))
                        .Returns(1); // Current value is 1

            var service = new PolicyService(mockRegistry.Object);
            var policy = service.GetAvailablePolicies().First(p => p.Id == "TelemetryLevel");
            policy.RecommendedValue = 0;

            // Act
            var result = service.ApplyPolicy(policy);

            // Assert
            Assert.True(result);
            Assert.Equal(0, policy.CurrentValue); // Policy should have the recommended value
            mockRegistry.Verify(r => r.SetValue(policy.RegistryPath, policy.RegistryValueName, 0, policy.RegistryType), Times.Once);
        }

        [Fact]
        public void RollbackPolicy_ShouldRestorePreviousValue_WhenApplied()
        {
            // Arrange
            var mockRegistry = new Mock<IRegistryService>();
            mockRegistry.Setup(r => r.GetValue(It.IsAny<string>(), It.IsAny<string>()))
                        .Returns(1); // Original value

            var service = new PolicyService(mockRegistry.Object);
            var policy = service.GetAvailablePolicies().First(p => p.Id == "TelemetryLevel");

            // Apply it first
            service.ApplyPolicy(policy);

            // Act
            var result = service.RollbackPolicy(policy);

            // Assert
            Assert.True(result);
            Assert.Equal(1, policy.CurrentValue); // Restored original value
            mockRegistry.Verify(r => r.SetValue(policy.RegistryPath, policy.RegistryValueName, 1, policy.RegistryType), Times.Once);
        }

        [Fact]
        public void RollbackPolicy_ShouldDeleteValue_WhenOriginalValueWasNull()
        {
            // Arrange
            var mockRegistry = new Mock<IRegistryService>();
            mockRegistry.Setup(r => r.GetValue(It.IsAny<string>(), It.IsAny<string>()))
                        .Returns(null); // Original value was null (didn't exist)

            var service = new PolicyService(mockRegistry.Object);
            var policy = service.GetAvailablePolicies().First(p => p.Id == "TelemetryLevel");

            // Apply it first
            service.ApplyPolicy(policy);

            // Act
            var result = service.RollbackPolicy(policy);

            // Assert
            Assert.True(result);
            Assert.Null(policy.CurrentValue);
            mockRegistry.Verify(r => r.DeleteValue(policy.RegistryPath, policy.RegistryValueName), Times.Once);
        }
    }
}
