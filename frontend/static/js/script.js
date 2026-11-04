/* static/script.js - Asientos interactivos y flujo de compra */
const $ = s => document.querySelector(s);
const cop = n => "$" + n.toLocaleString("es-CO");

let D = null;
let city = "Bogotá", fmt = "Todos", cart = [];
let funcionSeleccionada = null;

function setTema(t) {
  document.documentElement.setAttribute("data-tema", t);
  try { localStorage.setItem("CineStar-tema", t); } catch (e) {}
  $("#themeBtn").textContent = t === "oscuro" ? "☀ Modo claro" : "☾ Modo oscuro";
}
$("#themeBtn").onclick = () => setTema(
  document.documentElement.getAttribute("data-tema") === "oscuro" ? "claro" : "oscuro"
);
setTema(document.documentElement.getAttribute("data-tema") || "oscuro");

const price = f => D.ticketPrices[f] || D.ticketPrices.default;
const timeBtn = (f, s) => `<button class="t" data-film="${f.title}" data-time="${s}" data-format="${f.format}">${s}</button>`;
const ang = i => `${140 + (i % 5) * 18}deg`;

function renderBoard() {
  $("#boardCity").textContent = city;
  const sedes = D.cities[city];
  $("#board").innerHTML = D.films.slice(0, 4).map((f, i) =>
    `<div class="row"><div><strong>${f.title}</strong><small>${sedes[i % sedes.length]} · ${f.format}</small></div>
    <div class="times">${D.slots.slice(i % 3, i % 3 + 2).map(s => timeBtn(f, s)).join("")}</div></div>`
  ).join("");
}

function renderFilms() {
  $("#fmt").innerHTML = D.formats.map(x =>
    `<button class="tab" aria-pressed="${x === fmt}" data-fmt="${x}">${x}</button>`
  ).join("");
  const list = D.films.filter(f => fmt === "Todos" || f.format === fmt);
  $("#films").innerHTML = list.length
    ? list.map((f, i) => `<article class="film"><div class="poster" style="--ang:${ang(i)}"><em>${f.rating} · ${f.format}</em>${f.title}</div>
      <h3>${f.title}</h3><div class="meta">${f.genre} · ${f.duration}</div>
      <div class="times">${D.slots.slice(0, 4).map(s => timeBtn(f, s)).join("")}</div></article>`).join("")
    : '<p class="meta">No hay funciones en este formato hoy.</p>';
}

function drawCart() {
  $("#count").textContent = cart.length;
  $("#items").innerHTML = cart.length
    ? cart.map((c, i) => `<div class="item"><span>${c.pelicula} (${c.formato})<br><small>${c.funcion} - Sillas: ${c.asientos.join(", ")}</small></span>
        <span>${cop(price(c.formato) * c.asientos.length)} <button data-del="${i}" aria-label="Quitar">✕</button></span></div>`).join("")
    : '<p class="meta">Aún no has seleccionado funciones.</p>';
  
  const subtotal = cart.reduce((a, c) => a + (price(c.formato) * c.asientos.length), 0);
  $("#total").textContent = "Total " + cop(subtotal);
}

function toast(m) {
  const t = $("#toast");
  t.textContent = m; t.style.display = "block";
  clearTimeout(t._h); t._h = setTimeout(() => t.style.display = "none", 2600);
}

/* MODAL DE ASIENTOS */
async function abrirModalAsientos(pelicula, funcion, formato) {
  funcionSeleccionada = { pelicula, funcion, formato, seleccionados: [] };
  
  let seatModal = $("#seatModal");
  if (!seatModal) {
    seatModal = document.createElement("div");
    seatModal.id = "seatModal";
    seatModal.className = "login-overlay";
    seatModal.innerHTML = `
      <div class="login-modal" style="width:min(480px, 100%); text-align:center;">
        <button class="login-close" id="closeSeats">✕</button>
        <h2 id="seatModalTitle">Selecciona tus asientos</h2>
        <p class="login-sub" id="seatModalSub"></p>
        <div style="background:var(--line); color:var(--mute); margin:15px 0; padding:6px; border-radius:6px; font-size:0.8rem; font-weight:bold;">PANTALLA</div>
        <div id="seatsGrid" style="display:grid; grid-template-columns:repeat(6, 1fr); gap:8px; margin:20px 0;"></div>
        <button class="btn" id="confirmSeats" style="width:100%;">Confirmar Selección</button>
      </div>`;
    document.body.appendChild(seatModal);
    $("#closeSeats").onclick = () => seatModal.hidden = true;
  }
  
  $("#seatModalTitle").textContent = pelicula;
  $("#seatModalSub").textContent = `Función: ${funcion} (${formato})`;
  seatModal.hidden = false;

  let ocupados = [];
  try {
    const res = await fetch(`/api/asientos-ocupados?pelicula=${encodeURIComponent(pelicula)}&funcion=${encodeURIComponent(funcion)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "No se pudo consultar la disponibilidad.");
    ocupados = data.asientos_ocupados || [];
  } catch (e) {
    console.error(e);
    seatModal.hidden = true;
    toast(e.message || "No fue posible consultar los asientos.");
    return;
  }

  const filas = ["A", "B", "C", "D", "E"];
  let gridHTML = "";
  filas.forEach(f => {
    for (let c = 1; c <= 6; c++) {
      const code = `${f}${c}`;
      const isOcupado = ocupados.includes(code);
      gridHTML += `<button class="seat-btn ${isOcupado ? 'occupied' : ''}" data-seat="${code}" ${isOcupado ? 'disabled' : ''} style="padding:8px; border-radius:6px; border:1px solid var(--line); background:${isOcupado ? '#ff6b6b' : 'var(--bg2)'}; color:var(--ink);">${code}</button>`;
    }
  });
  $("#seatsGrid").innerHTML = gridHTML;

  document.querySelectorAll(".seat-btn:not(.occupied)").forEach(btn => {
    btn.onclick = () => {
      const code = btn.dataset.seat;
      if (funcionSeleccionada.seleccionados.includes(code)) {
        funcionSeleccionada.seleccionados = funcionSeleccionada.seleccionados.filter(s => s !== code);
        btn.style.background = "var(--bg2)";
      } else {
        funcionSeleccionada.seleccionados.push(code);
        btn.style.background = "var(--accent)";
      }
    };
  });

  $("#confirmSeats").onclick = () => {
    if (!funcionSeleccionada.seleccionados.length) return toast("Selecciona al menos un asiento.");
    const sameFunction = cart.find(item =>
      item.pelicula === funcionSeleccionada.pelicula &&
      item.funcion === funcionSeleccionada.funcion &&
      item.formato === funcionSeleccionada.formato
    );
    const duplicateSeats = sameFunction
      ? funcionSeleccionada.seleccionados.filter(seat => sameFunction.asientos.includes(seat))
      : [];
    if (duplicateSeats.length) {
      return toast(`Ya agregaste estos asientos: ${duplicateSeats.join(", ")}`);
    }
    if (sameFunction) {
      sameFunction.asientos.push(...funcionSeleccionada.seleccionados);
    } else {
      cart.push({
        pelicula: funcionSeleccionada.pelicula,
        funcion: funcionSeleccionada.funcion,
        formato: funcionSeleccionada.formato,
        asientos: [...funcionSeleccionada.seleccionados]
      });
    }
    drawCart();
    seatModal.hidden = true;
    toast(`${funcionSeleccionada.seleccionados.length} asiento(s) agregados`);
  };
}

/* Eventos globales */
document.addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.film) {
    abrirModalAsientos(b.dataset.film, b.dataset.time, b.dataset.format);
  } else if (b.dataset.fmt) {
    fmt = b.dataset.fmt; renderFilms();
  } else if (b.dataset.del !== undefined) {
    cart.splice(+b.dataset.del, 1); drawCart();
  } else if (b.dataset.toast) {
    toast(b.dataset.toast);
  }
});

$("#openCart").onclick = () => $("#cart").classList.add("open");
$("#closeCart").onclick = () => $("#cart").classList.remove("open");

$("#pay").onclick = async () => {
  if (!cart.length) return toast("Tu compra está vacía");
  const payButton = $("#pay");
  payButton.disabled = true;

  try {
    while (cart.length) {
      const item = cart[0];
      const res = await fetch("/api/compra", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(item),
      });
      const data = await res.json().catch(() => ({}));

      if (res.status === 401) {
        $("#cart").classList.remove("open");
        toast("Inicia sesión para completar tu compra.");
        setTimeout(() => {
          if ($("#loginOverlay")) $("#loginOverlay").hidden = false;
        }, 400);
        return;
      }

      if (!res.ok) {
        toast(data.error || "No se pudo registrar la compra. Tu carrito se conservó.");
        return;
      }

      cart.shift();
      drawCart();
    }

    toast("¡Todas tus compras se registraron con éxito!");
    $("#cart").classList.remove("open");
  } catch (e) {
    console.error(e);
    toast("No fue posible conectar con el servidor. Se conservó lo pendiente.");
  } finally {
    payButton.disabled = false;
  }
};

(async function init() {
  try {
    const res = await fetch("/api/contenido", { credentials: "same-origin" });
    D = await res.json();
    if (!res.ok) throw new Error(D.error || "No se pudo cargar el contenido.");

    $("#city").innerHTML = Object.keys(D.cities).map(c => `<option>${c}</option>`).join("");
    $("#city").value = city;
    $("#city").onchange = e => { city = e.target.value; renderBoard(); };

    $("#promoList").innerHTML = D.promos.map(p =>
      `<div class="promo"><h3>${p.title}</h3><span>${p.text}</span></div>`).join("");
    $("#soon").innerHTML = D.soon.map((s, i) =>
      `<article class="film"><div class="poster" style="--ang:${ang(i)}"><em>${s.tag}</em>${s.title}</div>
        <h3>${s.title}</h3><div class="meta">${s.genre}</div>
        <button class="btn ghost" data-toast="Notificación registrada">Avísame</button></article>`).join("");
    $("#faq").innerHTML = D.faq.map(f =>
      `<details><summary>${f.q}</summary><p>${f.a}</p></details>`).join("");

    renderBoard(); renderFilms(); drawCart();
  } catch (e) {
    console.error(e);
    toast("No se pudo cargar el contenido");
  }
})();