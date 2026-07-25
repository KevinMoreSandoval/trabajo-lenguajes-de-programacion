# ⚽ Sistema de Reservas de Canchas de Fútbol

Sistema web para la gestión de reservas de canchas de fútbol desarrollado con **Django 6.0** y **MySQL**.

## 📋 Características

- **Autenticación** — Registro, login y gestión de usuarios con roles (Admin, Recepcionista, Cliente)
- **Gestión de Canchas** — CRUD completo de canchas con estados, reglas y horarios bloqueados
- **Reservas** — Sistema de reservas con estados, agrupación y control de horarios
- **Pagos** — Registro de pagos con múltiples métodos de pago y estados
- **Dashboard** — Panel con KPIs, ingresos, ocupación y estadísticas de reservas

## 🏗️ Estructura del Proyecto

```
├── authentication/     # Usuarios, roles, login/registro
├── canchas/            # CRUD de canchas, estados, reglas
├── reservas/           # Gestión de reservas y grupos
├── pagos/              # Registro y control de pagos
├── services/           # Lógica de negocio (analytics)
├── djangocrud/         # Configuración principal del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── .env.example        # Plantilla de variables de entorno
└── .gitignore
```

## 🗄️ Modelo de Base de Datos

```
usuarios ──────┐
roles ─────────┤
               │
canchas ───────┼── reservas ──── pagos
estados_canchas┤   estados_reservas
reglas ────────┤   reservas_grupos
horarios_bloqueados
               │
               ├── metodos_pago
               ├── tipos_metodos_pago
               └── estados_pagos
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python** 3.12+
- **MySQL** 8.0+ (local o en la nube)
- **pip** (gestor de paquetes de Python)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

### 2. Crear y activar el entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

> **Nota sobre `mysqlclient`:** En Linux puede requerir dependencias del sistema:
> ```bash
> # Ubuntu/Debian
> sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
>
> # macOS
> brew install mysql pkg-config
> ```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo con tus valores:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Django
DEBUG=True
SECRET_KEY=tu-secret-key-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
# Opción A - MySQL local:
DATABASE_URL=mysql://root:tu_password@localhost:3306/reservas_canchas

# Opción B - MySQL en Railway (u otro servicio en la nube):
# DATABASE_URL=mysql://user:password@host:port/database
```

> **💡 Generar una SECRET_KEY segura:**
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 5. Crear la base de datos (solo si usas MySQL local)

```sql
CREATE DATABASE reservas_canchas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> Si usas Railway u otro servicio en la nube, la base de datos ya está creada. Solo necesitas la `DATABASE_URL`.

### 6. Ejecutar migraciones

```bash
python manage.py migrate
```

### 7. Crear un superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar el servidor

```bash
python manage.py runserver
```

Accede a la aplicación en: **http://127.0.0.1:8000/**

Panel de administración: **http://127.0.0.1:8000/admin/**

## 🔧 Variables de Entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DEBUG` | Modo debug (nunca `True` en producción) | `True` |
| `SECRET_KEY` | Clave secreta de Django | `django-insecure-abc123...` |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por coma | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL de conexión a MySQL | `mysql://user:pass@host:port/db` |

## 👥 Roles del Sistema

| Rol | Permisos |
|---|---|
| **Admin** | Acceso total: usuarios, canchas, reservas, pagos, dashboard |
| **Recepcionista** | Gestión de canchas, reservas y pagos |
| **Cliente** | Realizar y ver sus propias reservas |

## 🛠️ Tecnologías

- **Backend:** Django 6.0.6
- **Base de datos:** MySQL 8.0+
- **Driver:** mysqlclient 2.2.8
- **Configuración:** python-decouple + dj-database-url

## 📝 Notas

- El proyecto usa `email` como campo de autenticación principal (no `username`)
- La zona horaria está configurada como `America/Lima`
- El idioma por defecto es `es-es` (español)
