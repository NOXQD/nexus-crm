// js/form.js
// Add / Edit client form logic with validation

import { addClient, getClientById, updateClient } from './storage.js?v=4';
import { generateId, showToast, setActiveNav, escapeHtml } from './utils.js?v=4';

// ── State ──────────────────────────────────────────────────────────────────

let editId = null;

// ── Init ───────────────────────────────────────────────────────────────────

function init() {
  setActiveNav();

  // Check for edit mode via URL param
  const params = new URLSearchParams(window.location.search);
  editId = params.get('edit');

  if (editId) {
    enterEditMode(editId);
  } else {
    // Default date to today
    const dateInput = document.getElementById('createdAt');
    if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
  }

  document.getElementById('clientForm').addEventListener('submit', handleSubmit);
  document.getElementById('cancelBtn').addEventListener('click', goBack);
  setupMobileMenu();
}

// ── Edit Mode ──────────────────────────────────────────────────────────────

function enterEditMode(id) {
  const client = getClientById(id);
  if (!client) {
    showToast('Клиент не найден', 'error');
    window.location.href = 'index.html';
    return;
  }

  // Update UI labels
  const titleEl = document.getElementById('pageTitle');
  const subtitleEl = document.getElementById('pageSubtitle');
  const submitBtn = document.getElementById('submitBtn');
  if (titleEl) titleEl.textContent = 'Редактировать клиента';
  if (subtitleEl) subtitleEl.textContent = 'Измените данные клиента';
  if (submitBtn) submitBtn.textContent = 'Сохранить изменения';

  // Fill fields
  setField('fullName', client.fullName);
  setField('phone', client.phone);
  setField('email', client.email);
  setField('status', client.status);
  setField('comment', client.comment);

  if (client.createdAt) {
    const date = new Date(client.createdAt);
    if (!isNaN(date)) {
      setField('createdAt', date.toISOString().split('T')[0]);
    }
  }
}

function setField(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value || '';
}

// ── Submit ─────────────────────────────────────────────────────────────────

function handleSubmit(e) {
  e.preventDefault();

  clearFieldErrors();

  const data = collectFormData();
  const errors = validateFormData(data);

  if (errors.length > 0) {
    showToast(errors[0], 'error');
    return;
  }

  if (editId) {
    updateClient(editId, data);
    showToast('Данные клиента обновлены', 'success');
  } else {
    const newClient = { id: generateId(), ...data };
    addClient(newClient);
    showToast('Клиент успешно добавлен', 'success');
  }

  // Redirect after brief delay so toast is visible
  setTimeout(() => { window.location.href = 'index.html'; }, 900);
}

/** Read all form field values */
function collectFormData() {
  const dateVal = document.getElementById('createdAt').value;
  return {
    fullName: document.getElementById('fullName').value.trim(),
    phone: document.getElementById('phone').value.trim(),
    email: document.getElementById('email').value.trim(),
    status: document.getElementById('status').value,
    comment: document.getElementById('comment').value.trim(),
    createdAt: dateVal
      ? new Date(dateVal).toISOString()
      : new Date().toISOString()
  };
}

/** Validate form data. Returns array of error messages. */
function validateFormData(data) {
  const errors = [];

  if (!data.fullName) {
    errors.push('Введите имя клиента');
    markError('fullName');
  }

  if (!data.phone) {
    errors.push('Введите номер телефона');
    markError('phone');
  }

  if (!data.email) {
    errors.push('Введите email клиента');
    markError('email');
  } else if (!isValidEmail(data.email)) {
    errors.push('Введите корректный email (example@domain.com)');
    markError('email');
  }

  return errors;
}

function markError(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  field.classList.add('field-error');
  field.addEventListener('input', () => field.classList.remove('field-error'), { once: true });
}

function clearFieldErrors() {
  document.querySelectorAll('.field-error').forEach(el => el.classList.remove('field-error'));
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ── Navigation ─────────────────────────────────────────────────────────────

function goBack() {
  window.location.href = 'index.html';
}

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
