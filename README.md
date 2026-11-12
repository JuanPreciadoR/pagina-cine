# CineStar

Aplicación web de cartelera y venta de boletas con Flask y Microsoft SQL Server. Esta guía permite instalarla desde un clon nuevo en Linux o Windows.

## Requisitos

- Python 3.10 o posterior y Git.
- SQL Server accesible mediante autenticación SQL.
- Microsoft ODBC Driver 18 for SQL Server.
- Docker Desktop en Windows o Docker Engine en Linux si se usa la opción recomendada de base de datos en contenedor.

La aplicación no usa SQLite. Sin SQL Server y ODBC 18, las páginas pueden abrir, pero las APIs de cartelera, autenticación, compra y administración no funcionarán.

Instala el controlador desde la documentación oficial de [ODBC en Linux](https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server) o el [instalador de ODBC para Windows](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server). En Windows, instala la versión x64.

## 1. Clonar e instalar Python

Reemplaza la URL de ejemplo por la URL real del repositorio.

### Linux (Bash)

```bash
git clone <URL_DEL_REPOSITORIO>
cd pagina_cine
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

En Ubuntu/Debian, instala `python3-venv` si el comando `venv` no está disponible.

### Windows (PowerShell)

```powershell
git clone <URL_DEL_REPOSITORIO>
cd pagina_cine
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si PowerShell bloquea la activación, ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` en esa ventana y vuelve a activar. En CMD usa `.venv\Scripts\activate.bat`.

## 2. Iniciar SQL Server

### Opción recomendada: Docker

Instala Docker (en Windows, usa contenedores Linux en Docker Desktop) y ejecuta el comando siguiente en Bash o PowerShell. La imagen oficial requiere un equipo x86-64. Cambia la contraseña de ejemplo y guarda el valor para usarlo también en `.env`.

```sh
docker run --name cinestar-sqlserver --restart unless-stopped -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD='ChangeThis_Sql2026' -p 1433:1433 -v cinestar-sql-data:/var/opt/mssql -d mcr.microsoft.com/mssql/server:2022-latest
```

El volumen `cinestar-sql-data` conserva la base aunque se detenga o elimine el contenedor. No elimines el volumen si necesitas conservar los datos. Espera a que SQL Server inicie; puedes revisar su estado con `docker logs cinestar-sqlserver`.

### Usar una instancia SQL Server existente

Habilita TCP/IP y autenticación SQL, permite conexiones al puerto elegido y usa credenciales con permisos para crear una base de datos. SQL Server Express en Windows puede usar una instancia con nombre y otro puerto; configura `DB_SERVER` y `DB_PORT` con los valores reales. En Windows, SSMS permite ejecutar el script del esquema.

## 3. Configurar `.env`

Edita el `.env` creado desde `.env.example`. El archivo `.env` está excluido por `.gitignore`; no lo subas al repositorio.

```dotenv
DB_SERVER=localhost
DB_PORT=1433
DB_NAME=CineDB
DB_USER=sa
DB_PASS=ChangeThis_Sql2026
SECRET_KEY=reemplaza-por-un-valor-aleatorio-largo
FLASK_HOST=127.0.0.1
PORT=5000
ADMIN_INITIAL_PASSWORD=admin123
```

`DB_PASS` debe coincidir con la contraseña configurada en SQL Server. Genera un valor para `SECRET_KEY` con `python -c "import secrets; print(secrets.token_hex(32))"` y pégalo en `.env`. Cambia también `ADMIN_INITIAL_PASSWORD` antes de crear la cuenta. Las credenciales de ejemplo son solo para desarrollo local.

Comprueba que `pyodbc` detecta el controlador:

```sh
python -c "import pyodbc; print(pyodbc.drivers())"
```

La salida debe incluir `ODBC Driver 18 for SQL Server`.

## 4. Crear la base y cargar los datos iniciales

`backend/database/script_cinestar.sql` crea `CineDB`, sus tablas y restricciones. Se detiene si `CineDB` ya existe; no elimina ni reemplaza bases existentes. Ejecútalo una sola vez en una instancia nueva y no sobre una base que ya tenga datos.

Para SQL Server iniciado con Docker desde la raíz del repositorio, copia y ejecuta el script:

```sh
docker cp backend/database/script_cinestar.sql cinestar-sqlserver:/tmp/script_cinestar.sql
docker exec cinestar-sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'ChangeThis_Sql2026' -C -b -i /tmp/script_cinestar.sql
```

Usa en `-P` la contraseña de SQL Server que elegiste. `-C` confía en el certificado del servidor local y `-b` devuelve un error si el script falla. Para otra instancia, ejecuta el archivo con SSMS o `sqlcmd`; el script contiene separadores `GO`.

Con `.env` configurado y la base creada, ejecuta desde la raíz del repositorio:

```sh
python backend/seed_catalog.py
python backend/init_admin.py
```

El seed agrega cuatro películas, sedes, salas, asientos y funciones para siete días de forma idempotente; no elimina datos ni crea ventas de prueba. `init_admin.py` crea o restablece el administrador con la contraseña indicada por `ADMIN_INITIAL_PASSWORD`. Las credenciales del `.env.example` son `admin@cinestar.com` / `admin123`.

## 5. Ejecutar y verificar

Con el entorno virtual activo:

```sh
python backend/app.py
```

Abre <http://127.0.0.1:5000>. `/` sirve la aplicación y <http://127.0.0.1:5000/api/contenido> debe devolver JSON con películas, funciones, sedes y formas de pago. Si falla la API, revisa el estado de SQL Server, los valores `DB_SERVER`, `DB_PORT`, `DB_USER` y `DB_PASS`, y la instalación de ODBC 18.

El servidor de desarrollo escucha solo en el equipo local por defecto. No lo expongas a Internet; `FLASK_DEBUG` debe permanecer desactivado fuera del desarrollo local.

## Solución de problemas

- `No module named ...`: activa `.venv` e instala de nuevo con `python -m pip install -r requirements.txt`.
- `Can't open lib 'ODBC Driver 18 for SQL Server'`: instala ODBC Driver 18 para el sistema y la arquitectura de Python en uso.
- Error de conexión: confirma que SQL Server está iniciado, que el puerto coincide con `DB_PORT` y que las credenciales de `.env` son correctas. Revisa el firewall si la base está en otro equipo.
- `CineDB ya existe`: no ejecutes de nuevo el inicializador del esquema. Conecta la aplicación a esa base o prepara conscientemente otra instancia.
- Cartelera vacía: ejecuta `python backend/seed_catalog.py` con `.env` correcto y comprueba la respuesta de `/api/contenido`.

## Tecnologías

- Backend: Python, Flask, Werkzeug, `python-dotenv` y `pyodbc`.
- Base de datos: Microsoft SQL Server.
- Frontend: HTML, CSS y JavaScript sin dependencias externas.

## Pruebas automatizadas

Con el entorno virtual activo, ejecuta desde la raíz:

```sh
python -m pytest -q
```

Las pruebas usan una base simulada y no necesitan conectarse a SQL Server.

## Despliegue seguro en Linux

No expongas el servidor de desarrollo de Flask. Para producción configura `APP_ENV=production`, una `SECRET_KEY` larga generada aleatoriamente y `RATELIMIT_STORAGE_URI` apuntando a Redis (`redis://` o `rediss://`). La aplicación se niega a iniciar en producción si falta la clave o Redis. Protege Redis en una red privada y usa TLS/autenticación cuando corresponda.

Usa una cuenta SQL con los permisos mínimos que requiera la aplicación; no despliegues con el usuario `sa`. Mantén `.env` fuera del repositorio y suministra los secretos mediante el gestor de secretos del servidor.

Instala Gunicorn en el entorno virtual y ejecútalo desde `backend/`, enlazado solo a loopback detrás de un proxy inverso configurado con HTTPS:

```sh
python -m pip install gunicorn
cd backend
../.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app
```

El proxy debe terminar TLS, sobrescribir los encabezados `X-Forwarded-For`, `X-Forwarded-Proto` y `X-Forwarded-Host`, y reenviar tráfico a Gunicorn. La aplicación confía en un único proxy en producción. Habilita cookies `HttpOnly`, `SameSite=Lax` y `Secure`, sesiones de hasta 8 horas, encabezados de seguridad y un máximo de 5 MB por solicitud. Las mutaciones requieren token CSRF; el login tiene un límite de 5 solicitudes por minuto, registro 5 por hora, compra 10 por minuto y consulta de asientos 60 por minuto. Redis permite compartir estos límites entre procesos de Gunicorn. Ajusta los límites al tráfico esperado y monitoriza errores `429`.

La dependencia `Flask-Limiter` aplica los límites y `Flask-WTF` valida CSRF. Para desarrollo local se usa almacenamiento en memoria; ese modo no comparte contadores entre procesos y no debe usarse en producción.
