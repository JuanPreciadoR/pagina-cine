# CineStar - Sistema web de gestión de cine

CineStar es una aplicación web de demostración construida con Python, Flask,
SQLite, HTML, CSS y JavaScript. Incluye cartelera, selección de asientos,
registro e inicio de sesión, un carrito de compras y un panel administrativo.
Las compras se guardan en la base de datos, pero no se procesa ningún pago real.

## Requisitos

- Python 3.10 o posterior.
- Git, si vas a clonar el repositorio.
- No se necesita Node.js ni una base de datos externa.

## Instalación y ejecución en Linux o macOS

Abre una terminal en la carpeta donde quieras guardar el proyecto y ejecuta:

```bash
git clone https://github.com/JuanPreciadoR/pagina-cine.git
cd pagina-cine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Si ya tienes el repositorio, omite `git clone` y `cd`; ejecuta los demás
comandos desde la carpeta raíz del proyecto (la que contiene `backend/` y
`requirements.txt`).

En la primera instalación, crea el archivo local de configuración:

```bash
cp .env.example .env
```

Edita `.env` y reemplaza `SECRET_KEY` por un valor aleatorio privado. Puedes
generar uno con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Pega el valor generado después de `SECRET_KEY=` en `.env`. No publiques ni
compartas ese archivo. Si ya existe, no lo sobrescribas.

Inicia el servidor desde la raíz del proyecto y con el entorno virtual activo:

```bash
python backend/app.py
```

Abre <http://127.0.0.1:5000> en el navegador. Mantén abierta la terminal
mientras uses la aplicación; para detenerla, presiona `Ctrl+C`.

## Visual Studio Code y GitHub Codespaces

En VS Code, abre la carpeta del proyecto y sigue los pasos de instalación del
sistema operativo que estés usando. En Codespaces, abre una terminal en la raíz
del repositorio y ejecuta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Configura un `SECRET_KEY` privado en `.env` como se indica arriba. Para que el
servidor sea accesible desde el navegador de Codespaces, enlázalo a todas las
interfaces:

```bash
FLASK_HOST=0.0.0.0 python backend/app.py
```

En VS Code, abre la pestaña **Ports** y visita el puerto `5000` reenviado.
Codespaces puede mostrar la aplicación en una URL HTTPS propia; usa esa URL,
no `127.0.0.1` en tu navegador local. En VS Code ejecutado directamente en tu
PC con Linux o Windows, usa la URL local `http://127.0.0.1:5000`.

## Instalación en Windows (PowerShell)

```powershell
git clone https://github.com/JuanPreciadoR/pagina-cine.git
cd pagina-cine
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python backend/app.py
```

Edita `.env` y cambia `SECRET_KEY` antes de iniciar. Si PowerShell bloquea la
activación del entorno, puedes usar el símbolo del sistema (CMD) en su lugar:

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
copy .env.example .env
python backend\app.py
```

No ejecutes de nuevo `Copy-Item` o `copy` si ya existe `.env`, para no
sobrescribir tu configuración.

## Solución al error `No module named pip` o `No module named flask`

El entorno virtual puede haberse copiado desde otra carpeta. En ese caso,
puede aparecer `(.venv)` en la terminal, pero `python` seguir apuntando al
Python del sistema. En Linux o macOS, desde la raíz del proyecto, recrea el
entorno virtual y reinstala las dependencias:

```bash
deactivate
python3 -m venv --clear --copies .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Si `deactivate` indica que no existe el comando, omite esa línea. Comprueba
que Python y pip pertenecen al entorno del proyecto:

```bash
which python
python -m pip --version
```

Las rutas mostradas deben comenzar con la ruta de este proyecto seguida de
`.venv/`. Luego inicia el servidor:

```bash
python backend/app.py
```

En Windows, cierra y vuelve a abrir la terminal en la raíz del proyecto,
activa `.venv` con los comandos anteriores y ejecuta:

```powershell
python -m pip install -r requirements.txt
```

## Configuración

Las variables opcionales se configuran en `.env`:

| Variable | Valor predeterminado | Descripción |
| --- | --- | --- |
| `SECRET_KEY` | Sin configurar en la plantilla | Clave para firmar las sesiones de Flask. Define un valor privado. |
| `DATABASE_PATH` | `backend/data/cinestar.db` | Ruta de la base de datos SQLite, relativa a la raíz del proyecto o absoluta. |
| `FLASK_HOST` | `127.0.0.1` | Dirección donde escucha el servidor local. |
| `PORT` | `5000` | Puerto HTTP local. |
| `FLASK_DEBUG` | `0` | Usa `1` solo para desarrollo local. |

La base de datos y sus tablas se crean al iniciar la aplicación. No abras
`frontend/templates/index.html` como archivo local: Flask debe servir la página
para que funcionen las rutas API, la autenticación y las sesiones.

## Acceso de prueba

En una base de datos nueva se crea una cuenta de administrador:

- Correo: `admin@cinestar.com`
- Contraseña: `admin123`

Usa estas credenciales solo para desarrollo local. Cambia o elimina la cuenta
antes de desplegar la aplicación en un entorno accesible a otras personas.
El panel está en <http://127.0.0.1:5000/admin>; las operaciones administrativas
requieren iniciar sesión con una cuenta admin.

## Pruebas

Con el entorno virtual activado, ejecuta las pruebas del backend desde la raíz
del repositorio:

```bash
python -m unittest discover -s tests -v
```

La integración continua ejecuta estas pruebas en Linux y Windows con Python
3.10 y 3.14 en cada push y pull request.

## Estructura del proyecto

```text
pagina-cine/
├── .github/
│   └── workflows/
│       └── tests.yml
├── backend/
│   ├── app.py
│   └── data/                 # Base SQLite creada al iniciar
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   └── js/
│   └── templates/
├── .env.example
├── requirements.txt
├── tests/
│   └── test_app.py
└── README.md
```
