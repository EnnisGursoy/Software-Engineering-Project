// Centralized API base URL — update RAILWAY_URL after deploying the backend
const RAILWAY_URL = 'https://REPLACE_WITH_RAILWAY_URL';

const isLocal = window.location.protocol === 'file:'
  || window.location.hostname === ''
  || window.location.hostname === 'localhost'
  || window.location.hostname === '127.0.0.1';

const API = isLocal || RAILWAY_URL.includes('REPLACE_WITH_RAILWAY_URL')
  ? 'http://localhost:8000'
  : RAILWAY_URL;

const API_BASE = API; // alias used by taxes.html

// ─────────────────────────────────────────────────────────────
// Auth helpers — shared across every page
// ─────────────────────────────────────────────────────────────

/** Returns the saved JWT, or null if none. */
function getToken() {
  return localStorage.getItem('access_token');
}

/** Decoded JWT payload, or null. */
function getTokenPayload() {
  const t = getToken();
  if (!t) return null;
  try {
    const base64 = t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

/** True iff a token exists AND has not expired. */
function isTokenValid() {
  const p = getTokenPayload();
  if (!p) return false;
  if (typeof p.exp === 'number' && p.exp * 1000 <= Date.now()) return false;
  return true;
}

/** Clears auth state and sends user back to login (unless already there). */
function clearAuthAndRedirect() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_role');
  const here = (window.location.pathname.split('/').pop() || '').toLowerCase();
  const onPublic = here === '' || here === 'login.html' || here === 'index.html';
  if (!onPublic) {
    window.location.replace('login.html');
  }
}

/** Standard auth headers for protected requests. */
function authHeaders(extra = {}) {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}`, ...extra } : { ...extra };
}

/**
 * Page-level guard. Call at the top of any protected page:
 *   if (!requireAuth())              return;  // any logged-in user
 *   if (!requireAuth({admin:true}))  return;  // admin only
 */
function requireAuth({ admin = false, roles = null } = {}) {
  if (!isTokenValid()) {
    clearAuthAndRedirect();
    return false;
  }
  const role = localStorage.getItem('user_role') || '';
  if (admin && role !== 'admin') {
    window.location.replace('homepage.html');
    return false;
  }
  if (roles && !roles.includes(role)) {
    window.location.replace('homepage.html');
    return false;
  }
  return true;
}

// Endpoints that legitimately respond 401/403 without meaning "your session
// died" — don't bounce the user to login on these.
const _AUTH_OPEN_PATHS = ['/auth/login', '/auth/setup-status', '/auth/create'];

// Global fetch wrapper: any 401 from a protected endpoint clears the stale
// token and sends the user back to login. Prevents pages from silently
// showing "Failed to load …" after a token expires.
const _origFetch = window.fetch.bind(window);
window.fetch = async function (...args) {
  const res = await _origFetch(...args);
  if (res.status === 401) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
    const isOpenPath = _AUTH_OPEN_PATHS.some(p => url.includes(p));
    if (!isOpenPath) {
      clearAuthAndRedirect();
    }
  }
  return res;
};
