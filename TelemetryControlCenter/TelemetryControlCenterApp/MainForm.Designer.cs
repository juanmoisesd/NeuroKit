namespace TelemetryControlCenterApp
{
    partial class MainForm
    {
        private System.ComponentModel.IContainer components = null;
        private System.Windows.Forms.DataGridView dgvPolicies;
        private System.Windows.Forms.Button btnScan;
        private System.Windows.Forms.Button btnApply;
        private System.Windows.Forms.Button btnRollback;
        private System.Windows.Forms.Label lblDisclaimer;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            this.dgvPolicies = new System.Windows.Forms.DataGridView();
            this.btnScan = new System.Windows.Forms.Button();
            this.btnApply = new System.Windows.Forms.Button();
            this.btnRollback = new System.Windows.Forms.Button();
            this.lblDisclaimer = new System.Windows.Forms.Label();

            var colName = new System.Windows.Forms.DataGridViewTextBoxColumn { DataPropertyName = "Name", HeaderText = "Política", Width = 200 };
            var colCategory = new System.Windows.Forms.DataGridViewTextBoxColumn { DataPropertyName = "Category", HeaderText = "Categoría", Width = 100 };
            var colCurrent = new System.Windows.Forms.DataGridViewTextBoxColumn { DataPropertyName = "CurrentValue", HeaderText = "Valor Actual", Width = 100 };
            var colRecommended = new System.Windows.Forms.DataGridViewTextBoxColumn { DataPropertyName = "RecommendedValue", HeaderText = "Recomendado", Width = 100 };
            var colLimits = new System.Windows.Forms.DataGridViewTextBoxColumn { DataPropertyName = "EditionLimitations", HeaderText = "Limitaciones de Edición", Width = 150 };
            var colJustification = new System.Windows.Forms.DataGridViewTextBoxColumn { DataPropertyName = "TechnicalJustification", HeaderText = "Justificación", Width = 300 };
            var colIsOptimal = new System.Windows.Forms.DataGridViewCheckBoxColumn { DataPropertyName = "IsOptimal", HeaderText = "Óptimo", ReadOnly = true, Width = 60 };

            this.dgvPolicies.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
                colName, colCategory, colCurrent, colRecommended, colLimits, colJustification, colIsOptimal
            });

            ((System.ComponentModel.ISupportInitialize)(this.dgvPolicies)).BeginInit();
            this.SuspendLayout();

            //
            // dgvPolicies
            //
            this.dgvPolicies.AllowUserToAddRows = false;
            this.dgvPolicies.AllowUserToDeleteRows = false;
            this.dgvPolicies.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dgvPolicies.Location = new System.Drawing.Point(12, 12);
            this.dgvPolicies.Name = "dgvPolicies";
            this.dgvPolicies.ReadOnly = true;
            this.dgvPolicies.RowHeadersVisible = false;
            this.dgvPolicies.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.dgvPolicies.Size = new System.Drawing.Size(1000, 400);
            this.dgvPolicies.TabIndex = 0;
            //
            // btnScan
            //
            this.btnScan.Location = new System.Drawing.Point(12, 420);
            this.btnScan.Name = "btnScan";
            this.btnScan.Size = new System.Drawing.Size(120, 30);
            this.btnScan.TabIndex = 1;
            this.btnScan.Text = "Analizar (Sólo lectura)";
            this.btnScan.UseVisualStyleBackColor = true;
            this.btnScan.Click += new System.EventHandler(this.btnScan_Click);
            //
            // btnApply
            //
            this.btnApply.Location = new System.Drawing.Point(150, 420);
            this.btnApply.Name = "btnApply";
            this.btnApply.Size = new System.Drawing.Size(150, 30);
            this.btnApply.TabIndex = 2;
            this.btnApply.Text = "Aplicar Seleccionado";
            this.btnApply.UseVisualStyleBackColor = true;
            this.btnApply.Click += new System.EventHandler(this.btnApply_Click);
            //
            // btnRollback
            //
            this.btnRollback.Location = new System.Drawing.Point(320, 420);
            this.btnRollback.Name = "btnRollback";
            this.btnRollback.Size = new System.Drawing.Size(150, 30);
            this.btnRollback.TabIndex = 3;
            this.btnRollback.Text = "Revertir Seleccionado";
            this.btnRollback.UseVisualStyleBackColor = true;
            this.btnRollback.Click += new System.EventHandler(this.btnRollback_Click);
            //
            // lblDisclaimer
            //
            this.lblDisclaimer.Location = new System.Drawing.Point(12, 465);
            this.lblDisclaimer.Name = "lblDisclaimer";
            this.lblDisclaimer.Size = new System.Drawing.Size(1000, 40);
            this.lblDisclaimer.TabIndex = 4;
            this.lblDisclaimer.Text = "Nota: Las políticas de Windows Defender, Firewall, SmartScreen, UAC y Windows Update se mantienen operativas por seguridad. Esta herramienta audita la configuración local del Registro, lo cual no siempre refleja el tráfico de red observado (algunas telemetrías no pueden eliminarse por completo).";
            //
            // MainForm
            //
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1024, 520);
            this.Controls.Add(this.lblDisclaimer);
            this.Controls.Add(this.btnRollback);
            this.Controls.Add(this.btnApply);
            this.Controls.Add(this.btnScan);
            this.Controls.Add(this.dgvPolicies);
            this.Name = "MainForm";
            this.Text = "Telemetry Control Center";
            ((System.ComponentModel.ISupportInitialize)(this.dgvPolicies)).EndInit();
            this.ResumeLayout(false);
        }
    }
}
