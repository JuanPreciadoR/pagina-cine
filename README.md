# CineStar — Aplicación Web Cinematográfica

Sistema web full-stack para la exploración de cartelera, selección interactiva de asientos en tiempo real, reserva de boletas y administración de ventas y usuarios.

---

## 🛠️ Arquitectura y Tecnologías

* **Backend:** Python 3 + Flask (API RESTful), Werkzeug (criptografía con Scrypt), `python-dotenv`.
* **Base de Datos:** SQL Server, conectado con `pyodbc`; las tablas y relaciones se definen en `backend/database/script_cinestar.sql`.
* **Frontend:** HTML5 semántico (`<dialog>` nativos para modales y modales de asientos), CSS3 moderno basado en tokens/variables y arquitectura JS ES6+ modularizada (sin librerías de terceros).

---

## 📁 Estructura del Proyecto

```text
pagina_cine/
├── backend/
│   ├── app.py              # Aplicación Flask
│   ├── db.py               # Conexión a SQL Server
│   ├── init_admin.py       # Creación/restablecimiento del administrador
│   ├── database/           # Esquema de SQL Server, sin datos de demostración
│   └── routes/             # Autenticación, cartelera y API de administración
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
cp .env.example .env

```

Configura en `.env` el servidor, base, usuario, contraseña SQL Server y una `SECRET_KEY` aleatoria. Se requiere el controlador ODBC 18 para SQL Server. La aplicación solo admite SQL Server y no usa una base local alternativa.

### 3. Crear el esquema

Ejecuta `backend/database/script_cinestar.sql` una sola vez en una instancia donde todavía no exista `CineDB`. El script crea únicamente las tablas y restricciones; se detiene si la base ya existe y nunca la borra.

### 4. Cargar la cartelera y crear el administrador

Desde la raíz del proyecto, carga el catálogo inicial y luego crea o restablece el administrador:

```bash
python backend/seed_catalog.py
python backend/init_admin.py
```

El catálogo es idempotente: agrega las cuatro películas con póster, sedes, salas, sillas y funciones para los próximos siete días cuando faltan, sin borrar ventas, usuarios ni otros registros. El acceso inicial es `admin@cinestar.com` con contraseña `admin123`; ejecuta `python backend/init_admin.py` para crear o restablecer esa cuenta. Esa clave es solo para desarrollo local: cámbiala antes de publicar la aplicación.

### 5. Ejecutar el servidor de desarrollo

```bash
python3 backend/app.py

```

El servidor iniciará en `http://127.0.0.1:5000`.

---

## ⚙️ Características Clave

### Vista Cliente (`/`)

* **Cartelera Dinámica:** Películas, pósteres, funciones, precios, sedes y formatos consultados desde SQL Server.
* **Mapa de Asientos Interactivos:** Consulta la sala y las sillas disponibles para cada función; la compra vuelve a validar la disponibilidad dentro de una transacción.
* **Autenticación Modal:** Registro e inicio de sesión seguro con almacenamiento de contraseñas hasheadas.
* **Carrito de Compras:** Gestión de múltiples boletas y cálculo dinámico de totales.

### Panel de Administración (`/admin`)

* **Métricas en Vivo:** Indicadores clave de recaudo total, boletas vendidas, usuarios registrados y película más vendida.
* **Datos disponibles:** métricas, lista de usuarios y ventas.

---

El esquema activa claves foráneas y restricciones `CHECK`. El catálogo de inicio se agrega con `backend/seed_catalog.py`; no se insertan ventas de prueba.