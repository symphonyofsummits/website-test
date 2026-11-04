/* =========================================================
   Symphony of Summits — API client (talks to FastAPI backend)
   ========================================================= */
const API_BASE = (window.SOS_CONFIG && window.SOS_CONFIG.apiBase) || "http://127.0.0.1:8000/api/v1";

const authStore = {
  get: () => localStorage.getItem("sos_token"),
  set: (t) => localStorage.setItem("sos_token", t),
  clear: () => localStorage.removeItem("sos_token"),
};

async function request(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const t = authStore.get();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const r = await fetch(`${API_BASE}${path}`, opts);
  const text = await r.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!r.ok) {
    const msg = (data && data.detail) || `Request failed (${r.status})`;
    throw new Error(msg);
  }
  return data;
}

/* ---------- Trips ---------- */
const Trips = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/trips${qs ? "?" + qs : ""}`);
  },
  detail: (slug) => request(`/trips/${slug}`),
  batches: (slug) => request(`/trips/${slug}/batches`),
  upcoming: (limit = 30) => request(`/trips/by/upcoming?limit=${limit}`),
};

/* ---------- Leads (quote form) ---------- */
const Leads = {
  create: (payload) => request("/leads", { method: "POST", body: payload }),
  subscribeNewsletter: (email) => request(`/leads/newsletter?email=${encodeURIComponent(email)}`, { method: "POST" }),
};

/* ---------- Auth ---------- */
const Auth = {
  signup: (payload) => request("/auth/signup", { method: "POST", body: payload }),
  login: (payload) => request("/auth/login", { method: "POST", body: payload }),
  me: () => request("/auth/me", { auth: true }),
};

/* ---------- Bookings ---------- */
const Bookings = {
  create: (payload) => request("/bookings", { method: "POST", body: payload, auth: true }),
  mine: () => request("/bookings", { auth: true }),
  cancel: (id, reason = "") =>
    request(`/bookings/${id}/cancel?reason=${encodeURIComponent(reason)}`, { method: "POST", auth: true }),
};

/* ---------- Payments ---------- */
const Payments = {
  initiate: (payload) => request("/payments/initiate", { method: "POST", body: payload, auth: true }),
  verify: (payload) => request("/payments/verify", { method: "POST", body: payload, auth: true }),
};

/* ---------- Stories & Instagram ---------- */
const Stories = {
  list: (limit = 6) => request(`/stories?limit=${limit}`),
  detail: (slug) => request(`/stories/${slug}`),
};
const Instagram = {
  feed: (limit = 6) => request(`/instagram?limit=${limit}`),
};

/* ---------- expose ---------- */
window.SOS = { API_BASE, Trips, Leads, Auth, Bookings, Payments, Stories, Instagram, authStore };
