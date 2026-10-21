using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using TelemetryControlCenterCore;

namespace TelemetryControlCenterApp
{
    public partial class MainForm : Form
    {
        private readonly IPolicyService _policyService;
        private List<PolicyItem> _policies;

        public MainForm()
        {
            InitializeComponent();
            _policyService = new PolicyService(new RegistryService());
            _policies = _policyService.GetAvailablePolicies();
            LoadData();
        }

        private void LoadData()
        {
            dgvPolicies.AutoGenerateColumns = false;
            dgvPolicies.DataSource = _policies;
        }

        private void btnScan_Click(object sender, EventArgs e)
        {
            try
            {
                _policyService.ScanPolicies(_policies);
                dgvPolicies.Refresh();
                MessageBox.Show("Análisis completado.", "Éxito", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al analizar: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnApply_Click(object sender, EventArgs e)
        {
            if (dgvPolicies.CurrentRow?.DataBoundItem is PolicyItem policy)
            {
                var result = MessageBox.Show($"¿Deseas aplicar el cambio para: {policy.Name}?\n\nJustificación: {policy.TechnicalJustification}",
                                             "Confirmar", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (result == DialogResult.Yes)
                {
                    bool success = _policyService.ApplyPolicy(policy);
                    if (success)
                    {
                        dgvPolicies.Refresh();
                        MessageBox.Show("Política aplicada y respaldada exitosamente.", "Éxito", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        MessageBox.Show("No se pudo aplicar la política. Verifica permisos de administrador.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
        }

        private void btnRollback_Click(object sender, EventArgs e)
        {
            if (dgvPolicies.CurrentRow?.DataBoundItem is PolicyItem policy)
            {
                var result = MessageBox.Show($"¿Deseas revertir el cambio para: {policy.Name}?",
                                             "Confirmar", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (result == DialogResult.Yes)
                {
                    bool success = _policyService.RollbackPolicy(policy);
                    if (success)
                    {
                        dgvPolicies.Refresh();
                        MessageBox.Show("Política revertida exitosamente a su estado anterior.", "Éxito", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        MessageBox.Show("No se encontró un respaldo o falló la reversión.", "Advertencia", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
            }
        }
    }
}
