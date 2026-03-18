// js/main.js
// Main page logic: render clients, search, filter, status change, delete

import {
  initClients, getClients, updateClient, deleteClient
} from './storage.js?v=4';
import {
  formatDate, getInitials, getStatusLabel, getStatusClass,
  getAvatarColor, escapeHtml, showToast, debounce, setActiveNav
} from './utils.js?v=4';

// ── State ──────────────────────────────────────────────────────────────────

let currentFilter = 'all';
let currentSearch = '';

// Guard: event listeners are attached once and survive bfcache restores.
// Setting this flag prevents duplicate listeners on pageshow re-init.
let listenersAttached = false;

// ── Init ───────────────────────────────────────────────────────────────────

/**
 * Full initialization — called on first page load.
 * Seeds storage, renders UI, attaches all event listeners.
 */
function init() {
  console.log('[CRM] init() — readyState:', document.readyState);
  initClients();
  setActiveNav();
  renderClients();

  if (!listenersAttached) {
    setupSearch();
    setupFilters();
    setupMobileMenu();
    listenersAttached = true;
  }
}

/**
 * Soft re-init — called when page is restored from bfcache (back/forward).
 * Re-renders content from localStorage but does NOT re-attach listeners
 * because they are still alive on the restored DOM.
 */
function reinit() {
  console.log('[CRM] reinit() — bfcache restore');
  setActiveNav();
  renderClients();
}

// ── Render ─────────────────────────────────────────────────────────────────

function renderClients() {
  const allClients = getClients();
  console.log('[CRM] renderClients() —', allClients.length, 'total clients in storage:', allClients);

  const filtered = filterClients(allClients);

  const grid = document.getElementById('clientsGrid');
  const shownCount = document.getElementById('clientCount');
  const totalCount = document.getElementById('totalCount');

  if (!grid) {
    console.error('[CRM] renderClients: #clientsGrid not found in DOM');
    return;
  }

  if (shownCount) shownCount.textContent = filtered.length;
  if (totalCount) totalCount.textContent = allClients.length;

  updateFilterBadges(allClients);

  if (filtered.length === 0) {
    grid.innerHTML = buildEmptyState();
    return;
  }

  grid.innerHTML = '';
  filtered.forEach((client, index) => {
    const card = buildClientCard(client, index);
    grid.appendChild(card);
  });
}

/** Apply current filter + search to client array */
function filterClients(clients) {
  return clients.filter(client => {
    const matchesFilter = currentFilter === 'all' || client.status === currentFilter;
    const q = currentSearch.toLowerCase();
    const matchesSearch =
      !q ||
      (client.fullName  && client.fullName.toLowerCase().includes(q)) ||
      (client.email     && client.email.toLowerCase().includes(q))    ||
      (client.phone     && client.phone.includes(q));
    return matchesFilter && matchesSearch;
  });
}

/** Build a client card DOM element */
function buildClientCard(client, index) {
  const card = document.createElement('article');
  card.className = 'client-card';
  card.style.animationDelay = `${index * 0.055}s`;
  card.dataset.id = client.id;

  const initials    = getInitials(client.fullName);
  const color       = getAvatarColor(client.fullName);
  const statusClass = getStatusClass(client.status);
  const statusLabel = getStatusLabel(client.status);
  const date        = formatDate(client.createdAt);

  card.innerHTML = `
    <div class="card-header">
      <div class="client-avatar" style="background:${color}18;color:${color};border:2px solid ${color}35">
        ${initials}
      </div>
      <div class="client-meta">
        <h3 class="client-name">${escapeHtml(client.fullName)}</h3>
        <a href="mailto:${escapeHtml(client.email)}" class="client-email">
          ${escapeHtml(client.email)}
        </a>
      </div>
      <span class="status-badge ${statusClass}">${statusLabel}</span>
    </div>

    <div class="card-body">
      ${client.phone ? `
        <div class="detail-row">
          <svg class="detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.81a19.79 19.79 0 01-3.07-8.64A2 2 0 012.11.13h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.91 7.09a16 16 0 006 6l.46-.46a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 14.92z"/>
          </svg>
          <span>${escapeHtml(client.phone)}</span>
        </div>
      ` : ''}
      ${client.comment ? `
        <div class="detail-row detail-comment">
          <svg class="detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
          </svg>
          <span class="comment-text">${escapeHtml(client.comment)}</span>
        </div>
      ` : ''}
    </div>

    <div class="card-footer">
      <div class="card-date">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="4" width="18" height="18" rx="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        ${date}
      </div>
      <div class="card-actions">
        <select class="status-select" data-id="${client.id}" title="Сменить статус">
          <option value="new"       ${client.status === 'new'       ? 'selected' : ''}>Новый</option>
          <option value="active"    ${client.status === 'active'    ? 'selected' : ''}>В работе</option>
          <option value="completed" ${client.status === 'completed' ? 'selected' : ''}>Завершён</option>
        </select>
        <a href="form.html?edit=${client.id}" class="btn-icon btn-edit" title="Редактировать">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </a>
        <button class="btn-icon btn-delete" data-id="${client.id}" title="Удалить клиента">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
          </svg>
        </button>
      </div>
    </div>
  `;

  // Attach events directly on the card element (safe: card is new each render)
  card.querySelector('.status-select').addEventListener('change', function () {
    handleStatusChange(client.id, this.value, card);
  });

  card.querySelector('.btn-delete').addEventListener('click', function () {
    handleDelete(client.id, client.fullName);
  });

  return card;
}

// ── Event Handlers ─────────────────────────────────────────────────────────

function handleStatusChange(id, newStatus, card) {
  const ok = updateClient(id, { status: newStatus });
  if (!ok) return;

  // Update badge in-place — no full re-render needed
  const badge = card.querySelector('.status-badge');
  if (badge) {
    badge.className = `status-badge ${getStatusClass(newStatus)}`;
    badge.textContent = getStatusLabel(newStatus);
  }

  updateFilterBadges(getClients());
  showToast(`Статус изменён: «${getStatusLabel(newStatus)}»`, 'success');
}

function handleDelete(id, name) {
  const confirmed = confirm(`Удалить клиента «${name}»?\n\nЭто действие необратимо.`);
  if (!confirmed) return;

  deleteClient(id);

  const card = document.querySelector(`[data-id="${id}"]`);
  if (card) {
    card.classList.add('card-removing');
    setTimeout(renderClients, 320);
  } else {
    renderClients();
  }

  showToast(`Клиент «${name}» удалён`, 'info');
}

// ── Filter Badge Counts ────────────────────────────────────────────────────

function updateFilterBadges(clients) {
  const counts = {
    all:       clients.length,
    new:       clients.filter(c => c.status === 'new').length,
    active:    clients.filter(c => c.status === 'active').length,
    completed: clients.filter(c => c.status === 'completed').length
  };
  document.querySelectorAll('[data-filter]').forEach(btn => {
    const el = btn.querySelector('.filter-badge');
    if (el) el.textContent = counts[btn.dataset.filter] ?? 0;
  });
}

// ── Search ─────────────────────────────────────────────────────────────────

function setupSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;

  const onInput = debounce(function (e) {
    currentSearch = e.target.value;
    renderClients();
  }, 280);

  input.addEventListener('input', onInput);

  const clearBtn = document.getElementById('searchClear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      currentSearch = '';
      renderClients();
      input.focus();
    });
  }
}

// ── Filters ────────────────────────────────────────────────────────────────

function setupFilters() {
  document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      currentFilter = this.dataset.filter;
      renderClients();
    });
  });
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

  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      toggle.classList.remove('open');
    });
  });
}

// ── Empty State ────────────────────────────────────────────────────────────

function buildEmptyState() {
  const isFiltering = currentSearch || currentFilter !== 'all';
  return `
    <div class="empty-state">
      <div class="empty-illustration">
        ${isFiltering
          ? `<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="36" cy="36" r="22" stroke="#6366f1" stroke-width="2.5" stroke-dasharray="4 3"/>
              <line x1="52" y1="52" x2="68" y2="68" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/>
              <line x1="28" y1="36" x2="44" y2="36" stroke="#8b5cf6" stroke-width="2.5" stroke-linecap="round"/>
            </svg>`
          : `<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="32" cy="28" r="12" stroke="#6366f1" stroke-width="2.5"/>
              <path d="M8 60a24 24 0 0148 0" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round"/>
              <circle cx="56" cy="24" r="8" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="3 2.5"/>
              <line x1="62" y1="18" x2="70" y2="12" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round"/>
            </svg>`
        }
      </div>
      <h3 class="empty-title">${isFiltering ? 'Ничего не найдено' : 'Нет клиентов'}</h3>
      <p class="empty-text">
        ${isFiltering
          ? 'Попробуйте изменить параметры поиска или выбрать другой фильтр'
          : 'Добавьте первого клиента, чтобы начать вести базу'}
      </p>
      ${!isFiltering
        ? `<a href="form.html" class="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Добавить клиента
          </a>`
        : ''}
    </div>
  `;
}

// ── Boot ───────────────────────────────────────────────────────────────────

// type="module" scripts are deferred — they run after HTML is parsed.
// At that point readyState is 'interactive', NOT 'loading'.
// So the else branch always executes immediately with the DOM ready.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Re-render (but don't re-attach listeners) when browser restores page
// from bfcache (back/forward button). DOMContentLoaded does NOT fire
// in that case, but 'pageshow' with event.persisted = true does.
window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    reinit();
  }
});
