// js/stats.js
// Statistics page logic

import { getClients, initClients } from './storage.js?v=4';
import { formatDate, getStatusLabel, getStatusClass, escapeHtml, setActiveNav } from './utils.js?v=4';

// ── Init ───────────────────────────────────────────────────────────────────

function init() {
  initClients();
  setActiveNav();
  renderStats();
  setupMobileMenu();
}

// ── Render ─────────────────────────────────────────────────────────────────

function renderStats() {
  const clients = getClients() || [];

  renderKPICards(clients);
  renderStatusBreakdown(clients);
  renderRecentClients(clients);
  renderMonthlyActivity(clients);
}

/** KPI summary cards */
function renderKPICards(clients) {
  const total = clients.length;
  const newCount = clients.filter(c => c.status === 'new').length;
  const activeCount = clients.filter(c => c.status === 'active').length;
  const completedCount = clients.filter(c => c.status === 'completed').length;
  const convRate = total > 0 ? Math.round((completedCount / total) * 100) : 0;

  setValue('statTotal', total);
  setValue('statNew', newCount);
  setValue('statActive', activeCount);
  setValue('statCompleted', completedCount);
  setValue('statConversion', convRate + '%');
}

function setValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

/** Status progress bars */
function renderStatusBreakdown(clients) {
  const total = clients.length;
  const statuses = [
    { key: 'new',       label: 'Новые клиенты',   count: clients.filter(c => c.status === 'new').length },
    { key: 'active',    label: 'В работе',         count: clients.filter(c => c.status === 'active').length },
    { key: 'completed', label: 'Завершённые',      count: clients.filter(c => c.status === 'completed').length }
  ];

  const container = document.getElementById('statusBreakdown');
  if (!container) return;

  container.innerHTML = statuses.map(s => {
    const pct = total > 0 ? Math.round((s.count / total) * 100) : 0;
    return `
      <div class="breakdown-item">
        <div class="breakdown-header">
          <span class="breakdown-label">
            <span class="breakdown-dot dot-${s.key}"></span>
            ${s.label}
          </span>
          <span class="breakdown-values">
            <strong>${s.count}</strong>
            <span class="breakdown-pct">${pct}%</span>
          </span>
        </div>
        <div class="progress-track">
          <div class="progress-fill fill-${s.key}" style="width:0" data-target="${pct}%"></div>
        </div>
      </div>
    `;
  }).join('');

  // Animate bars in on next frame
  requestAnimationFrame(() => {
    setTimeout(() => {
      container.querySelectorAll('.progress-fill').forEach(bar => {
        bar.style.width = bar.dataset.target;
      });
    }, 80);
  });
}

/** Recent 5 clients by date */
function renderRecentClients(clients) {
  const container = document.getElementById('recentClients');
  if (!container) return;

  const recent = [...clients]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 5);

  if (recent.length === 0) {
    container.innerHTML = '<p class="text-muted text-center">Нет данных</p>';
    return;
  }

  container.innerHTML = recent.map((c, i) => `
    <div class="recent-row" style="animation-delay:${i * 0.06}s">
      <span class="recent-rank">${i + 1}</span>
      <div class="recent-info">
        <span class="recent-name">${escapeHtml(c.fullName)}</span>
        <span class="recent-email">${escapeHtml(c.email)}</span>
      </div>
      <div class="recent-right">
        <span class="status-badge ${getStatusClass(c.status)}">${getStatusLabel(c.status)}</span>
        <span class="recent-date">${formatDate(c.createdAt)}</span>
      </div>
    </div>
  `).join('');
}

/** Last 6 months client additions bar chart */
function renderMonthlyActivity(clients) {
  const container = document.getElementById('monthlyActivity');
  if (!container) return;

  const months = getLast6Months();
  const counts = months.map(({ year, month }) =>
    clients.filter(c => {
      const d = new Date(c.createdAt);
      return d.getFullYear() === year && d.getMonth() === month;
    }).length
  );

  const max = Math.max(...counts, 1);

  container.innerHTML = months.map((m, i) => {
    const pct = Math.round((counts[i] / max) * 100);
    return `
      <div class="bar-col">
        <div class="bar-track">
          <div class="bar-fill" style="height:0" data-target="${pct}%"></div>
        </div>
        <span class="bar-count">${counts[i]}</span>
        <span class="bar-label">${m.label}</span>
      </div>
    `;
  }).join('');

  // Animate
  requestAnimationFrame(() => {
    setTimeout(() => {
      container.querySelectorAll('.bar-fill').forEach(bar => {
        bar.style.height = bar.dataset.target;
      });
    }, 120);
  });
}

/** Returns last 6 month descriptors */
function getLast6Months() {
  const result = [];
  const now = new Date();
  const MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    result.push({ year: d.getFullYear(), month: d.getMonth(), label: MONTH_NAMES[d.getMonth()] });
  }
  return result;
}

// ── Mobile Menu ────────────────────────────────────────────────────────────

function setupMobileMenu() {
  const toggle = document.getElementById('menuToggle');
  const navLinks = document.querySelector('.nav-links');
  if (!toggle || !navLinks) return;
  toggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    toggle.classList.toggle('open');
  });
}

// ── Boot ───────────────────────────────────────────────────────────────────
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    init();
  }
});
