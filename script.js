// ZZP Uurtarief Calculator 2025 Script

let fiscalParams = {
  year: 2025,
  tax_brackets_box1: [
    { up_to: 38441, rate: 0.3582 },
    { up_to: 75518, rate: 0.3748 },
    { up_to: null, rate: 0.4950 }
  ],
  zelfstandigenaftrek: 2470,
  startersaftrek: 2123,
  mkb_winstvrijstelling_rate: 0.127,
  algemene_heffingskorting: { max_amount: 3068, phase_out_start: 28406, phase_out_rate: 0.0667 },
  arbeidskorting: { max_amount: 5599, phase_out_start: 43071, phase_out_rate: 0.0651 }
};

document.addEventListener('DOMContentLoaded', function() {
  // Load JSON fiscal parameters if available
  fetch('data/fiscal_params_2025.json')
    .then(response => response.ok ? response.json() : null)
    .then(data => {
      if (data) fiscalParams = data;
      initCalculator();
    })
    .catch(() => initCalculator());
});

function initCalculator() {
  const inputs = ['netIncome', 'billableHours', 'vacationWeeks', 'sickWeeks', 'businessCosts', 'pensionContribution', 'insuranceCosts', 'startersaftrek'];

  // Read URL query parameters if present (for shareable URL feature)
  const urlParams = new URLSearchParams(window.location.search);
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (urlParams.has(id)) {
      if (el.type === 'checkbox') {
        el.checked = urlParams.get(id) === 'true';
      } else {
        el.value = urlParams.get(id);
      }
    }
    el.addEventListener('input', calculateRate);
    el.addEventListener('change', calculateRate);
  });

  const shareBtn = document.getElementById('shareBtn');
  if (shareBtn) {
    shareBtn.addEventListener('click', copyShareUrl);
  }

  // Initial calculation
  calculateRate();
}

function calculateBox1Tax(taxableIncome) {
  if (taxableIncome <= 0) return 0;

  let tax = 0;
  let prevLimit = 0;

  for (const bracket of fiscalParams.tax_brackets_box1) {
    const limit = bracket.up_to !== null ? bracket.up_to : Infinity;
    if (taxableIncome > prevLimit) {
      const taxableInBracket = Math.min(taxableIncome, limit) - prevLimit;
      tax += taxableInBracket * bracket.rate;
    }
    prevLimit = limit;
  }

  // Algemene heffingskorting calculation
  let ahk = fiscalParams.algemene_heffingskorting.max_amount;
  if (taxableIncome > fiscalParams.algemene_heffingskorting.phase_out_start) {
    ahk -= (taxableIncome - fiscalParams.algemene_heffingskorting.phase_out_start) * fiscalParams.algemene_heffingskorting.phase_out_rate;
  }
  ahk = Math.max(0, ahk);

  // Arbeidskorting calculation
  let ak = fiscalParams.arbeidskorting.max_amount;
  if (taxableIncome > fiscalParams.arbeidskorting.phase_out_start) {
    ak -= (taxableIncome - fiscalParams.arbeidskorting.phase_out_start) * fiscalParams.arbeidskorting.phase_out_rate;
  }
  ak = Math.max(0, ak);

  const totalTax = Math.max(0, tax - ahk - ak);
  return totalTax;
}

function calculateRate() {
  const netIncome = parseFloat(document.getElementById('netIncome').value) || 0;
  const billableHours = parseFloat(document.getElementById('billableHours').value) || 0;
  const vacationWeeks = parseFloat(document.getElementById('vacationWeeks').value) || 0;
  const sickWeeks = parseFloat(document.getElementById('sickWeeks').value) || 0;
  const businessCosts = parseFloat(document.getElementById('businessCosts').value) || 0;
  const pensionContribution = parseFloat(document.getElementById('pensionContribution').value) || 0;
  const insuranceCosts = parseFloat(document.getElementById('insuranceCosts').value) || 0;
  const applyStartersaftrek = document.getElementById('startersaftrek').checked;

  // Calculate annual billable hours
  const workingWeeks = Math.max(0, 52 - vacationWeeks - sickWeeks);
  const totalBillableHours = workingWeeks * billableHours;

  // Iteratively solve for gross profit before tax needed to get desired net income
  // Net = GrossProfit - Tax(GrossProfit - Deductions)
  let grossProfit = netIncome;
  let tax = 0;

  for (let i = 0; i < 20; i++) {
    let deductions = 0;
    // Zelfstandignaftrek & Startersaftrek
    deductions += fiscalParams.zelfstandigenaftrek;
    if (applyStartersaftrek) {
      deductions += fiscalParams.startersaftrek;
    }

    let profitAfterEntrepreneurDeductions = Math.max(0, grossProfit - deductions);
    let mkbVrijstelling = profitAfterEntrepreneurDeductions * fiscalParams.mkb_winstvrijstelling_rate;
    let taxableIncome = Math.max(0, profitAfterEntrepreneurDeductions - mkbVrijstelling);

    tax = calculateBox1Tax(taxableIncome);
    let calculatedNet = grossProfit - tax;

    let diff = netIncome - calculatedNet;
    if (Math.abs(diff) < 0.5) break;
    grossProfit += diff * 0.7; // convergence step
  }

  const grossTurnover = grossProfit + businessCosts + pensionContribution + insuranceCosts;
  const hourlyRate = totalBillableHours > 0 ? grossTurnover / totalBillableHours : 0;

  // Render Display Values
  document.getElementById('hourlyRateDisplay').innerHTML = `€ ${hourlyRate.toFixed(2)} <span class="per-hour">/ uur</span>`;
  document.getElementById('totalBillableHoursDisplay').textContent = `${Math.round(totalBillableHours)} uur`;
  document.getElementById('grossTurnoverDisplay').textContent = `€ ${Math.round(grossTurnover).toLocaleString('nl-NL')}`;

  // Breakdown Visualizer
  const total = grossTurnover > 0 ? grossTurnover : 1;
  const pensionInsurance = pensionContribution + insuranceCosts;

  const pctNet = ((netIncome / total) * 100).toFixed(1);
  const pctTax = ((tax / total) * 100).toFixed(1);
  const pctCosts = ((businessCosts / total) * 100).toFixed(1);
  const pctPension = ((pensionInsurance / total) * 100).toFixed(1);

  document.getElementById('segNet').style.width = `${pctNet}%`;
  document.getElementById('segTax').style.width = `${pctTax}%`;
  document.getElementById('segCosts').style.width = `${pctCosts}%`;
  document.getElementById('segPension').style.width = `${pctPension}%`;

  document.getElementById('valNet').textContent = `€ ${Math.round(netIncome).toLocaleString('nl-NL')}`;
  document.getElementById('pctNet').textContent = `${pctNet}%`;

  document.getElementById('valTax').textContent = `€ ${Math.round(tax).toLocaleString('nl-NL')}`;
  document.getElementById('pctTax').textContent = `${pctTax}%`;

  document.getElementById('valCosts').textContent = `€ ${Math.round(businessCosts).toLocaleString('nl-NL')}`;
  document.getElementById('pctCosts').textContent = `${pctCosts}%`;

  document.getElementById('valPension').textContent = `€ ${Math.round(pensionInsurance).toLocaleString('nl-NL')}`;
  document.getElementById('pctPension').textContent = `${pctPension}%`;

  updateUrlState();
}

function updateUrlState() {
  const params = new URLSearchParams();
  const inputs = ['netIncome', 'billableHours', 'vacationWeeks', 'sickWeeks', 'businessCosts', 'pensionContribution', 'insuranceCosts', 'startersaftrek'];

  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.type === 'checkbox') {
      params.set(id, el.checked);
    } else {
      params.set(id, el.value);
    }
  });

  const newUrl = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState({}, '', newUrl);
}

function copyShareUrl() {
  navigator.clipboard.writeText(window.location.href).then(() => {
    const btn = document.getElementById('shareBtn');
    const origText = btn.textContent;
    btn.textContent = '✅ URL Gekopieerd!';
    setTimeout(() => { btn.textContent = origText; }, 2000);
  });
}
