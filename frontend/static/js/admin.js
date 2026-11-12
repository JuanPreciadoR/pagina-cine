/* admin.js · Métricas, usuarios, cartelera y ventas */

const ROLES = { cliente: "Cliente", admin: "Administrador" };
let selectedSeatRoom = null;

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
      <td><button class="btn danger sm" type="button" data-action="delete-user" data-id="${user.id}" data-name="${esc(user.nombre)}">Desactivar</button></td>
    </tr>`).join("") || emptyRow(4, "Aún no hay usuarios registrados.");
}

async function loadFilms() {
  const { ok, data } = await request("/api/contenido");
  if (!ok) return toast(data.error || "No pudimos cargar la cartelera.");

  $("#filmsBody").innerHTML = (data.films ?? []).map(film => `
    <tr>
      <td><strong>${esc(film.title)}</strong><small>${esc(film.genre)}</small></td>
      <td>${esc(film.format)}</td>
      <td>${esc(film.duration)}</td>
      <td><button class="btn danger sm" type="button" data-action="delete-film" data-id="${film.id}" data-title="${esc(film.title)}">Quitar</button></td>
    </tr>`).join("") || emptyRow(4, "La cartelera está vacía. Agrega una película.");
}

function fillSelect(id, items, label, value = "id") {
  const select = $(`#${id}`);
  select.innerHTML = items.length
    ? items.map(item => `<option value="${esc(item[value])}">${esc(label(item))}</option>`).join("")
    : '<option value="">No hay opciones activas</option>';
  select.disabled = !items.length;
}

async function loadOperation() {
  const selectedDate = $("#showFilterDate").value;
  const { ok, data } = await request(`/api/admin/operacion?fecha=${encodeURIComponent(selectedDate)}`);
  if (!ok) return toast(data.error || "No pudimos cargar la administración de sedes.");
  const activeCinemas = data.sedes.filter(item => item.estado === "Activo");
  const activeRooms = data.salas.filter(item => item.estado === "Activo");
  const activeFilms = data.peliculas;

  $("#cinemasBody").innerHTML = data.sedes.map(cinema => `
    <tr><td><strong>${esc(cinema.nombre)}</strong><small>${esc(cinema.ciudad)}</small></td>
      <td>${esc(cinema.tipo)}</td><td>${esc(cinema.documento)}</td><td>${esc(cinema.estado)}</td>
      <td>${cinema.estado === "Activo" ? `<button class="btn danger sm" type="button" data-action="delete-cinema" data-id="${cinema.id}" data-name="${esc(cinema.nombre)}">Desactivar</button>` : ""}</td></tr>`
  ).join("") || emptyRow(5, "Aún no hay sedes registradas.");

  $("#roomsBody").innerHTML = data.salas.map(room => `
    <tr><td><strong>${esc(room.nombre)}</strong><small>${esc(room.city)} · capacidad ${room.capacidad}</small></td>
      <td>${esc(room.cinema)}</td><td>${room.asientos}</td><td>${esc(room.estado)}</td>
      <td><button class="btn ghost sm" type="button" data-action="show-seats" data-id="${room.id}" data-name="${esc(room.nombre)}">Sillas</button>
      ${room.estado === "Activo" ? `<button class="btn danger sm" type="button" data-action="delete-room" data-id="${room.id}" data-name="${esc(room.nombre)}">Desactivar</button>` : ""}</td></tr>`
  ).join("") || emptyRow(5, "Aún no hay salas registradas.");

  $("#showsBody").innerHTML = data.funciones.map(show => `
    <tr><td><strong>${esc(show.pelicula)}</strong></td><td>${esc(show.sala)}<small>${esc(show.sede)}</small></td>
      <td>${esc(show.fecha)}<small>${esc(show.hora)}</small></td><td>${esc(show.formato)}</td><td>${cop(show.precio)}</td>
      <td>${esc(show.estado)}</td><td>${show.estado === "Activo" ? `<button class="btn danger sm" type="button" data-action="delete-show" data-id="${show.id}" data-name="${esc(show.pelicula)} · ${esc(show.fecha)} ${esc(show.hora)}">Cancelar</button>` : ""}</td></tr>`
  ).join("") || emptyRow(7, "No hay funciones próximas.");

  fillSelect("roomCinema", activeCinemas, cinema => `${cinema.nombre} · ${cinema.ciudad}`);
  fillSelect("seatRoom", activeRooms, room => `${room.nombre} · ${room.cinema}`);
  fillSelect("showRoom", activeRooms, room => `${room.nombre} · ${room.cinema}`);
  fillSelect("showFilm", activeFilms, film => film.titulo);
  if (selectedSeatRoom && activeRooms.some(room => room.id === selectedSeatRoom)) {
    $("#seatRoom").value = selectedSeatRoom;
  } else {
    selectedSeatRoom = activeRooms[0]?.id ?? null;
  }
  if (selectedSeatRoom) await loadSeats(selectedSeatRoom);
}

async function loadSeats(roomId) {
  selectedSeatRoom = Number(roomId);
  $("#seatTitle").textContent = `Sillas de ${$("#seatRoom").selectedOptions[0]?.textContent ?? "la sala"}`;
  const { ok, data } = await request(`/api/admin/salas/${selectedSeatRoom}/asientos`);
  if (!ok) return toast(data.error || "No pudimos cargar las sillas.");
  $("#seatsBody").innerHTML = data.asientos.map(seat => `
    <tr><td><strong>${esc(seat.fila)}${seat.numero}</strong></td><td>${esc(seat.tipo)}</td><td>${esc(seat.estado)}</td>
      <td>${seat.estado === "Activo" ? `<button class="btn danger sm" type="button" data-action="delete-seat" data-id="${seat.id}" data-name="${esc(seat.fila)}${seat.numero}">Desactivar</button>` : ""}</td></tr>`
  ).join("") || emptyRow(4, "Esta sala no tiene sillas registradas.");
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
      title: "Desactivar usuario",
      text: `Se desactivará el acceso de ${el.dataset.name}. Su cuenta y su historial de compras se conservarán.`,
      action: "Desactivar",
    });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/usuarios/eliminar/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos eliminar al usuario.");
    await Promise.all([loadUsers(), loadStats(), loadSales()]);
  },

  async "delete-film"(el) {
    const confirmed = await confirmAction({
      title: "Retirar película",
      text: `«${el.dataset.title}» dejará de mostrarse en cartelera. Su historial se conservará.`,
      action: "Retirar película",
    });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/pelicula/eliminar/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos quitar la película.");
    await Promise.all([loadFilms(), loadOperation()]);
  },

  async "delete-cinema"(el) {
    const confirmed = await confirmAction({ title: "Desactivar sede", text: `La sede ${el.dataset.name} dejará de estar disponible para nuevas funciones.`, action: "Desactivar" });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/sedes/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos desactivar la sede.");
    if (ok) await loadOperation();
  },

  async "delete-room"(el) {
    const confirmed = await confirmAction({ title: "Desactivar sala", text: `Se desactivará ${el.dataset.name}. Primero cancela sus funciones futuras.`, action: "Desactivar" });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/salas/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos desactivar la sala.");
    if (ok) await loadOperation();
  },

  async "show-seats"(el) {
    $("#seatRoom").value = el.dataset.id;
    await loadSeats(el.dataset.id);
    $("#seatTitle").scrollIntoView({ behavior: "smooth", block: "start" });
  },

  async "delete-seat"(el) {
    const confirmed = await confirmAction({ title: "Desactivar silla", text: `La silla ${el.dataset.name} se conservará en el historial y dejará de ofrecerse.`, action: "Desactivar" });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/asientos/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos desactivar la silla.");
    if (ok) await Promise.all([loadSeats(selectedSeatRoom), loadOperation()]);
  },

  async "delete-show"(el) {
    const confirmed = await confirmAction({ title: "Cancelar función", text: `Se cancelará ${el.dataset.name}. Las compras registradas se conservarán.`, action: "Cancelar función" });
    if (!confirmed) return;
    const { ok, data } = await request(`/api/admin/funciones/${el.dataset.id}`, { method: "DELETE" });
    toast(ok ? data.mensaje : data.error || "No pudimos cancelar la función.");
    if (ok) await loadOperation();
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
  if (ok) { form.reset(); await Promise.all([loadFilms(), loadOperation()]); }
});

async function submitJsonForm(event, url, successMessage) {
  event.preventDefault();
  const form = event.currentTarget;
  const body = Object.fromEntries(new FormData(form));
  const { ok, data } = await request(url, { method: "POST", body });
  toast(ok ? (data.mensaje || successMessage) : data.error || "No pudimos guardar los cambios.");
  if (ok) {
    form.reset();
    await loadOperation();
  }
}

$("#addCinemaForm").addEventListener("submit", event => submitJsonForm(event, "/api/admin/sedes", "Sede creada."));
$("#addRoomForm").addEventListener("submit", event => submitJsonForm(event, "/api/admin/salas", "Sala creada."));
$("#addShowForm").addEventListener("submit", event => submitJsonForm(event, "/api/admin/funciones", "Función programada."));
$("#seatRoom").addEventListener("change", event => loadSeats(event.target.value));
$("#addSeatForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const body = Object.fromEntries(new FormData(form));
  const roomId = body.room_id;
  delete body.room_id;
  const { ok, data } = await request(`/api/admin/salas/${roomId}/asientos`, { method: "POST", body });
  toast(ok ? data.mensaje : data.error || "No pudimos agregar la silla.");
  if (ok) {
    form.reset();
    $("#seatRoom").value = roomId;
    await Promise.all([loadSeats(roomId), loadOperation()]);
  }
});

const today = new Date();
const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
$("#showDate").min = localToday;
$("#showFilterDate").value = localToday;
$("#showFilterDate").addEventListener("change", loadOperation);

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
Promise.all([loadStats(), loadUsers(), loadFilms(), loadSales(), loadOperation()]);