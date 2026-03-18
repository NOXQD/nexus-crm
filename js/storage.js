// js/storage.js
// All localStorage operations for CRM client data

const STORAGE_KEY = 'nexus_crm_clients';

/** Default demo clients shown on first launch */
const DEFAULT_CLIENTS = [
  {
    id: '1700000001000',
    fullName: 'Александр Петров',
    phone: '+7 (916) 234-56-78',
    email: 'a.petrov@company.ru',
    status: 'active',
    comment: 'Заинтересован в расширении пакета услуг. Нужно выслать коммерческое предложение.',
    createdAt: '2025-12-10T09:00:00.000Z'
  },
  {
    id: '1700000002000',
    fullName: 'Мария Соколова',
    phone: '+7 (903) 456-78-90',
    email: 'sokolova.m@gmail.com',
    status: 'new',
    comment: 'Обратилась через сайт. Интересует базовый тариф для стартапа.',
    createdAt: '2026-01-05T14:30:00.000Z'
  },
  {
    id: '1700000003000',
    fullName: 'Дмитрий Козлов',
    phone: '+7 (925) 678-90-12',
    email: 'd.kozlov@biz.com',
    status: 'completed',
    comment: 'Сделка успешно закрыта. Оплата получена. Клиент доволен результатом.',
    createdAt: '2025-11-20T11:00:00.000Z'
  },
  {
    id: '1700000004000',
    fullName: 'Елена Морозова',
    phone: '+7 (499) 123-45-67',
    email: 'morozova@enterprise.ru',
    status: 'active',
    comment: 'Ведём переговоры по корпоративному договору. Ждём подтверждения бюджета.',
    createdAt: '2026-01-15T10:00:00.000Z'
  },
  {
    id: '1700000005000',
    fullName: 'Сергей Новиков',
    phone: '+7 (812) 987-65-43',
    email: 'novikov.s@startup.io',
    status: 'new',
    comment: 'Рекомендован партнёром. Ожидает звонка менеджера для первичной консультации.',
    createdAt: '2026-02-01T16:00:00.000Z'
  },
  {
    id: '1700000006000',
    fullName: 'Анна Белова',
    phone: '+7 (921) 345-67-89',
    email: 'a.belova@design.studio',
    status: 'completed',
    comment: 'Завершён проект по редизайну. Оставила положительный отзыв.',
    createdAt: '2026-02-20T09:30:00.000Z'
  }
];

/**
 * Read clients from localStorage.
 * ALWAYS returns an array — never null, never throws.
 */
export function getClients() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);

    // Nothing stored yet → return empty array (not null)
    if (raw === null || raw === undefined) return [];

    const parsed = JSON.parse(raw);

    // Sanity-check: must be an array
    if (!Array.isArray(parsed)) {
      console.warn('[CRM] getClients: data is not an array, resetting to defaults');
      saveClients(DEFAULT_CLIENTS);
      return [...DEFAULT_CLIENTS];
    }

    // Each item must have at least an id
    const valid = parsed.filter(item => item && typeof item === 'object' && item.id);
    if (valid.length !== parsed.length) {
      console.warn('[CRM] getClients: some items were malformed and removed');
      saveClients(valid);
    }

    return valid;
  } catch (err) {
    console.warn('[CRM] getClients: localStorage corrupted, restoring defaults:', err);
    saveClients(DEFAULT_CLIENTS);
    return [...DEFAULT_CLIENTS];
  }
}

/** Save clients array to localStorage */
export function saveClients(clients) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(clients));
  } catch (err) {
    console.error('[CRM] saveClients: failed to write localStorage:', err);
  }
}

/**
 * Must be called once on page load.
 * If storage is empty → seeds demo clients automatically.
 * Always returns a valid non-empty array on first run.
 */
export function initClients() {
  const clients = getClients();

  if (clients.length === 0) {
    // Either first run, cleared storage, or corrupted data → restore defaults
    saveClients(DEFAULT_CLIENTS);
    console.log('[CRM] initClients: storage empty, seeded', DEFAULT_CLIENTS.length, 'demo clients');
    return [...DEFAULT_CLIENTS];
  }

  console.log('[CRM] initClients: loaded', clients.length, 'clients from storage');
  return clients;
}

/** Add a new client object to the list */
export function addClient(client) {
  const clients = getClients();
  clients.push(client);
  saveClients(clients);
}

/** Update fields of a client by id. Returns true on success. */
export function updateClient(id, updates) {
  const clients = getClients();
  const index = clients.findIndex(c => c.id === id);
  if (index === -1) return false;
  clients[index] = { ...clients[index], ...updates };
  saveClients(clients);
  return true;
}

/** Remove a client by id */
export function deleteClient(id) {
  saveClients(getClients().filter(c => c.id !== id));
}

/** Get a single client by id */
export function getClientById(id) {
  return getClients().find(c => c.id === id) || null;
}

/** DEV HELPER — wipe storage and re-seed (call from console if needed) */
export function resetToDefaults() {
  localStorage.removeItem(STORAGE_KEY);
  return initClients();
}

// Alias for compatibility — some older code may use createClient
export { addClient as createClient };
