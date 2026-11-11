/* script.js · Cartelera, selección de sillas y compra */

const SEAT_ROWS = ["A", "B", "C", "D", "E"];
const SEAT_COLUMNS = 6;
const AISLE_BEFORE_COLUMN = 4;

const state = { data: null, city: "Bogotá", format: "Todos", cart: [] };
const seatPicker = { film: null, time: null, format: null, selected: new Set(), request: 0 };

const seatDialog = $("#seatDialog");
const cartDialog = $("#cartDialog");

const price = format => state.data.ticketPrices[format] ?? state.data.ticketPrices.default;
const hue = seed => (seed * 47 + 205) % 360;
const plural = (n, one, many) => (n === 1 ? one : many);
const isSameFunction = line =>
  line.pelicula === seatPicker.film && line.funcion === seatPicker.time && line.formato === seatPicker.format;

/* ---------- Plantillas ---------- */
const slotButton = (film, slot) => `
  <button class="slot" type="button" data-action="pick-seats"
    data-film="${esc(film.title)}" data-format="${esc(film.format)}" data-time="${esc(slot)}"
    aria-label="${esc(film.title)}, ${esc(film.format)}, función de las ${esc(slot)}">${esc(slot)}</button>`;

const posterCard = ({ seed, title, chips, meta, footer, poster }) => `
  <article class="film" style="--hue:${hue(seed)}">
    <div class="poster"${poster ? ` style="background-image: linear-gradient(rgb(0 0 0 / 0.18), rgb(0 0 0 / 0.72)), url('${esc(poster)}')"` : ""}>
      <div class="chips">${chips.map(chip => `<span class="chip">${esc(chip)}</span>`).join("")}</div>
      <h3>${esc(title)}</h3>
    </div>
    <div class="film-info">
      <p class="meta">${esc(meta)}</p>
      ${footer}
    </div>
  </article>`;

const emptyState = (message, actionHtml) =>
  `<div class="empty"><p>${esc(message)}</p>${actionHtml}</div>`;

/* ---------- Render ---------- */
function renderBoard() {
  const { films, slots, cities } = state.data;
  const venues = cities[state.city] || cities["Bogotá"];
  $("#boardCity").textContent = state.city;
  $("#board").innerHTML = films.length
    ? films.slice(0, 4).map((film, i) => `
        <div class="board-row">
          <div>
            <strong>${esc(film.title)}</strong>
            <p class="meta">${esc(venues[i % venues.length])}, ${esc(film.format)}</p>
          </div>
          <div class="slots">${slots.slice(i % 3, (i % 3) + 2).map(slot => slotButton(film, slot)).join("")}</div>
        </div>`).join("")
    : '<p class="meta">No hay funciones programadas por ahora.</p>';
}

function renderFilters() {
  $("#formatFilters").innerHTML = state.data.formats.map(format => `
    <button class="filter" type="button" data-action="filter" data-format="${esc(format)}"
      aria-pressed="${format === state.format}">${esc(format)}</button>`).join("");
}

function syncFilters() {
  document.querySelectorAll(".filter").forEach(button =>
    button.setAttribute("aria-pressed", button.dataset.format === state.format));
}

function renderFilms() {
  const { films, slots } = state.data;
  const visible = films.filter(film => state.format === "Todos" || film.format === state.format);

  $("#films").innerHTML = visible.length
    ? visible.map((film, i) => posterCard({
        seed: film.id ?? i,
        title: film.title,
        poster: film.poster ?? null,
        chips: [film.rating, film.format],
        meta: `${film.genre}, ${film.duration}`,
        footer: `<div class="slots">${slots.map(slot => slotButton(film, slot)).join("")}</div>`,
      })).join("")
    : emptyState(
        `No hay funciones en formato ${state.format}.`,
        '<button class="btn ghost" type="button" data-action="filter" data-format="Todos">Ver todos los formatos</button>'
      );
}

function renderStaticSections() {
  const { promos, soon, faq } = state.data;

  const announcements = [
    { image: "anuncio.png", alt: "Exploradores descubren un planeta lejano", kicker: "PROMOCIÓN DE TEMPORADA" },
    { image: "anuncion2.png", alt: "Investigadores recorren una ciudad misteriosa", kicker: "COMBOS CINESTAR" },
    { image: "anuncio3.png", alt: "Aventura entre montañas y ruinas antiguas", kicker: "PRÓXIMOS ESTRENOS" },
  ];

  $("#promoList").innerHTML = announcements.map((announcement, index) => {
    const promo = promos[index];
    const title = promo?.title ?? "Una nueva aventura te espera";
    const text = promo?.text ?? "Descubre los próximos estrenos y encuentra tu siguiente historia favorita.";
    const action = promo
      ? '<button class="btn ghost sm" type="button" onclick="toast(\'¡Promoción aplicada!\')">Aprovechar</button>'
      : '<a class="btn ghost sm" href="#proximamente">Ver próximos estrenos</a>';

    return `
      <article class="promo-banner-card">
        <img src="/static/images/posters/${announcement.image}" alt="${esc(announcement.alt)}">
        <div class="promo-content">
          <p class="promo-kicker">${announcement.kicker}</p>
          <h3>${esc(title)}</h3>
          <p>${esc(text)}</p>
          ${action}
        </div>
      </article>`;
  }).join("");

  updatePromoPagination();

  $("#soon").innerHTML = soon.map((item, i) => posterCard({
    seed: i,
    title: item.title,
    chips: [item.tag],
    meta: item.genre,
    footer: `<button class="btn ghost sm" type="button" data-action="notify" data-title="${esc(item.title)}">Avísame</button>`,
  })).join("");

  $("#faq").innerHTML = faq.map(item => `
    <details><summary>${esc(item.q)}</summary><p>${esc(item.a)}</p></details>`).join("");
}

function drawCart() {
  const tickets = state.cart.reduce((sum, line) => sum + line.asientos.length, 0);
  const total = state.cart.reduce((sum, line) => sum + price(line.formato) * line.asientos.length, 0);

  $("#count").textContent = tickets;
  $("#total").textContent = cop(total);
  $("#pay").disabled = !state.cart.length;
  $("#cartItems").innerHTML = state.cart.length
    ? state.cart.map((line, i) => `
        <li class="cart-item">
          <div>
            <strong>${esc(line.pelicula)}</strong>
            <p class="meta">${esc(line.formato)}, función de las ${esc(line.funcion)}</p>
            <p class="meta">${plural(line.asientos.length, "Silla", "Sillas")} ${line.asientos.join(", ")}</p>
          </div>
          <div class="cart-item-side">
            <span>${cop(price(line.formato) * line.asientos.length)}</span>
            <button class="link" type="button" data-action="remove" data-index="${i}"
              aria-label="Quitar ${esc(line.pelicula)} de la compra">Quitar</button>
          </div>
        </li>`).join("")
    : '<li class="meta">Aún no has elegido sillas. Escoge una función para empezar.</li>';
}

/* ---------- Selección de sillas y compra ---------- */
function updateSeatSummary() {
  const seats = [...seatPicker.selected].sort();
  const total = seats.length * price(seatPicker.format);
  $("#seatSummary").textContent = seats.length
    ? `${plural(seats.length, "Silla elegida", "Sillas elegidas")}: ${seats.join(", ")}. Total ${cop(total)}`
    : "Elige al menos una silla.";
  $("#confirmSeats").disabled = !seats.length;
}

function renderSeatMap(taken) {
  const inCart = new Set(state.cart.find(isSameFunction)?.asientos);
  const columns = Array.from({ length: SEAT_COLUMNS }, (_, i) => i + 1);

  const seat = code => {
    const isTaken = taken.has(code);
    const isMine = inCart.has(code);
    const status = isTaken ? ", ocupada" : isMine ? ", ya está en tu compra" : "";
    return `<button class="seat${isMine ? " in-cart" : ""}" type="button" data-seat="${code}"
      aria-pressed="false" aria-label="Silla ${code}${status}"${isTaken || isMine ? " disabled" : ""}>${code.slice(1)}</button>`;
  };

  $("#seatMap").innerHTML = SEAT_ROWS.map(row => `
    <div class="seat-row">
      <span class="row-label" aria-hidden="true">${row}</span>
      ${columns.map(col => (col === AISLE_BEFORE_COLUMN ? '<i aria-hidden="true"></i>' : "") + seat(`${row}${col}`)).join("")}
    </div>`).join("");
}

async function openSeats({ film, time, format }) {
  Object.assign(seatPicker, { film, time, format, request: seatPicker.request + 1 });
  seatPicker.selected.clear();

  const request = seatPicker.request;
  $("#seatTitle").textContent = film;
  $("#seatSub").textContent = `${format}, función de las ${time}`;
  $("#seatMap").innerHTML = '<p class="meta">Consultando disponibilidad…</p>';
  updateSeatSummary();
  seatDialog.showModal();

  const query = new URLSearchParams({ pelicula: film, funcion: time });
  const { ok, data } = await api(`/api/asientos-ocupados?${query}`);
  if (request !== seatPicker.request) return;

  if (!ok) {
    seatDialog.close();
    return toast(data.error || "No pudimos consultar las sillas. Inténtalo de nuevo.");
  }
  renderSeatMap(new Set(data.asientos_ocupados));
}

function confirmSeats() {
  const seats = [...seatPicker.selected].sort();
  const line = state.cart.find(isSameFunction);

  if (line) line.asientos.push(...seats);
  else state.cart.push({ pelicula: seatPicker.film, funcion: seatPicker.time, formato: seatPicker.format, asientos: seats });

  drawCart();
  seatDialog.close();
  toast(`${seats.length} ${plural(seats.length, "silla agregada", "sillas agregadas")}.`);
}

async function checkout() {
  $("#pay").disabled = true;

  while (state.cart.length) {
    const { ok, status, data } = await api("/api/compra", { method: "POST", body: state.cart[0] });

    if (status === 401) {
      cartDialog.close();
      document.dispatchEvent(new CustomEvent("login:required"));
      toast("Inicia sesión para completar tu compra.");
      break;
    }
    if (!ok) {
      toast(data.error || "No pudimos registrar la compra.");
      break;
    }
    state.cart.shift();
    drawCart();
  }

  if (!state.cart.length) {
    cartDialog.close();
    toast("Compra registrada. ¡Disfruta la función!");
  }
  drawCart();
}

/* ---------- Eventos y Arranque ---------- */
const actions = {
  "pick-seats": el => openSeats({ film: el.dataset.film, time: el.dataset.time, format: el.dataset.format }),
  filter: el => { state.format = el.dataset.format; syncFilters(); renderFilms(); },
  remove: el => { state.cart.splice(Number(el.dataset.index), 1); drawCart(); },
  notify: el => toast(`Te avisaremos del estreno de ${el.dataset.title}.`),
  retry: () => init(),
};

document.addEventListener("click", event => {
  const el = event.target.closest("[data-action]");
  if (el) actions[el.dataset.action]?.(el);
});

$("#seatMap").addEventListener("click", event => {
  const button = event.target.closest(".seat");
  if (!button) return;
  const picked = !seatPicker.selected.has(button.dataset.seat);
  seatPicker.selected[picked ? "add" : "delete"](button.dataset.seat);
  button.setAttribute("aria-pressed", picked);
  updateSeatSummary();
});

$("#confirmSeats").addEventListener("click", confirmSeats);
$("#openCart").addEventListener("click", () => cartDialog.showModal());
$("#pay").addEventListener("click", checkout);
$("#city").addEventListener("change", event => { state.city = event.target.value; renderBoard(); });
function updatePromoPagination() {
  const list = $("#promoList");
  const current = list.clientWidth ? Math.round(list.scrollLeft / list.clientWidth) : 0;
  document.querySelectorAll(".promo-dot").forEach((dot, index) =>
    dot.setAttribute("aria-current", String(index === current)));
}

function scrollPromos(direction) {
  const list = $("#promoList");
  const count = list.children.length;
  if (!count) return;
  const current = Math.round(list.scrollLeft / list.clientWidth);
  const next = (current + direction + count) % count;
  list.scrollTo({ left: next * list.clientWidth, behavior: "smooth" });
}

$("#promoPrevious").addEventListener("click", () => scrollPromos(-1));
$("#promoNext").addEventListener("click", () => scrollPromos(1));
$("#promoPagination").addEventListener("click", event => {
  const dot = event.target.closest("[data-slide-to]");
  if (!dot) return;
  const list = $("#promoList");
  const slide = list.children[Number(dot.dataset.slideTo)];
  if (!slide) return;
  list.scrollTo({
    left: list.scrollLeft + slide.getBoundingClientRect().left - list.getBoundingClientRect().left,
    behavior: "smooth",
  });
});
$("#promoList").addEventListener("scroll", updatePromoPagination, { passive: true });

let lastScrollY = window.scrollY;
let scrollFrame = 0;
window.addEventListener("scroll", () => {
  if (scrollFrame) return;
  scrollFrame = requestAnimationFrame(() => {
    const currentScrollY = window.scrollY;
    const header = document.querySelector(".site-header-public");

    if (currentScrollY <= 80 || currentScrollY < lastScrollY) {
      header.classList.remove("is-hidden");
    } else if (currentScrollY > lastScrollY) {
      header.classList.add("is-hidden");
    }

    lastScrollY = currentScrollY;
    scrollFrame = 0;
  });
}, { passive: true });

async function init() {
  const { ok, data } = await api("/api/contenido");
  if (!ok) {
    $("#films").innerHTML = emptyState(
      "No pudimos cargar la cartelera.",
      '<button class="btn ghost" type="button" data-action="retry">Reintentar</button>'
    );
    return toast(data.error || "No pudimos cargar la cartelera.");
  }

  state.data = data;
  $("#city").innerHTML = Object.keys(data.cities).map(city => `<option>${esc(city)}</option>`).join("");
  $("#city").value = state.city;

  renderBoard();
  renderFilters();
  renderFilms();
  renderStaticSections();
  drawCart();
}

init();