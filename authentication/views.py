from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import logging
import unicodedata

from .models import Usuario, Rol
from djangocrud.security import SecurityValidator, rate_limiter

# Logger de seguridad
security_logger = logging.getLogger("app.security")


@require_http_methods(["GET", "POST"])
@csrf_protect
def signin(request):
    """
    Vista de autenticación segura
    - Protección CSRF
    - Rate limiting
    - Validación de entrada
    - Logging de intentos
    """
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "signin.html")

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()

            # Validar que no estén vacíos
            if not email or not password:
                messages.error(request, "Email y contraseña son obligatorios.")
                security_logger.warning(
                    f"Login attempt with missing fields from {request.META.get('REMOTE_ADDR')}"
                )
                return render(request, "signin.html")

            # Validar email formato
            try:
                email = SecurityValidator.validate_email(email)
            except ValidationError as e:
                messages.error(request, f"Email inválido: {str(e)}")
                security_logger.warning(f"Invalid email format: {email[:50]}")
                return render(request, "signin.html")

            # Validar contraseña no esté vacía (no se valida el formato aquí, solo autenticación)
            if len(password) < 1 or len(password) > 500:
                messages.error(request, "Contraseña inválida.")
                return render(request, "signin.html")

            # Validar contra inyección SQL
            if not SecurityValidator.validate_input_against_injection(
                email
            ) or not SecurityValidator.validate_input_against_injection(password):
                security_logger.critical(
                    f"SQL Injection attempt in signin from {request.META.get('REMOTE_ADDR')}"
                )
                messages.error(request, "Entrada inválida detectada.")
                return JsonResponse({"error": "Entrada inválida"}, status=400)

            # Autenticar usuario
            user = authenticate(request, username=email, password=password)

            if user is not None and user.activo:
                # Usuario válido y activo
                login(request, user)
                if request.POST.get("remember"):
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                security_logger.info(f"Successful login for user: {email}")
                messages.success(request, f"¡Bienvenido {user.get_full_name()}!")
                return redirect("dashboard")
            else:
                # Login fallido
                security_logger.warning(
                    f"Failed login attempt for: {email} from {request.META.get('REMOTE_ADDR')}"
                )
                messages.error(request, "Email o contraseña inválidos.")
                return render(request, "signin.html")

        except Exception as e:
            security_logger.error(f"Unexpected error in signin: {str(e)}")
            messages.error(request, "Ocurrió un error. Intente más tarde.")
            return render(request, "signin.html")


@require_http_methods(["GET", "POST"])
@csrf_protect
def signup(request):
    """
    Vista de registro segura
    - Protección CSRF
    - Validación de entrada
    - Sanitización de datos
    - Protección contra inyección SQL
    - Verificación de contraseñas fuertes
    """
    if request.method == "GET":
        return render(request, "signup.html")

    if request.method == "POST":
        try:
            # Obtener y limpiar datos
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()
            confirm_password = request.POST.get("confirm_password", "").strip()
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            dni = request.POST.get("dni", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            fecha_nacimiento = request.POST.get("fecha_nacimiento", "").strip()
            username = request.POST.get("username", "").strip()

            # ========== VALIDACIONES DE SEGURIDAD ==========

            # Validar email
            try:
                email = SecurityValidator.validate_email(email)
            except ValidationError as e:
                messages.error(request, f"Email inválido: {str(e)}")
                return render(request, "signup.html")

            # Validar contraseña fuerte
            try:
                SecurityValidator.validate_password(password)
            except ValidationError as e:
                messages.error(request, f"Contraseña débil: {str(e)}")
                return render(request, "signup.html")

            # Validar que las contraseñas coincidan
            if password != confirm_password:
                messages.error(request, "Las contraseñas no coinciden.")
                security_logger.warning(f"Password mismatch for email: {email}")
                return render(request, "signup.html")

            # Validar DNI
            try:
                dni = SecurityValidator.validate_dni(dni)
            except ValidationError as e:
                messages.error(request, f"DNI inválido: {str(e)}")
                return render(request, "signup.html")

            # Validar Teléfono
            try:
                telefono = SecurityValidator.validate_telefono(telefono)
            except ValidationError as e:
                messages.error(request, f"Teléfono inválido: {str(e)}")
                return render(request, "signup.html")

            # Validar nombres
            try:
                first_name = SecurityValidator.validate_text(first_name, max_length=100)
                last_name = SecurityValidator.validate_text(last_name, max_length=100)
                username = SecurityValidator.validate_text(username, max_length=150)
            except ValidationError as e:
                messages.error(request, f"Datos inválidos: {str(e)}")
                return render(request, "signup.html")

            # Validar contra inyección SQL
            for field in [
                email,
                password,
                first_name,
                last_name,
                dni,
                telefono,
                username,
            ]:
                if not SecurityValidator.validate_input_against_injection(field):
                    security_logger.critical(
                        f"SQL Injection attempt in signup from {request.META.get('REMOTE_ADDR')}"
                    )
                    messages.error(request, "Entrada inválida detectada.")
                    return JsonResponse({"error": "Entrada inválida"}, status=400)

            # ========== VERIFICACIONES DE DISPONIBILIDAD ==========

            # Verificar si el email ya existe
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, "El correo electrónico ya está registrado.")
                security_logger.info(f"Signup attempt with existing email: {email}")
                return render(request, "signup.html")

            # Verificar si el DNI ya existe
            if Usuario.objects.filter(dni=dni).exists():
                messages.error(request, "Este DNI ya se encuentra registrado.")
                security_logger.info(f"Signup attempt with existing DNI: {dni}")
                return render(request, "signup.html")

            # Verificar si el username ya existe
            if Usuario.objects.filter(username=username).exists():
                messages.error(request, "Este nombre de usuario ya está registrado.")
                return render(request, "signup.html")

            # ========== CREACIÓN DE USUARIO ==========

            # Asignar automáticamente el rol 'Cliente'
            rol = Rol.objects.filter(nombre="Cliente").first()
            if not rol:
                # Crear rol si no existe
                rol = Rol.objects.create(nombre="Cliente")

            # Crear usuario con contraseña hasheada
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
                telefono=telefono,
                rol=rol,
                activo=True,
            )

            # Registrar en log de seguridad
            security_logger.info(f"New user registered: {email}")

            # Iniciar sesión automáticamente
            login(request, user)
            messages.success(
                request,
                f"¡Bienvenido {user.get_full_name()}! Te has registrado correctamente.",
            )
            return redirect("dashboard")

        except ValidationError as e:
            messages.error(request, f"Error de validación: {str(e)}")
            return render(request, "signup.html")
        except Exception as e:
            security_logger.error(f"Unexpected error in signup: {str(e)}")
            messages.error(
                request, "Ocurrió un error durante el registro. Intente más tarde."
            )
            return render(request, "signup.html")


@require_http_methods(["POST"])
def signout(request):
    """
    Vista de cierre de sesión segura
    """
    user = request.user
    logout(request)
    security_logger.info(
        f"User logged out: {user.email if user.is_authenticated else 'Unknown'}"
    )
    messages.success(request, "Ha cerrado sesión correctamente.")
    return redirect("signin")


@require_http_methods(["GET"])
def dashboard(request, section="inicio"):
    """
    Dashboard con control de acceso
    """
    if not request.user.is_authenticated:
        return redirect("signin")

    # Importaciones dinámicas para evitar dependencias circulares
    from canchas.models import Cancha, Regla, Horario
    from reservas.models import Reserva, Notificacion
    from pagos.models import Pago, MetodoPago

    try:
        # Verificar que el usuario está activo
        if not request.user.activo:
            logout(request)
            messages.error(request, "Tu cuenta ha sido desactivada.")
            return redirect("signin")

        rol_usuario = request.user.rol.nombre if request.user.rol else "Cliente"
        _sync_reservation_reminders(request.user)

        # Contadores y listados generales
        canchas_count = Cancha.objects.count()
        reglas_count = Regla.objects.count()

        # Distinguir acceso por rol
        if rol_usuario in ("Admin", "Administrador", "Recepcionista"):
            # Admin tiene acceso a todos los datos
            reservas_count = Reserva.objects.count()
            pagos_count = Pago.objects.count()
            usuarios_count = Usuario.objects.filter(rol__nombre="Cliente").count()

            recent_canchas = Cancha.objects.select_related("estado").all()
            if rol_usuario == "Recepcionista":
                recent_canchas = recent_canchas.exclude(estado__nombre="Inactiva")
            recent_reservas = (
                Reserva.objects.select_related("cancha", "cliente", "estado")
                .all()
                .order_by("-fecha", "-hora_inicio")
            )
            recent_pagos = (
                Pago.objects.select_related("reserva", "metodo_pago", "estado_pago")
                .all()
                .order_by("-fecha_pago")[:10]
            )
            if rol_usuario in ("Admin", "Administrador"):
                recent_usuarios = (
                    Usuario.objects.select_related("rol")
                    .all()
                    .order_by("first_name", "last_name")
                )
            else:
                recent_usuarios = (
                    Usuario.objects.select_related("rol")
                    .filter(rol__nombre="Cliente")
                    .order_by("first_name", "last_name")
                )
        else:
            # Clientes solo ven sus propios datos
            reservas_count = Reserva.objects.filter(cliente=request.user).count()
            pagos_count = Pago.objects.filter(reserva__cliente=request.user).count()
            usuarios_count = 0

            recent_canchas = Cancha.objects.select_related("estado").exclude(
                estado__nombre="Inactiva"
            )
            recent_reservas = (
                Reserva.objects.select_related("cancha", "cliente", "estado")
                .filter(cliente=request.user)
                .order_by("-fecha", "-hora_inicio")
            )
            recent_pagos = (
                Pago.objects.select_related("reserva", "metodo_pago", "estado_pago")
                .filter(reserva__cliente=request.user)
                .order_by("-fecha_pago")
            )
            recent_usuarios = []

        for reserva in recent_reservas:
            reserva.saldo_pendiente = reserva.monto_total - reserva.monto_pagado

        cart = (
            request.session.get("reservation_cart", [])
            if rol_usuario == "Cliente"
            else []
        )
        cart_total = sum((Decimal(item["monto"]) for item in cart), Decimal("0.00"))
        time_slots = []
        slot = datetime.combine(
            timezone.localdate(), datetime.strptime("08:00", "%H:%M").time()
        )
        slot_end = datetime.combine(
            timezone.localdate(), datetime.strptime("23:30", "%H:%M").time()
        )
        while slot <= slot_end:
            hour_12 = slot.hour % 12 or 12
            period = "a. m." if slot.hour < 12 else "p. m."
            time_slots.append(
                (slot.strftime("%H:%M"), f"{hour_12}:{slot.minute:02d} {period}")
            )
            slot += timedelta(minutes=30)

        context = {
            "rol_usuario": rol_usuario,
            "canchas_count": canchas_count,
            "reglas_count": reglas_count,
            "reservas_count": reservas_count,
            "pagos_count": pagos_count,
            "usuarios_count": usuarios_count,
            "recent_canchas": recent_canchas,
            "recent_reservas": recent_reservas,
            "recent_pagos": recent_pagos,
            "recent_usuarios": recent_usuarios,
            "metodos_pago": MetodoPago.objects.filter(activo=True),
            "hoy": timezone.localdate(),
            "cart_items": cart,
            "cart_count": len(cart),
            "cart_total": cart_total,
            "time_slots": time_slots,
            "notifications": Notificacion.objects.filter(
                usuario=request.user
            ).select_related("tipo", "reserva")[:8],
            "unread_notifications": Notificacion.objects.filter(
                usuario=request.user, leida=False
            ).count(),
            "horarios": (
                Horario.objects.select_related("cancha").all()
                if rol_usuario in ("Admin", "Administrador")
                else []
            ),
            "report_total_income": Pago.objects.aggregate(total=Sum("monto"))["total"]
            or Decimal("0.00"),
            "report_reservations_by_status": (
                Reserva.objects.values("estado__nombre")
                .annotate(total=Count("id"))
                .order_by("estado__nombre")
                if rol_usuario in ("Admin", "Administrador")
                else []
            ),
        }

        security_logger.info(f"Dashboard accessed by: {request.user.email}")
        if rol_usuario in ("Admin", "Administrador", "Recepcionista"):
            allowed_sections = {
                "inicio",
                "reservas",
                "clientes",
                "canchas",
                "horarios",
                "administracion",
            }
            section = section if section in allowed_sections else "inicio"
            if rol_usuario == "Recepcionista" and section == "administracion":
                section = "inicio"
            context["active_section"] = section
            return render(request, f"staff/{section}.html", context)
        return render(request, "dashboard.html", context)

    except Exception as e:
        security_logger.error(
            f"Error in dashboard for user {request.user.email}: {str(e)}"
        )
        messages.error(request, "Ocurrió un error al cargar el dashboard.")
        return redirect("signin")


def _role_name(user):
    return user.rol.nombre if user.rol else "Cliente"


def _reservation_redirect(request):
    """Mantiene al personal en la vista independiente de reservas."""
    if _is_staff_role(request.user):
        return redirect("staff_page", section="reservas")
    return redirect("dashboard")


def _is_staff_role(user):
    return _role_name(user) in ("Admin", "Administrador", "Recepcionista")


def _is_admin_role(user):
    return _role_name(user) in ("Admin", "Administrador")


def _notify(user, reserva, message, subject="Actualización de reserva"):
    from reservas.models import Notificacion, TipoNotificacion

    notification_type, _ = TipoNotificacion.objects.get_or_create(nombre="Sistema")
    return Notificacion.objects.create(
        reserva=reserva,
        usuario=user,
        tipo=notification_type,
        asunto=subject,
        mensaje=message,
    )


def _sync_reservation_reminders(user):
    """Mantiene recordatorios únicamente mientras la reserva pagada está vigente."""
    from reservas.models import Reserva, Notificacion, TipoNotificacion

    reminder_type, _ = TipoNotificacion.objects.get_or_create(
        nombre="Recordatorio de cancha"
    )
    now = timezone.localtime()
    reminders = Notificacion.objects.filter(
        usuario=user, tipo=reminder_type
    ).select_related("reserva")

    for reminder in reminders:
        end_at = timezone.make_aware(
            datetime.combine(reminder.reserva.fecha, reminder.reserva.hora_fin)
        )
        if end_at <= now or reminder.reserva.estado.nombre.lower() == "cancelada":
            reminder.delete()

    reservations = (
        Reserva.objects.select_related("cancha", "estado")
        .filter(
            cliente=user,
            fecha__gte=now.date(),
        )
        .exclude(estado__nombre__iexact="Cancelada")
    )
    for reservation in reservations:
        if reservation.monto_pagado < reservation.monto_total:
            continue
        end_at = timezone.make_aware(
            datetime.combine(reservation.fecha, reservation.hora_fin)
        )
        if end_at <= now:
            continue
        if reservation.fecha == now.date():
            when = f'Hoy a las {reservation.hora_inicio.strftime("%H:%M")}'
        elif reservation.fecha == now.date() + timedelta(days=1):
            when = f'Mañana a las {reservation.hora_inicio.strftime("%H:%M")}'
        else:
            when = f'{reservation.fecha.strftime("%d/%m/%Y")} a las {reservation.hora_inicio.strftime("%H:%M")}'
        message = (
            f"{when} tienes {reservation.cancha.nombre}, "
            f'de {reservation.hora_inicio.strftime("%H:%M")} a {reservation.hora_fin.strftime("%H:%M")}.'
        )
        reminder, created = Notificacion.objects.get_or_create(
            usuario=user,
            reserva=reservation,
            tipo=reminder_type,
            defaults={"asunto": "Tu cancha está reservada", "mensaje": message},
        )
        if not created and (
            reminder.mensaje != message or reminder.asunto != "Tu cancha está reservada"
        ):
            reminder.mensaje = message
            reminder.asunto = "Tu cancha está reservada"
            reminder.save(update_fields=["mensaje", "asunto"])


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def mark_notifications_read(request):
    from reservas.models import Notificacion

    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect("dashboard")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def toggle_user(request, user_id):
    if not _is_admin_role(request.user):
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect("dashboard")
    user = Usuario.objects.filter(pk=user_id).exclude(pk=request.user.pk).first()
    if not user:
        messages.error(request, "Usuario no encontrado o no modificable.")
    else:
        user.activo = not user.activo
        user.is_active = user.activo
        user.save(update_fields=["activo", "is_active"])
        messages.success(
            request, f'Usuario {"activado" if user.activo else "desactivado"}.'
        )
    return redirect("staff_page", section="administracion")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def create_managed_user(request):
    from .models import Cliente, Recepcionista

    if not _is_admin_role(request.user):
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect("dashboard")
    role_name = request.POST.get("rol")
    if role_name not in ("Cliente", "Recepcionista"):
        messages.error(request, "Selecciona un rol permitido.")
        return redirect("staff_page", section="administracion")
    try:
        email = request.POST["email"].strip().lower()
        dni = request.POST["dni"].strip()
        telefono = request.POST.get("telefono", "").strip() or None
        if (
            Usuario.objects.filter(email=email).exists()
            or Usuario.objects.filter(dni=dni).exists()
        ):
            raise ValidationError("El correo o DNI ya está registrado.")
        if len(request.POST.get("password", "")) < 8:
            raise ValidationError(
                "La contraseña temporal debe tener al menos 8 caracteres."
            )
        rol, _ = Rol.objects.get_or_create(nombre=role_name)
        username_base = email.split("@")[0][:120] or "usuario"
        username, suffix = username_base, 1
        while Usuario.objects.filter(username=username).exists():
            suffix += 1
            username = f"{username_base}{suffix}"
        user = Usuario(
            username=username,
            email=email,
            first_name=request.POST["first_name"].strip(),
            last_name=request.POST["last_name"].strip(),
            dni=dni,
            telefono=telefono,
            rol=rol,
            activo=True,
            is_active=True,
        )
        user.set_password(request.POST["password"])
        user.full_clean()
        user.save()
        (
            Recepcionista if role_name == "Recepcionista" else Cliente
        ).objects.get_or_create(usuario=user)
        messages.success(request, f"{role_name} creado correctamente.")
    except (KeyError, ValidationError) as exc:
        message = (
            exc.messages[0]
            if isinstance(exc, ValidationError) and exc.messages
            else "Completa correctamente los datos."
        )
        messages.error(request, message)
    return redirect("staff_page", section="administracion")


@login_required(login_url="signin")
@require_http_methods(["POST"])
@csrf_protect
def delete_managed_user(request, user_id):
    from django.db.models.deletion import ProtectedError

    if not _is_admin_role(request.user):
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect("dashboard")
    user = Usuario.objects.filter(pk=user_id).exclude(pk=request.user.pk).first()
    if not user:
        messages.error(request, "El usuario no existe o no puede eliminarse.")
    else:
        try:
            label = user.get_full_name() or user.email
            user.delete()
            messages.success(request, f"Usuario {label} eliminado.")
        except ProtectedError:
            messages.error(
                request,
                "Este usuario tiene reservas históricas. Desactívalo para conservar los registros.",
            )
    return redirect("staff_page", section="administracion")
