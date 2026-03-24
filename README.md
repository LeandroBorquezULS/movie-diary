# Movie Diary

Aplicación web para buscar películas, guardar vistas, recomendar o no recomendar títulos, y generar recomendaciones personalizadas por usuario.

Usa:
- `FastAPI` en el backend
- `PostgreSQL` como base de datos principal
- `TMDB` como fuente externa de películas
- frontend estático en `HTML + CSS + JavaScript`

## Requisitos

Programas necesarios:
- `Python 3.12` o compatible
- `PostgreSQL` instalado y en ejecución
- acceso a una API key de `TMDB`

Paquetes de Python usados:
- `fastapi`
- `uvicorn`
- `requests`
- `python-dotenv`
- `psycopg[binary]`

## Estructura

Carpetas principales:
- `backend/`
- `frontend/`

Organización del backend:
- `backend/core/`: configuración, seguridad, autenticación y rate limiting
- `backend/database/`: conexión PostgreSQL y repositorios
- `backend/models/`: esquemas Pydantic
- `backend/routes/`: endpoints HTTP
- `backend/services/`: TMDB y motor de recomendaciones

## Instalación

### 1. Clonar o abrir el proyecto

Ubícate en la carpeta raíz del proyecto:

```powershell
cd "C:\Users\PC\Desktop\movie diary"
```

### 2. Crear y activar entorno virtual

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

## Configuración de PostgreSQL

### 1. Crear la base de datos

Desde `psql`:

```sql
CREATE DATABASE movie_diary;
```

### 2. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con este contenido:

```env
TMDB_API_KEY=tu_api_key_de_tmdb
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/movie_diary
ENFORCE_STRONG_PASSWORDS=false
MAX_LOGIN_ATTEMPTS=10
LOCKOUT_MINUTES=15
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_MAX_REQUESTS=120
AUTH_RATE_LIMIT_MAX_REQUESTS=20
```

Notas:
- `DATABASE_URL` debe apuntar a tu instancia local de PostgreSQL.
- `ENFORCE_STRONG_PASSWORDS=false` deja desactivada la política estricta de contraseñas para pruebas.
- `MAX_LOGIN_ATTEMPTS=10` bloquea temporalmente la cuenta si se exceden los intentos.

## Cómo ejecutar

### Backend

Levanta la API:

```powershell
uvicorn backend.main:app --reload
```

Si todo está bien, la API debería quedar disponible en:

```text
http://127.0.0.1:8000
```

### Frontend

El frontend es estático. Puedes abrir `frontend/index.html` directamente, pero es preferible servirlo con un servidor local para evitar problemas de navegador.

Opción simple con Python:

```powershell
cd frontend
python -m http.server 5500
```

Luego abre:

```text
http://127.0.0.1:5500
```

## Uso de la aplicación

Flujo general:
- crear cuenta o iniciar sesión
- buscar películas
- abrir una película para ver su detalle
- marcarla como vista
- recomendarla o no recomendarla
- revisar recomendaciones personalizadas
- revisar historial de vistas en la pestaña de usuario
- cambiar usuario, contraseña o gustos desde configuración

## Cómo funcionan las recomendaciones

La app combina varias señales:
- películas vistas recientemente
- géneros favoritos del usuario
- recomendaciones relacionadas desde TMDB
- votos locales de la comunidad
- cantidad de usuarios que han visto una película

El ranking final se hace localmente en el backend y no se delega por completo a TMDB.

El algoritmo está documentado en:
- `backend/services/recommendation_engine.py`

Características del ranking:
- usa una puntuación compuesta
- prioriza señales personales y comunitarias
- se ordena con `merge sort`
- `merge sort` fue elegido por ser estable y tener costo `O(n log n)`

## Seguridad actual

El proyecto actualmente incluye:
- hash de contraseñas con `PBKDF2-HMAC-SHA256`
- salt aleatoria por contraseña
- sesiones con token
- hash del token de sesión en base de datos
- consultas SQL parametrizadas
- rate limiting básico
- bloqueo temporal tras múltiples intentos fallidos
- validación de entrada con Pydantic

Importante:
- la política fuerte de contraseñas existe, pero se puede activar o desactivar con `ENFORCE_STRONG_PASSWORDS`
- por ahora `CORS` está abierto para desarrollo

## Base de datos

La base usa dos esquemas lógicos dentro de PostgreSQL:
- `accounts`: usuarios, sesiones y géneros favoritos
- `catalog`: caché de películas, búsquedas, vistas y feedback

Esto permite separar datos de cuentas y catálogo sin complicar joins ni transacciones.

## Dependencia externa: TMDB

La app usa TMDB para:
- buscar películas
- obtener detalle de películas
- obtener recomendaciones relacionadas
- obtener géneros

Para reducir llamadas repetidas, la aplicación guarda caché local en PostgreSQL.

## Solución de problemas

### Error: `DATABASE_URL no está configurada`

Revisa que exista el archivo `.env` y que contenga:

```env
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/movie_diary
```

### Error de conexión a PostgreSQL

Verifica:
- que PostgreSQL esté encendido
- que el usuario y contraseña sean correctos
- que la base `movie_diary` exista
- que el puerto `5432` sea el correcto

### Error con TMDB

Verifica:
- que `TMDB_API_KEY` sea válida
- que tengas conexión a internet

### El frontend abre pero no carga datos

Verifica:
- que el backend esté corriendo en `http://127.0.0.1:8000`
- que abras el frontend desde un servidor local si el navegador bloquea peticiones

## Comandos útiles

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Ejecutar backend:

```powershell
uvicorn backend.main:app --reload
```

Servir frontend:

```powershell
cd frontend
python -m http.server 5500
```

## Estado del proyecto

El proyecto está pensado como base funcional para seguir iterando. Ya incluye:
- multiusuario
- historial tipo diario
- caché local de películas
- recomendaciones personalizadas
- métricas comunitarias
- autenticación por sesión

Todavía se puede mejorar más en:
- despliegue productivo
- endurecimiento de seguridad
- tests automatizados
- panel administrativo
- migraciones formales de base de datos
