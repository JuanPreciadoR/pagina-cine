Aquí tienes el archivo **`README.md`** completo, estructurado de forma ejecutiva y técnica. Está optimizado para portafolio en GitHub y entregas académicas, resaltando la arquitectura del proyecto sin texto de relleno.

Copia y reemplaza el contenido de tu archivo **`README.md`**:

```markdown
# CineStar — Aplicación Web Cinematográfica

Sistema web full-stack para la exploración de cartelera, selección interactiva de asientos en tiempo real, reserva de boletas y administración de ventas y usuarios.

---

## 🛠️ Arquitectura y Tecnologías

* **Backend:** Python 3 + Flask (API RESTful), Werkzeug (criptografía con Scrypt), `python-dotenv`.
* **Base de Datos:** SQLite3 con restricciones de integridad referencial (`FOREIGN KEY ON DELETE CASCADE`, cláusulas `CHECK` y aislamiento por transacciones con `contextmanager`).
* **Frontend:** HTML5 semántico (`<dialog>` nativos para modales y modales de asientos), CSS3 moderno basado en tokens/variables y arquitectura JS ES6+ modularizada (sin librerías de terceros).

---

## 📁 Estructura del Proyecto

```text
pagina_cine/
├── backend/
│   ├── app.py              # API REST, autenticación, control de sesiones y endpoints admin
│   └── data/
│       └── cinestar.db     # Base de datos SQLite3
├── frontend/
│   ├── static/
│   │   ├── css/            # Estilos globales (style.css, admin.css)
│   │   └── js/             # Lógica cliente (common.js, script.js, login.js, admin.js)
│   └── templates/
│       ├── index.html      # Vista pública (cartelera, selección de sillas, carrito)
│       └── admin.html      # Panel de administración y dashboard
├── .env.example            # Variables de entorno de muestra
├── requirements.txt        # Dependencias de Python
└── README.md

```

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio y entrar al proyecto

```bash
git clone <URL_DE_TU_REPOSITY>
cd pagina_cine

```

### 2. Configurar el entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

### 3. Ejecutar el servidor de desarrollo

```bash
python3 backend/app.py

```

El servidor iniciará en `http://127.0.0.1:5000`.

---

## ⚙️ Características Clave

### Vista Cliente (`/`)

* **Cartelera Dinámica:** Filtros por formato (2D, 3D, IMAX, 4DX) y sede/ciudad.
* **Mapa de Asientos Interactivos:** Consulta en tiempo real de disponibilidad por función y bloqueo de sillas ocupadas.
* **Autenticación Modal:** Registro e inicio de sesión seguro con almacenamiento de contraseñas hasheadas.
* **Carrito de Compras:** Gestión de múltiples boletas y cálculo dinámico de totales.

### Panel de Administración (`/admin`)

* **Métricas en Vivo:** Indicadores clave de recaudo total, boletas vendidas, usuarios registrados y película más vendida.
* **Gestión de Usuarios:** Control de roles (`admin`, `cliente`, `cajero`, `gerente`) y borrado seguro de cuentas en cascada.
* **Gestión de Cartelera:** Publicación y eliminación de películas en el sistema.
* **Historial de Ventas:** Registro detallado de transacciones con cliente, película, función y asientos asignados.

---

## 🔐 Credenciales de Prueba (Entorno Local)

* **Usuario Administrador:** `admin@cinestar.com`
* **Contraseña:** `admin123`

---

## 📝 Justificación de Diseño de Base de Datos

Aunque el modelo de dominio original se diseñó bajo una estructura relacional 3NF completa, para este entorno de ejecución ligero se utilizó **SQLite3** con la opción `PRAGMA foreign_keys = ON` activada y control manual de transacciones desde Flask, garantizando la consistencia de datos sin requerir un motor de base de datos pesado para la demostración.

```

---

### Guardar el archivo en Git:

Una vez guardado tu `README.md`, puedes registrar la actualización en tu repositorio local con:

```bash
git add README.md
git commit -m "docs: Actualización del README con arquitectura, instalación y mapa de características"

```