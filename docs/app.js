(() => {
  'use strict';

  const REPOSITORY_URL = 'https://github.com/poojasri234/nyc-311-service-operations-analysis';
  const number = new Intl.NumberFormat('en-US');
  const oneDecimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  const twoDecimals = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 });

  const escapeHtml = (value) => String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  const asNumber = (value) => (Number.isFinite(Number(value)) ? Number(value) : 0);
  const count = (value) => number.format(asNumber(value));
  const pct = (value) => `${oneDecimal.format(asNumber(value))}%`;
  const hours = (value) => `${twoDecimals.format(asNumber(value))} h`;

  function setText(selector, value) {
    const el = document.querySelector(selector);
    if (el) el.textContent = value;
  }

  function setRows(selector, html) {
    const target = document.querySelector(`${selector} tbody`);
    if (target) target.innerHTML = html;
  }

  function renderKpis(metrics) {
    const cards = [
      { label: 'Records profiled', value: count(metrics.records_profiled), detail: 'Created on the selected snapshot date' },
      { label: 'Valid row rate', value: pct(metrics.valid_row_rate_percent), detail: 'Identifier and timestamp checks passed' },
      { label: 'Close timestamp rate', value: pct(metrics.closure_rate_percent), detail: `${count(metrics.closed_requests)} requests have a closed date` },
      { label: 'Resolution time', value: hours(metrics.median_resolution_hours), detail: `Median; P90 is ${hours(metrics.p90_resolution_hours)}` }
    ];
    const target = document.querySelector('#kpi-grid');
    target.innerHTML = cards.map((card) => `
      <article class="kpi-card">
        <span class="kpi-label">${escapeHtml(card.label)}</span>
        <strong class="kpi-value">${escapeHtml(card.value)}</strong>
        <span class="kpi-detail">${escapeHtml(card.detail)}</span>
      </article>`).join('');
  }

  function renderBars(rows, focusLabel) {
    const visibleRows = rows.slice(0, 8);
    const max = Math.max(...visibleRows.map((row) => asNumber(row.requests)), 1);
    const target = document.querySelector('#volume-bars');
    target.innerHTML = visibleRows.map((row) => {
      const amount = asNumber(row.requests);
      const width = Math.max(2, (amount / max) * 100);
      const isFocus = row.label === focusLabel;
      return `
        <div class="bar-row" tabindex="0" aria-label="${escapeHtml(row.label)}: ${count(amount)} requests">
          <span class="bar-label" title="${escapeHtml(row.label)}">${escapeHtml(row.label)}</span>
          <span class="bar-value">${count(amount)}</span>
          <div class="bar-track" aria-hidden="true"><div class="bar-fill${isFocus ? ' heat' : ''}" style="width: ${width.toFixed(1)}%"></div></div>
        </div>`;
    }).join('');
  }

  function renderTables(data) {
    setRows('#agency-table', data.agency_summary.slice(0, 8).map((row) => `
      <tr><td class="strong-cell">${escapeHtml(row.label)}</td><td class="numeric">${count(row.requests)}</td><td class="numeric">${pct(row.closure_rate_percent)}</td><td class="numeric">${hours(row.median_resolution_hours)}</td></tr>`).join(''));

    setRows('#complaint-table', data.top_complaint_types.map((row) => `
      <tr><td class="strong-cell">${escapeHtml(row.label)}</td><td class="numeric">${count(row.requests)}</td><td class="numeric">${pct(row.closure_rate_percent)}</td><td class="numeric">${hours(row.median_resolution_hours)}</td><td class="numeric">${hours(row.p90_resolution_hours)}</td></tr>`).join(''));

    setRows('#slow-table', data.slowest_comparable_complaint_types.slice(0, 8).map((row) => `
      <tr><td class="strong-cell">${escapeHtml(row.label)}</td><td class="numeric">${count(row.requests)}</td><td class="numeric">${hours(row.median_resolution_hours)}</td><td class="numeric">${hours(row.p90_resolution_hours)}</td></tr>`).join(''));

    setRows('#borough-table', data.borough_summary.map((row) => `
      <tr><td class="strong-cell">${escapeHtml(row.label)}</td><td class="numeric">${count(row.requests)}</td><td class="numeric">${pct(row.closure_rate_percent)}</td><td class="numeric">${hours(row.median_resolution_hours)}</td></tr>`).join(''));
  }

  function renderScenario(data) {
    const focus = data.metrics.watchlist_category;
    const scenario = data.recommendation_scenario;
    const baseHours = asNumber(scenario.recorded_elapsed_hours);

    setText('#focus-name', `${focus.label}: selected for a high-volume service-time review`);
    setText('#focus-rule', scenario.selection_rule);
    document.querySelector('#focus-grid').innerHTML = [
      ['Resolved requests', count(focus.resolved_requests)],
      ['Median elapsed time', hours(focus.median_resolution_hours)],
      ['Recorded elapsed time', hours(scenario.recorded_elapsed_hours)]
    ].map(([label, value]) => `<div class="focus-metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('');

    const slider = document.querySelector('#reduction-slider');
    const display = document.querySelector('#reduction-value');
    const result = document.querySelector('#scenario-result');
    const formula = document.querySelector('#scenario-formula');
    const update = () => {
      const reduction = asNumber(slider.value);
      const waitHours = baseHours * reduction / 100;
      display.value = `${reduction}%`;
      display.textContent = `${reduction}%`;
      result.value = `${oneDecimal.format(waitHours)} hours`;
      result.textContent = `${oneDecimal.format(waitHours)} hours`;
      formula.textContent = `${hours(scenario.recorded_elapsed_hours)} recorded elapsed time × ${reduction}% target.`;
    };
    slider.addEventListener('input', update);
    update();
  }

  function renderQuality(quality) {
    setText('#valid-rate', pct(quality.valid_row_rate_percent));
    const checks = [
      ['Raw records retained', `${count(quality.retained_records)} of ${count(quality.raw_records)}`],
      ['Duplicate unique keys removed', count(quality.duplicate_unique_keys_removed)],
      ['Missing unique key', count(quality.records_missing_unique_key)],
      ['Invalid created timestamp', count(quality.records_with_invalid_created_timestamp)],
      ['Closed before creation', count(quality.records_with_invalid_close_before_create)],
      ['Missing key business fields', count(quality.records_missing_borough + quality.records_missing_agency + quality.records_missing_complaint_type)],
      ['No closed date as extracted', count(quality.records_missing_closed_date)]
    ];
    document.querySelector('#dq-list').innerHTML = checks.map(([label, value]) => `<li><span>${escapeHtml(label)}</span><span>${escapeHtml(value)}</span></li>`).join('');
  }

  function renderPage(data) {
    document.title = data.project;
    setText('#source-scope', data.source.scope);
    document.querySelector('#dataset-link').href = data.source.dataset_url;
    document.querySelector('#source-card-link').href = data.source.dataset_url;
    setText('#hash-note', `Raw snapshot fingerprint: ${data.source.raw_snapshot_sha256}. Local snapshot file timestamp: ${data.source.local_snapshot_file_timestamp_utc}. The raw JSON is not published in this repository; rerun the documented query and build script to reproduce the analysis.`);

    renderKpis(data.metrics);
    renderBars(data.top_complaint_types, data.metrics.watchlist_category.label);
    renderTables(data);
    renderScenario(data);
    renderQuality(data.data_quality);

    const focus = data.metrics.watchlist_category;
    const scenario = data.recommendation_scenario;
    setText('#decision-title', `Prioritise a measured ${focus.label} service-time review.`);
    const scenarioAssumption = `${scenario.assumption.charAt(0).toLowerCase()}${scenario.assumption.slice(1)}`.replace(/[.]$/, '');
    document.querySelector('#decision-copy').innerHTML = `<strong>${escapeHtml(focus.label)}</strong> is the selected watchlist category because it has ${count(focus.requests)} requests and a ${hours(focus.median_resolution_hours)} median elapsed resolution time in this snapshot. Start with a root-cause review and a controlled escalation or triage pilot; measure the median and P90 elapsed time against a comparable period. The scenario below models ${escapeHtml(scenarioAssumption)}.`;

    // Keep the configured repository base in one place for easy reuse if the fork name changes.
    document.querySelectorAll(`a[href^="${REPOSITORY_URL}"]`).forEach((link) => link.setAttribute('referrerpolicy', 'no-referrer'));
  }

  async function init() {
    try {
      const response = await fetch('data.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`Could not load data.json (${response.status})`);
      const data = await response.json();
      renderPage(data);
    } catch (error) {
      console.error(error);
      const main = document.querySelector('main');
      const notice = document.createElement('div');
      notice.className = 'error-state';
      notice.setAttribute('role', 'alert');
      notice.textContent = 'The dashboard data could not be loaded. Run the documented build script to regenerate docs/data.json.';
      main.prepend(notice);
    }
  }

  init();
})();
