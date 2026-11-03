/* static/login.js - Autenticación limpia con redirección por rol */
(function () {
  const $ = s => document.querySelector(s);
  let modoRegistro = false;
  let usuario = null;

  const aviso = m => typeof toast === "function" ? toast(m) : alert(m);

  async function api(url, body) {
    try {
      const res = await fetch(url, {
        method: body ? "POST" : "GET",
        headers: body ? { "Content-Type": "application/json" } : {},
        credentials: "same-origin",
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json().catch(() => ({}));
      return { ok: res.ok, status: res.status, data };
    } catch (e) {
      console.error(e);
      return { ok: false, status: 0, data: { error: "No fue posible conectar con el servidor." } };
    }
  }

  function pintarBoton() {
    const btn = $("#loginLabel");
    if (!btn) return;
    if (usuario) {
      btn.textContent = usuario.rol === "admin" 
        ? `${usuario.nombre.split(" ")[0]} (Admin)` 
        : `${usuario.nombre.split(" ")[0]} · Salir`;
      
      let adminLink = $("#adminHeaderLink");
      if (usuario.rol === "admin" && !adminLink) {
        adminLink = document.createElement("a");
        adminLink.id = "adminHeaderLink";
        adminLink.href = "/admin";
        adminLink.textContent = "⚙️ Panel Admin";
        adminLink.className = "btn ghost";
        adminLink.style.marginLeft = "8px";
        $("#openLogin").parentNode.insertBefore(adminLink, $("#openLogin"));
      }
    } else {
      btn.textContent = "Iniciar sesión";
      const adminLink = $("#adminHeaderLink");
      if (adminLink) adminLink.remove();
    }
  }

  function modo(registro) {
    modoRegistro = registro;
    $("#loginTitle").textContent = registro ? "Crear cuenta" : "Iniciar sesión";
    $("#loginSub").textContent = registro
      ? "Regístrate para guardar tus compras."
      : "Ingresa con tu cuenta para comprar más rápido.";
    $("#loginSubmit").textContent = registro ? "Registrarme" : "Iniciar sesión";
    $("#switchText").textContent = registro ? "¿Ya tienes cuenta?" : "¿No tienes cuenta?";
    $("#switchMode").textContent = registro ? "Inicia sesión" : "Regístrate";
    $("#nameField").hidden = !registro;
    $("#forgotLink").hidden = registro;
    $("#loginPass").autocomplete = registro ? "new-password" : "current-password";
    error("");
  }

  function error(m) { const e = $("#loginError"); e.textContent = m; e.hidden = !m; }

  function abrir() {
    modo(false);
    $("#loginForm").reset();
    $("#loginOverlay").hidden = false;
    setTimeout(() => $("#loginEmail").focus(), 0);
  }
  function cerrar() { $("#loginOverlay").hidden = true; }

  (async function init() {
    const { ok, data } = await api("/api/sesion");
    if (ok && data.logueado) { usuario = data.usuario; }
    pintarBoton();
  })();

  $("#openLogin").onclick = async () => {
    if (usuario) {
      const { ok, data } = await api("/api/logout", {});
      if (!ok) return aviso(data.error || "No se pudo cerrar la sesión.");
      usuario = null;
      pintarBoton();
      aviso("Sesión cerrada");
    } else {
      abrir();
    }
  };
  $("#closeLogin").onclick = cerrar;
  $("#loginOverlay").addEventListener("mousedown", e => { if (e.target.id === "loginOverlay") cerrar(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("#loginOverlay").hidden) cerrar(); });

  $("#switchMode").onclick = e => { e.preventDefault(); modo(!modoRegistro); };
  $("#forgotLink").onclick = e => { e.preventDefault(); aviso("Restablecimiento no configurado."); };
  $("#togglePass").onclick = () => {
    const i = $("#loginPass"), ver = i.type === "password";
    i.type = ver ? "text" : "password";
    $("#togglePass").textContent = ver ? "Ocultar" : "Ver";
  };

  $("#loginForm").onsubmit = async e => {
    e.preventDefault();
    const email = $("#loginEmail").value.trim().toLowerCase();
    const password = $("#loginPass").value;
    const nombre = $("#regName").value.trim();
    if (!/^\S+@\S+\.\S+$/.test(email)) return error("Escribe un correo válido.");
    if (password.length < 6) return error("La contraseña debe tener mínimo 6 caracteres.");

    const url = modoRegistro ? "/api/registro" : "/api/login";
    const payload = modoRegistro ? { nombre, email, password } : { email, password };
    const { ok, data } = await api(url, payload);

    if (!ok) return error(data.error || "No se pudo iniciar sesión.");

    usuario = data.usuario;
    cerrar();
    pintarBoton();
    aviso((modoRegistro ? "Cuenta creada. ¡Bienvenido, " : "¡Hola de nuevo, ") + usuario.nombre.split(" ")[0] + "!");
    
    // Redirección fluida para el administrador
    if (usuario.rol === "admin") {
      setTimeout(() => {
        window.location.href = "/admin";
      }, 500);
    }
  };
})();