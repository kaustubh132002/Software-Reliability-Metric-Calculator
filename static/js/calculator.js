/**
 * Calculator module: Real-time SEQA reliability computations,
 * mathematical derivations, input validation, and preset scenarios.
 */

document.addEventListener('DOMContentLoaded', () => {
  initCalculator();
});

function initCalculator() {
  const opInput = document.getElementById('operating_time');
  const failInput = document.getElementById('failures');
  const repInput = document.getElementById('repair_time');
  const missionInput = document.getElementById('mission_time');

  if (!opInput || !failInput || !repInput) return;

  const inputs = [opInput, failInput, repInput, missionInput].filter(Boolean);
  inputs.forEach(input => {
    input.addEventListener('input', calculateReliability);
  });

  // Preset scenario selector
  const presetSelect = document.getElementById('presetScenarioSelect');
  if (presetSelect) {
    presetSelect.addEventListener('change', applyPresetScenario);
  }

  // Initial calculation on page load
  calculateReliability();
}

function calculateReliability() {
  const opTime = parseFloat(document.getElementById('operating_time')?.value) || 0;
  const failures = parseInt(document.getElementById('failures')?.value) || 0;
  const repTime = parseFloat(document.getElementById('repair_time')?.value) || 0;
  const missionTime = parseFloat(document.getElementById('mission_time')?.value) || 100;

  // Real-time values
  let mtbf = 0;
  let mttr = 0;
  let failureRate = 0;
  let availability = 0;
  let reliabilityMission = 0;

  if (opTime > 0) {
    failureRate = failures / opTime;
    mtbf = failures > 0 ? (opTime / failures) : opTime;
  }

  if (failures > 0) {
    mttr = repTime / failures;
  } else {
    mttr = repTime > 0 ? repTime : 0;
  }

  const totalTime = opTime + repTime;
  if (totalTime > 0) {
    availability = (opTime / totalTime) * 100;
  } else if (mtbf + mttr > 0) {
    availability = (mtbf / (mtbf + mttr)) * 100;
  } else {
    availability = failures === 0 ? 100 : 0;
  }
  availability = Math.min(100, Math.max(0, availability));

  // Mission Reliability R(t) = e^(-lambda * t)
  reliabilityMission = Math.exp(-failureRate * missionTime) * 100;

  // Update UI Elements
  updateMetricDisplay('res_mtbf', `${mtbf.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} hrs`);
  updateMetricDisplay('res_mttr', `${mttr.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} hrs`);
  updateMetricDisplay('res_fr', `${failureRate.toFixed(6)} / hr`);
  updateMetricDisplay('res_availability', `${availability.toFixed(3)}%`);
  updateMetricDisplay('res_mission_rel', `${reliabilityMission.toFixed(2)}%`);

  // Update status badge
  updateAvailabilityBadge(availability);

  // Update Step-by-Step Derivation Box
  updateDerivationBox(opTime, failures, repTime, mtbf, mttr, failureRate, availability, missionTime, reliabilityMission);
}

function updateMetricDisplay(elementId, text) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = text;
  }
}

function updateAvailabilityBadge(availability) {
  const badge = document.getElementById('res_availability_badge');
  if (!badge) return;

  if (availability >= 99.99) {
    badge.className = 'badge badge-success';
    badge.innerHTML = '<i class="fas fa-shield-alt"></i> Four 9s High Availability';
  } else if (availability >= 99.0) {
    badge.className = 'badge badge-primary';
    badge.innerHTML = '<i class="fas fa-check-circle"></i> Acceptable Production Tier';
  } else if (availability >= 95.0) {
    badge.className = 'badge badge-warning';
    badge.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Moderate Degradation';
  } else {
    badge.className = 'badge badge-danger';
    badge.innerHTML = '<i class="fas fa-times-circle"></i> Critical Reliability Risk';
  }
}

function updateDerivationBox(T, F, R, mtbf, mttr, lambda, avail, t, Rt) {
  const box = document.getElementById('stepByStepDerivation');
  if (!box) return;

  box.innerHTML = `
    <div style="font-size: 0.88rem; line-height: 1.6;">
      <p><b>1. MTBF (Mean Time Between Failures):</b></p>
      <code>MTBF = Total Operating Time (T) / Failures (F) = ${T} hrs / ${F} = <b>${mtbf.toFixed(2)} hrs</b></code>
      
      <p class="mt-2"><b>2. MTTR (Mean Time To Repair):</b></p>
      <code>MTTR = Total Repair Time (R) / Failures (F) = ${R} hrs / ${F || 1} = <b>${mttr.toFixed(2)} hrs</b></code>
      
      <p class="mt-2"><b>3. Failure Rate (&lambda;):</b></p>
      <code>&lambda; = Failures (F) / Operating Time (T) = ${F} / ${T || 1} = <b>${lambda.toFixed(6)} per hour</b></code>
      
      <p class="mt-2"><b>4. System Availability (A):</b></p>
      <code>A = [MTBF / (MTBF + MTTR)] &times; 100 = [${mtbf.toFixed(2)} / (${mtbf.toFixed(2)} + ${mttr.toFixed(2)})] &times; 100 = <b>${avail.toFixed(3)}%</b></code>

      <p class="mt-2"><b>5. Mission Reliability R(t=${t} hrs):</b></p>
      <code>R(${t}) = e^(-&lambda; &times; t) = e^(-${lambda.toFixed(6)} &times; ${t}) = <b>${Rt.toFixed(2)}%</b></code>
    </div>
  `;
}

function applyPresetScenario(e) {
  const val = e.target.value;
  const nameInput = document.getElementById('system_name');
  const catInput = document.getElementById('category');
  const opInput = document.getElementById('operating_time');
  const failInput = document.getElementById('failures');
  const repInput = document.getElementById('repair_time');
  const notesInput = document.getElementById('notes');

  const presets = {
    telecom: {
      name: 'High-Volume Telecom SIP Switch',
      category: 'Telecommunications',
      op: 8760,
      fail: 2,
      rep: 1.2,
      notes: 'Carrier-grade 99.99% availability target with automated node failover.'
    },
    ecommerce: {
      name: 'Black Friday E-Commerce Cart Engine',
      category: 'Web Application',
      op: 1440,
      fail: 5,
      rep: 7.5,
      notes: 'Monitored during high peak shopping season under extreme load.'
    },
    avionics: {
      name: 'DO-178C Flight Control Unit',
      category: 'Aerospace & Defense',
      op: 5000,
      fail: 1,
      rep: 0.25,
      notes: 'Triple modular redundant safety-critical avionics subsystem.'
    },
    banking: {
      name: 'FinTech Settlement Core Ledger',
      category: 'Banking & Financial',
      op: 3600,
      fail: 1,
      rep: 0.5,
      notes: 'Real-time atomic distributed transaction processor.'
    }
  };

  if (presets[val]) {
    const p = presets[val];
    if (nameInput) nameInput.value = p.name;
    if (catInput) catInput.value = p.category;
    if (opInput) opInput.value = p.op;
    if (failInput) failInput.value = p.fail;
    if (repInput) repInput.value = p.rep;
    if (notesInput) notesInput.value = p.notes;
    calculateReliability();
    showToast(`Loaded preset scenario: ${p.name}`, 'info');
  }
}
