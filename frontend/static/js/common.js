/* common.js · Utilidades compartidas: DOM, formato, API, tema, avisos y diálogos */

const $ = (selector, root = document) => root.querySelector(selector);
const cop = amount => "$" + Number(amount).toLocaleString("es-CO");

const HTML_ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => HTML_ESCAPES[char]);

/** Petición JSON uniforme. Nunca lanza: siempre devuelve { ok, status, data }. */
async function api(url, { method = "GET", body } = {}) {
  try {
    const isFormData = body instanceof FormData;
    const res = await fetch(url, {
      method,
      headers: body && !isFormData ? { "Content-Type": "application/json" } : {},
      credentials: "same-origin",
      body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch (error) {
    console.error(error);
    return { ok: false, status: 0, data: { error: "No fue posible conectar con el servidor." } };
  }
}

/* ---------- Tema ---------- */
const THEME_KEY = "CineStar-tema";

function storedTheme() {
  try { return localStorage.getItem(THEME_KEY); } catch { return null; }
}

function setTheme(theme, { persist = true } = {}) {
  document.documentElement.dataset.tema = theme;
  if (persist) {
    try { localStorage.setItem(THEME_KEY, theme); } catch { /* almacenamiento no disponible */ }
  }
  const button = $("#themeBtn");
  if (button) button.textContent = theme === "oscuro" ? "Modo claro" : "Modo oscuro";
}

setTheme(
  storedTheme() ?? (matchMedia("(prefers-color-scheme: light)").matches ? "claro" : "oscuro"),
  { persist: false }
);

document.addEventListener("DOMContentLoaded", () => {
  const button = $("#themeBtn");
  if (!button) return;
  setTheme(document.documentElement.dataset.tema, { persist: false });
  button.addEventListener("click", () =>
    setTheme(document.documentElement.dataset.tema === "oscuro" ? "claro" : "oscuro")
  );
});

/* ---------- Avisos (capa superior, visibles sobre los diálogos) ---------- */
let toastTimer;

function toast(message) {
  const el = $("#toast");
  if (!el) return;
  el.textContent = message;
  if (el.matches(":popover-open")) el.hidePopover();
  el.showPopover();
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.matches(":popover-open") && el.hidePopover(), 3000);
}

/* ---------- Diálogos: cerrar con [data-close] o al pulsar el fondo ---------- */
document.addEventListener("click", event => {
  const { target } = event;
  const dialog = target instanceof HTMLDialogElement
    ? target
    : target.closest("[data-close]")?.closest("dialog");
  dialog?.close();
});