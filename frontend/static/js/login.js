/* login.js · Sesión, registro y redirección por rol */
(() => {
    const dialog = $("#loginDialog");
    const form = $("#loginForm");
    const fields = { name: $("#regName"), email: $("#loginEmail"), password: $("#loginPass") };

    const MODES = {
        login: {
            title: "Iniciar sesión",
            sub: "Ingresa con tu cuenta para comprar más rápido.",
            submit: "Iniciar sesión",
            switchText: "¿No tienes cuenta?",
            switchLabel: "Regístrate",
            autocomplete: "current-password",
            endpoint: "/api/login",
        },
        register: {
            title: "Crear cuenta",
            sub: "Regístrate para guardar tus compras.",
            submit: "Crear cuenta",
            switchText: "¿Ya tienes cuenta?",
            switchLabel: "Inicia sesión",
            autocomplete: "new-password",
            endpoint: "/api/registro",
        },
    };

    let mode = "login";
    let user = null;

    const firstName = () => user.nombre.split(" ")[0];

    function showError(message = "") {
        const el = $("#loginError");
        el.textContent = message;
        el.hidden = !message;
    }

    function setMode(next) {
        mode = next;
        const copy = MODES[next];
        $("#loginTitle").textContent = copy.title;
        $("#loginSub").textContent = copy.sub;
        $("#loginSubmit").textContent = copy.submit;
        $("#switchText").textContent = copy.switchText;
        $("#switchMode").textContent = copy.switchLabel;
        $("#nameField").hidden = next !== "register";
        $("#forgotLink").hidden = next === "register";
        fields.password.autocomplete = copy.autocomplete;
        showError();
    }

    function renderSession() {
        $("#sessionLabel").textContent = user ? "Cerrar sesión" : "Iniciar sesión";
        $("#greeting").hidden = !user;
        $("#greeting").textContent = user ? `Hola, ${firstName()}` : "";
        $("#adminLink").hidden = user?.rol !== "admin";
    }

    function openDialog() {
        form.reset();
        setMode("login");
        dialog.showModal();
        fields.email.focus();
    }

    async function logout() {
        const { ok, data } = await api("/api/logout", { method: "POST", body: {} });
        if (!ok) return toast(data.error || "No pudimos cerrar la sesión.");
        user = null;
        renderSession();
        toast("Sesión cerrada.");
    }

    async function submit(event) {
        event.preventDefault();
        const name = fields.name.value.trim();
        const email = fields.email.value.trim().toLowerCase();
        const password = fields.password.value;

        if (mode === "register" && !name) return showError("Escribe tu nombre.");
        if (!/^\S+@\S+\.\S+$/.test(email)) return showError("Escribe un correo válido.");
        if (password.length < 6) return showError("La contraseña debe tener mínimo 6 caracteres.");

        const button = $("#loginSubmit");
        button.disabled = true;
        const { ok, data } = await api(MODES[mode].endpoint, {
            method: "POST",
            body: mode === "register" ? { nombre: name, email, password } : { email, password },
        });
        button.disabled = false;

        if (!ok) return showError(data.error || "No pudimos completar la solicitud. Inténtalo de nuevo.");

        user = data.usuario;
        dialog.close();
        renderSession();
        toast(`${mode === "register" ? "Cuenta creada. Bienvenido" : "Hola de nuevo"}, ${firstName()}.`);

        if (user.rol === "admin") setTimeout(() => location.assign("/admin"), 600);
    }

    $("#sessionBtn").addEventListener("click", () => (user ? logout() : openDialog()));
    $("#switchMode").addEventListener("click", () => setMode(mode === "login" ? "register" : "login"));
    $("#forgotLink").addEventListener("click", () => toast("El restablecimiento de contraseña aún no está disponible."));
    $("#togglePass").addEventListener("click", event => {
        const reveal = fields.password.type === "password";
        fields.password.type = reveal ? "text" : "password";
        event.currentTarget.textContent = reveal ? "Ocultar" : "Mostrar";
    });
    form.addEventListener("submit", submit);
    document.addEventListener("login:required", openDialog);

    (async () => {
        const { ok, data } = await api("/api/sesion");
        if (ok && data.logueado) user = data.usuario;
        renderSession();
    })();
})();