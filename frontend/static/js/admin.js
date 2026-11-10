/* admin.js · Métricas, usuarios, cartelera y ventas */

const ROLES = { cliente: "Cliente", cajero: "Cajero", gerente: "Gerente", admin: "Administrador" };

const formatDate = value =>
  value
    ? new Date(value.replace(" ", "T") + "Z").toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })
    : "";

const emptyRow = (columns, text) => `<tr><td class="empty-cell" colspan="${columns}">${text}</td></tr>`;

/** Igual que api(), pero expulsa al usuario si la sesión no es de administrador. */
async function request(url, options) {
  const result = await api(url, options);
  if (result.status === 403) location.assign("/");
  return result;
}

function confirmAction({ title, text, action }) {
  const dialog = $("#confirmDialog");
  $("#confirmTitle").textContent = title;
  $("#confirmText").textContent = text;
  $("#confirmOk").textContent = action;
  dialog.returnValue = "";
  dialog.showModal();
  return new Promise(resolve =>
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true })
  );
}

/* ---------- Carga de datos ---------- */
async function loadStats() {
  const { ok, data } = await request("/api/admin/stats");
  if (!ok) return;
  const values = {
    statTotal: cop(data.total_recaudado),
    statTickets: data.total_boletas,
    statUsers: data.total_usuarios,
    statTop: data.top_pelicula === "N/A" ? "Sin ventas" : data.top_pelicula,
  };
  Object.entries(values).forEach(([id, value]) => { $(`#${id}`).textContent = value; });
}

async function loadUsers() {
  const { ok, data } = await request("/api/admin/usuarios");
  if (!ok) return toast(data.error || "No pudimos cargar los usuarios.");

  const roleOptions = current => Object.entries(ROLES)
    .map(([value, label]) => `<option value="${value}"${value === current ? " selected" : ""}>${label}</option>`)
    .join("");

  $("#usersBody").innerHTML = data.usuarios.map(user => `
    <tr>
      <td><strong>${esc(user.nombre)}</strong><small>${esc(user.email)}</small></td>
      <td>
        <select class="control compact" data-role="${user.id}" aria-label="Rol de ${esc(user.nombre)}">
          ${roleOptions(user.rol)}
        </select>
      </td>
      <td>${formatDate(user.creado)}</td>
      <td><button class="btn danger sm" type="button" data-action="delete-user" data-id="${user.id}" data-name="${esc(user.nombre)}">Eliminar</button></td>
    </tr>`).join("") || emptyRow(4, "Aún no hay usuarios registrados.");
}

async function loadFilms() {
  const { ok, data } = await api("/api/contenido");
  if (!ok) return toast(data.error || "No pudimos cargar la cartelera.");

  $("#filmsBody").innerHTML = (data.films ?? []).map(film => `
    <tr>
      <td><strong>${esc(film.title)}</strong><small>${esc(film.genre)}</small></td>
      <td>${esc(film.format)}</td>
      <td>${esc(film.duration)}</td>
      <td><button class="btn danger sm" type="button" data-action="delete-film" data-id="${film.id}" data-title="${esc(film.title)}">Quitar</button></td>
    </tr>`).join("") || emptyRow(4, "La cartelera está vacía. Agrega una película.");
}

async function loadSales() {
  const { ok, data } = await request("/api/admin/ventas");
  if (!ok) return toast(data.error || "No pudimos cargar las ventas.");

  $("#salesBody").innerHTML = (data.ventas ?? []).map(sale => `
    <tr>
      <td>#${sale.id}</td>
      <td>${esc(sale.cliente)}<small>${esc(sale.email)}</small></td>
      <td><strong>${esc(sale.pelicula)}</strong><small>${esc(sale.formato)}</small></td>
      <td>${esc(sale.funcion)}</td>
      <td>${esc(sale.asientos).replaceAll(",", ", ")}</td>
      <td><strong>${cop(sale.total)}</strong></td>
      <td>${formatDate(sale.fecha)}</td>
    </tr>`).join("") || emptyRow(7, "Aún no hay ventas registradas.");
}

/* ---------- Acciones ---------- */
async function changeRole(select) {
  const { ok, data } = await request(`/api/admin/usuarios/cambiar-rol/${select.dataset.role}`, {
    method: "POST",
    body: { rol: select.value },
  });
  toast(ok ? data.mensaje : data.error || "No pudimos cambiar el rol.");
  loadUsers();
}

const actions = {
  async "delete-user"(el) {
    const confirmed = await confirmAction({
      title: "Eliminar usuario",
      text: `Se eliminará a ${el.dataset.name} junto con su historial de compras. Esta acción no se puede deshacer.`,
      action: "Eliminar usuario",
    });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/usuarios/eliminar/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos eliminar al usuario.");
    await Promise.all([loadUsers(), loadStats(), loadSales()]);
  },

  async "delete-film"(el) {
    const confirmed = await confirmAction({
      title: "Quitar película",
      text: `Se quitará «${el.dataset.title}» de la cartelera.`,
      action: "Quitar película",
    });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/pelicula/eliminar/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos quitar la película.");
    loadFilms();
  },
};

document.addEventListener("click", event => {
  const el = event.target.closest("[data-action]");
  if (el) actions[el.dataset.action]?.(el);
});

document.addEventListener("change", event => {
  if (event.target.matches("[data-role]")) changeRole(event.target);
});

$("#addFilmForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const { ok, data } = await request("/api/admin/pelicula/agregar", {
    method: "POST",
    body: new FormData(form),
  });
  toast(ok ? data.mensaje : data.error || "No pudimos guardar la película.");
  if (ok) { form.reset(); loadFilms(); }
});

/* ---------- Pestañas ---------- */
const tabs = document.querySelectorAll("[role=tab]");
tabs.forEach(tab => tab.addEventListener("click", () => {
  tabs.forEach(other => {
    const active = other === tab;
    other.setAttribute("aria-selected", active);
    $(`#${other.getAttribute("aria-controls")}`).hidden = !active;
  });
}));

/* ---------- Arranque ---------- */
Promise.all([loadStats(), loadUsers(), loadFilms(), loadSales()]);