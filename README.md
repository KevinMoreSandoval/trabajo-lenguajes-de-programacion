# ⚽ Sistema de Reservas de Canchas de Fútbol

Sistema web desarrollado en Django para la gestión de reservas de canchas de fútbol, con autenticación por roles, pagos, boletas y reportes.

---

## 📋 Stack Tecnológico

| Tecnología | Versión |
|-----------|---------|
| Python | 3.x |
| Django | 6.0.6 |
| MySQL | 8.x (Railway) |
| mysqlclient | 2.2.8 |
| dj-database-url | 3.1.2 |
| python-decouple | 3.8 |

---

## 🚀 Instalación y Configuración Local

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd djang-crud-auth
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Django
DEBUG=True
SECRET_KEY=tu-secret-key-segura-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos — URL de MySQL (Railway o local)
DATABASE_URL=mysql://usuario:contraseña@host:puerto/nombre_bd
```

> **Nota:** Para desarrollo local con MySQL nativo, la URL sería algo como:
> `DATABASE_URL=mysql://root:root@localhost:3306/reservas_canchas`

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

Esto creará todas las tablas **y sembrará automáticamente** un usuario Admin y un Recepcionista (migración `0010`).

### 6. Iniciar el servidor

```bash
python manage.py runserver
```

Accede a: **http://localhost:8000**

---

## 👥 Usuarios Iniciales

La migración `0010_seed_admin_recepcionista` crea automáticamente los siguientes usuarios:

| Rol | Email | Contraseña | Nombre | DNI | Teléfono |
|-----|-------|-----------|--------|-----|----------|
| **Admin** | admin@canchas.com | AdminSecure123! | Carlos Administrador | 12345678 | 987654321 |
| **Recepcionista** | recepcionista@canchas.com | RecepcionSecure123! | María Gómez López | 11223344 | 945678901 |

> ⚠️ **Cambiar estas contraseñas antes de usar en producción.**

### Crear usuarios adicionales de prueba (opcional)

```bash
python manage.py create_test_users
```

---

## 🔑 Roles y Permisos

### 🔐 Administrador
- ✅ Acceso completo al sistema
- ✅ Gestionar usuarios, canchas, reservas, pagos
- ✅ Ver logs de seguridad y generar reportes
- ✅ Acceso al panel de administración de Django

### 📞 Recepcionista
- ✅ Ver todas las reservas y canchas
- ✅ Registrar nuevas reservas y pagos
- ✅ Consultar horarios disponibles
- ❌ Eliminar datos
- ❌ Ver información de otros recepcionistas

### 👤 Cliente
- ✅ Ver sus propias reservas y pagos
- ✅ Hacer reservas de canchas
- ✅ Pagar reservas
- ❌ Ver datos de otros usuarios

---

## 🔒 Sistema de Seguridad

El proyecto implementa un sistema de seguridad multi-capa:

| Protección | Descripción |
|-----------|-------------|
| **SQL Injection** | Validación de patrones + Django ORM parametrizado |
| **XSS** | Escape automático en templates + middleware de sanitización |
| **CSRF** | Tokens en formularios + cookies `SameSite=Strict` |
| **Fuerza Bruta** | Rate limiting: 5 intentos / 5 min en login |
| **Contraseñas** | Mínimo 8 chars, mayúscula, minúscula, número, símbolo |
| **Headers** | CSP, X-Frame-Options, HSTS, Referrer-Policy |
| **Auditoría** | Logs rotativos en `logs/security.log` |
| **Sesiones** | HTTPOnly, expiran al cerrar navegador (1 hora max) |

### Archivos clave de seguridad

- `djangocrud/security.py` — Validadores (`SecurityValidator`)
- `djangocrud/middleware.py` — Middleware de headers, rate limit, sanitización
- `djangocrud/settings.py` — Configuración de seguridad

### Validadores disponibles

```python
from djangocrud.security import SecurityValidator

SecurityValidator.validate_email("user@example.com")
SecurityValidator.validate_password("MySecure123!Pass")
SecurityValidator.validate_dni("12345678")
SecurityValidator.validate_telefono("987654321")
SecurityValidator.validate_input_against_injection(user_input)
```

---

## 📁 Estructura del Proyecto

```
djang-crud-auth/
├── authentication/          # App de autenticación y usuarios
│   ├── models.py            # Modelos: Usuario, Rol, Admin, Cliente, Recepcionista
│   ├── views.py             # Vistas de login, signup, dashboard
│   ├── urls.py              # Rutas de autenticación
│   ├── management/commands/ # Comando create_test_users
│   └── migrations/          # Migraciones (incluye seed de usuarios)
├── canchas/                 # App de gestión de canchas
├── reservas/                # App de reservas
├── pagos/                   # App de pagos
├── boletas/                 # App de boletas
├── reportes/                # App de reportes
├── djangocrud/              # Configuración del proyecto
│   ├── settings.py          # Configuración principal
│   ├── urls.py              # Rutas raíz
│   ├── security.py          # Validadores de seguridad
│   ├── middleware.py        # Middleware de seguridad
│   └── wsgi.py
├── static/                  # Archivos estáticos (CSS, JS, imágenes)
├── logs/                    # Logs de Django y seguridad
├── manage.py
├── requirements.txt
├── .env                     # Variables de entorno (NO se sube al repo)
└── .gitignore
```

---

## ⚙️ Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|------------|---------|
| `DEBUG` | Modo debug | `True` / `False` |
| `SECRET_KEY` | Clave secreta de Django | `tu-clave-aleatoria` |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por coma) | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL de conexión a MySQL | `mysql://user:pass@host:port/db` |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF | `https://midominio.com` |

---

## 🚀 Deploy a Producción

### Checklist

- [ ] Cambiar `SECRET_KEY` a un valor aleatorio seguro
- [ ] Configurar `DEBUG=False`
- [ ] Configurar `ALLOWED_HOSTS` con el dominio real
- [ ] Configurar `CSRF_TRUSTED_ORIGINS` con la URL del frontend
- [ ] Habilitar `SECURE_SSL_REDIRECT = True`
- [ ] Habilitar `SESSION_COOKIE_SECURE = True` y `CSRF_COOKIE_SECURE = True`
- [ ] Ejecutar `python manage.py collectstatic`
- [ ] Usar Gunicorn como servidor WSGI
- [ ] Configurar reverse proxy (Nginx)
- [ ] Monitorear `logs/security.log`

### Generar SECRET_KEY segura

```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Ejecutar con Gunicorn

```bash
gunicorn djangocrud.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 🛠️ Comandos Útiles

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Crear usuarios de prueba
python manage.py create_test_users

# Recolectar archivos estáticos
python manage.py collectstatic --no-input

# Verificar configuración de seguridad
python manage.py check --deploy

# Ejecutar tests de seguridad
python manage.py test tests_seguridad -v 2

# Ver logs de seguridad
# Windows
Get-Content logs\security.log -Wait
# Linux
tail -f logs/security.log
```

---

## 📝 Licencia

Proyecto académico — Uso educativo.
