/**
 * kurl admin console
 * Single-page: login -> dashboard (analytics + approx-pairs).
 */

const STORAGE_KEY = 'kurl_admin_key';
const API_BASE = window.location.origin;

let apiKey = sessionStorage.getItem(STORAGE_KEY);
let days = 7;
let dashboardData = null;
let approxData = null;

// ----- helpers -----

function toast(msg, isError) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast show' + (isError ? ' toast-error' : '');
    setTimeout(() => t.className = 'toast', 2500);
}

async function api(path) {
    try {
        const r = await fetch(`${API_BASE}${path}`, { headers: { 'X-API-Key': apiKey } });
        if (r.status === 401) return { _unauthorized: true };
        if (!r.ok) return null;
        const json = await r.json();
        return json.data ?? json;
    } catch (e) {
        return null;
    }
}

function render(html) {
    document.getElementById('app').innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

// ----- login -----

function renderLogin() {
    render(`
        <div class="login-wrapper">
            <div class="login-card">
                <h1>kurl</h1>
                <div class="sub">admin console</div>
                <div class="login-error" id="loginError">Invalid API key</div>
                <input type="password" id="keyInput" placeholder="API key" autocomplete="off">
                <button class="btn" style="width:100%" onclick="login()">
                    <i data-lucide="log-in"></i> Enter
                </button>
            </div>
        </div>
    `);
    const input = document.getElementById('keyInput');
    input.focus();
    input.addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
}

async function login() {
    const key = document.getElementById('keyInput').value.trim();
    if (!key) return;
    apiKey = key;
    const d = await api('/api/events/summary?days=7');
    if (!d || d._unauthorized) {
        document.getElementById('loginError').style.display = 'block';
        apiKey = null;
        return;
    }
    sessionStorage.setItem(STORAGE_KEY, key);
    dashboardData = d;
    loadAndRender();
}

function logout() {
    sessionStorage.removeItem(STORAGE_KEY);
    apiKey = null;
    dashboardData = null;
    approxData = null;
    renderLogin();
}

// ----- dashboard -----

function setDays(d) {
    days = d;
    loadAndRender();
}

async function loadAndRender() {
    dashboardData = await api(`/api/events/summary?days=${days}`);
    approxData = await api(`/api/events/approx-pairs?days=${days}`);
    if (!dashboardData) {
        toast('Failed to load', true);
        return;
    }
    renderDashboard();
}

function rangeBtn(d, label) {
    return `<button class="tab-btn tab-btn-sm ${days === d ? 'active' : ''}" onclick="setDays(${d})">${label}</button>`;
}

function statCard(label, value) {
    return `<div class="stat-card"><div class="stat-value">${value ?? 0}</div><div class="stat-label">${label}</div></div>`;
}

function emptyRow(cols, msg) {
    return `<tr><td colspan="${cols}" class="empty">${msg}</td></tr>`;
}

function matchQualityRows(rows) {
    if (!rows || !rows.length) return emptyRow(4, 'No data');
    return rows.map(r => {
        const pct = r.total ? Math.round((r.exact / r.total) * 100) : 0;
        return `
            <tr>
                <td>${r.platform}</td>
                <td class="num">${r.exact}</td>
                <td class="num">${r.approx}</td>
                <td class="num"><span class="exact-bar" style="width:${pct}%"></span>${pct}%</td>
            </tr>`;
    }).join('');
}

function topListRows(rows, keyA, keyB) {
    if (!rows || !rows.length) return emptyRow(2, 'No data');
    return rows.map(r => `<tr><td>${r[keyA]}</td><td class="num">${r[keyB]}</td></tr>`).join('');
}

function approxRows(rows) {
    if (!rows || !rows.length) return emptyRow(3, 'No approx misses');
    return rows.map(r => {
        const url = r.sourceUrl || '';
        const short = url.length > 60 ? url.slice(0, 60) + '…' : url;
        return `
            <tr>
                <td><a href="${url}" target="_blank" rel="noopener">${short}</a></td>
                <td>${r.platform}</td>
                <td class="num">${r.misses}</td>
            </tr>`;
    }).join('');
}

function recentRows(rows) {
    if (!rows || !rows.length) return emptyRow(4, 'No events');
    return rows.slice(0, 10).map(r => `
        <tr>
            <td>${r.type}</td>
            <td>${r.platform || '-'}</td>
            <td>${r.via || '-'}</td>
            <td class="num">${(r.createdAt || '').slice(0, 19).replace('T', ' ')}</td>
        </tr>`).join('');
}

function renderDashboard() {
    const d = dashboardData;
    const ap = approxData;
    const totals = d.totals || {};
    const quality = d.matchQuality || [];

    render(`
        <div class="admin-header">
            <h1>kurl admin</h1>
            <button class="btn-icon" onclick="logout()" title="Logout"><i data-lucide="log-out"></i></button>
        </div>
        <div class="container">
            <div class="range-bar">
                ${rangeBtn(1, '1d')}
                ${rangeBtn(7, '7d')}
                ${rangeBtn(30, '30d')}
                ${rangeBtn(90, '90d')}
            </div>

            <div class="stat-grid">
                ${statCard('Kurls', totals.kurl)}
                ${statCard('Successes', totals.kurl_success)}
                ${statCard('Page views', totals.page_view)}
                ${statCard('Result opens', totals.open_result)}
            </div>

            <div class="section">
                <h2>Match quality per platform</h2>
                <div class="table-card">
                    <table>
                        <thead>
                            <tr><th>Platform</th><th class="num">Exact</th><th class="num">Approx</th><th class="num">Exact %</th></tr>
                        </thead>
                        <tbody>${matchQualityRows(quality)}</tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>Top approx misses (source URL → platform)</h2>
                <div class="table-card">
                    <table>
                        <thead>
                            <tr><th>Source URL</th><th>Target</th><th class="num">Misses</th></tr>
                        </thead>
                        <tbody>${approxRows(ap && ap.pairs)}</tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>Top platforms (kurls)</h2>
                <div class="table-card">
                    <table>
                        <thead><tr><th>Platform</th><th class="num">Count</th></tr></thead>
                        <tbody>${topListRows(d.topPlatforms, 'platform', 'count')}</tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>Countries</h2>
                <div class="table-card">
                    <table>
                        <thead><tr><th>Country</th><th class="num">Count</th></tr></thead>
                        <tbody>${topListRows(d.countries, 'country', 'count')}</tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>Recent events</h2>
                <div class="table-card">
                    <table>
                        <thead><tr><th>Type</th><th>Platform</th><th>Via</th><th class="num">When (UTC)</th></tr></thead>
                        <tbody>${recentRows(d.recent)}</tbody>
                    </table>
                </div>
            </div>
        </div>
    `);
}

// ----- boot -----

if (apiKey) {
    loadAndRender();
} else {
    renderLogin();
}
