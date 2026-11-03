

```markdown
# 🎬 CineStar — Sistema Web de Gestión de Cine

CineStar es una aplicación web full-stack moderna desarrollada con **Python (Flask)**, **SQLite** e interfaces responsivas hechas con **HTML5, JavaScript (ES6+) y CSS3**. El sistema cubre tanto el flujo del cliente (selección visual de asientos, cartelera, compras) como un módulo administrativo para la gestión de usuarios y roles directamente desde la interfaz web sin manipular la base de datos a mano.

---

## 🚀 Características Principales

### 👤 Módulo de Cliente
* **Cartelera Dinámica:** Filtro por formatos (2D, 3D, IMAX, 4DX) y cambio de ciudad.
* **Selección Visual de Asientos:** Mapa interactivo de sala en tiempo real (Fila A-E, 1-6) con bloqueo automático de asientos ya ocupados.
* **Autenticación Integrada:** Inicio de sesión y registro de usuarios mediante ventanas modales nativas.
* **Carrito y Checkout:** Proceso fluido de compra con validación de sesión activa.
* **Tema Visual:** Selector de modo oscuro / claro guardado en el navegador.

### ⚙️ Módulo Administrativo (Solo Admin)
* **Panel de Control Web (`/admin`):** Gestión completa sin requerir herramientas SQL externas.
* **Gestión de Usuarios:** Ver todos los usuarios registrados, cambiar roles (`cliente` ↔ `admin`) y eliminar cuentas.
* **Integridad Referencial:** Control de acceso en la API (restringe endpoints a usuarios con rol `admin`).

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3.x, Flask, Werkzeug (Encriptado de contraseñas con Scrypt).
* **Base de Datos:** SQLite3 con restricciones `CHECK`, `UNIQUE` y `FOREIGN KEY`.
* **Frontend:** HTML5, CSS3, JavaScript nativo (Fetch API, Async/Await).
* **Entorno & Variables:** Python-dotenv.

---

## 📋 Requisitos Previos

* **Python 3.10+** instalado.
* **Git** instalado.

---

## 💻 Guía de Instalación y Ejecución

Sigue estos pasos según tu sistema operativo:

### 🐧 Opción A: En Linux (Fedora, Ubuntu, Debian, Arch) / macOS

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/pagina-cine.git](https://github.com/TU_USUARIO/pagina-cine.git)
   cd pagina-cine

```

2. **Crear y activar el entorno virtual (`venv`):**
```bash
python3 -m venv venv
source venv/bin/activate

```


3. **Instalar dependencias:**
```bash
pip install -r requirements.txt

```


4. **Configurar el archivo de entorno:**
```bash
cp .env.example .env

```


5. **Iniciar el servidor:**
```bash
python3 app.py

```



---

### 🪟 Opción B: En Windows (PowerShell / Command Prompt)

1. **Clonar el repositorio:**
```cmd
git clone [https://github.com/TU_USUARIO/pagina-cine.git](https://github.com/TU_USUARIO/pagina-cine.git)
cd pagina-cine

```


2. **Crear y activar el entorno virtual (`venv`):**
```cmd
python -m venv venv
venv\Scripts\activate

```


3. **Instalar dependencias:**
```cmd
pip install -r requirements.txt

```


4. **Configurar el archivo de entorno:**
```cmd
copy .env.example .env

```


5. **Iniciar el servidor:**
```cmd
python app.py

```



---

## 🔑 Credenciales por Defecto (Pruebas)

Al ejecutar la aplicación por primera vez, el sistema creará automáticamente la base de datos `cinestar.db` y generará la cuenta de administrador inicial:

| Rol | Correo Electrónico | Contraseña | Acceso |
| --- | --- | --- | --- |
| **Administrador** | `admin@cinestar.com` | `admin123` | Acceso total a `/` y `/admin` |
| **Cliente** | *(Registrar nuevo en la web)* | *(Mínimo 6 caracteres)* | Acceso a compras y cartelera |

---

## 🔍 Inspección de la Base de Datos

Si deseas examinar directamente las tablas (`usuarios`, `compras`, `contenido`) de forma visual:

* **Herramienta recomendada:** [DB Browser for SQLite](https://sqlitebrowser.org/) (Gratuito y multiplataforma).
* En Linux Fedora: `sudo dnf install sqlitebrowser`
* En VSCode: Extensión **SQLite Viewer** (de *qwtel*).

---

## 📂 Estructura del Proyecto

```text
pagina-cine/
├── app.py              # Servidor Flask, API REST y conexión a la BD
├── cinestar.db         # Base de datos SQLite (se genera al iniciar)
├── .env.example        # Plantilla pública de variables de entorno
├── .gitignore          # Archivos excluidos del repositorio Git
├── requirements.txt    # Dependencias del proyecto
├── README.md           # Documentación
├── static/
│   ├── css/
│   │   └── style.css   # Estilos globales y temas
│   └── js/
│       ├── script.js   # Lógica del cliente, asientos y carrito
│       └── login.js    # Control de sesión y ventanas modales
└── templates/
    ├── index.html      # Portal principal para clientes
    └── admin.html      # Panel administrativo

```
