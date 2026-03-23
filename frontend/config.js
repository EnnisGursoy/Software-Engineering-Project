// Centralized API base URL — update RAILWAY_URL after deploying the backend
const RAILWAY_URL = 'https://REPLACE_WITH_RAILWAY_URL';

const API = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : RAILWAY_URL;

const API_BASE = API; // alias used by taxes.html
