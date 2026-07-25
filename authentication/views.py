import logging

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Count, Q

from .forms import ClienteRecepcionForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Usuario, Rol

logger = logging.getLogger(__name__)


def redirect_por_rol(user):
    if getattr(user, 'es_cliente', False):
        return redirect('canchas:lista')
    return redirect('dashboard')


def admin_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_admin', False):
            messages.error(request, 'Solo el administrador puede realizar esta accion.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def operador_required(view_func):
    @login_required(login_url='signin')
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'es_operador', False):
            messages.error(request, 'Solo administradores o recepcionistas pueden realizar esta accion.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def signin(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect_por_rol(request.user)
        return render(request, 'signin.html')
    
    if request.method == 'POST':
        email = request.POST.get('email') or request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect_por_rol(user)
        else:
            messages.error(request, "Credenciales inválidas")
            return render(request, 'signin.html')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('signin')
    
    # Importaciones dinámicas para evitar dependencias circulares
    from canchas.models import Cancha, Regla
    from reservas.models import Reserva
    from pagos.models import Pago

    rol_usuario = request.user.rol.nombre if request.user.rol else 'Cliente'
    
    # Contadores y listados generales
    canchas_count = Cancha.objects.count()
    reglas_count = Regla.objects.count()
    
    if rol_usuario == 'Admin':
        reservas_count = Reserva.objects.count()
        pagos_count = Pago.objects.count()
        usuarios_count = Usuario.objects.count()
        
        recent_canchas = Cancha.objects.all().order_by('-id')[:5]
        recent_reservas = Reserva.objects.select_related('cancha', 'cliente', 'estado').all().order_by('-fecha_creacion')[:5]
        recent_pagos = Pago.objects.select_related('reserva', 'metodo_pago', 'estado_pago').all().order_by('-fecha_pago')[:5]
        recent_usuarios = Usuario.objects.select_related('rol').all().order_by('-fecha_creacion')[:5]
    else:
        reservas_count = Reserva.objects.filter(cliente=request.user).count()
        pagos_count = Pago.objects.filter(reserva__cliente=request.user).count()
        usuarios_count = 0
        
        recent_canchas = Cancha.objects.all().order_by('-id')[:5]
        recent_reservas = Reserva.objects.select_related('cancha', 'cliente', 'estado').filter(cliente=request.user).order_by('-fecha_creacion')[:5]
        recent_pagos = Pago.objects.select_related('reserva', 'metodo_pago', 'estado_pago').filter(reserva__cliente=request.user).order_by('-fecha_pago')[:5]
        recent_usuarios = []
        
    context = {
        'rol_usuario': rol_usuario,
        'canchas_count': canchas_count,
        'reglas_count': reglas_count,
        'reservas_count': reservas_count,
        'pagos_count': pagos_count,
        'usuarios_count': usuarios_count,
        'recent_canchas': recent_canchas,
        'recent_reservas': recent_reservas,
        'recent_pagos': recent_pagos,
        'recent_usuarios': recent_usuarios,
    }
    
    return render(request, 'dashboard.html', context)

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    #Apartado de registro de usuario
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dni = request.POST.get('dni')

        # Verificar que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('signup')

        # Validación de longitud y formato de DNI
        if not dni or len(dni) != 8 or not dni.isdigit():
            messages.error(request, "El DNI debe tener exactamente 8 números.")
            return redirect('signup')

        telefono = request.POST.get('telefono')
        # Validación de longitud y formato de Teléfono
        if not telefono or len(telefono) != 9 or not telefono.isdigit():
            messages.error(request, "El número de teléfono debe tener exactamente 9 dígitos numéricos.")
            return redirect('signup')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        username = request.POST.get('username')


        # Verificar si el correo ya existe
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está registrado.")
            return redirect('signup')

        # Verificar si el DNI ya existe para evitar errores de base de datos
        if Usuario.objects.filter(dni=dni).exists():
            messages.error(request, "Este DNI ya se encuentra registrado.")
            return redirect('signup')

        # Asignar automaticamente el rol Cliente
        rol, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)

        try:
            with transaction.atomic():
                # Crear el usuario usando create_user para que la contraseña se guarde con hash
                user = Usuario.objects.create_user(
                    username=username, # Usamos el email como username interno
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    dni=dni,
                    fecha_nacimiento=fecha_nacimiento,
                    telefono=telefono,
                    rol=rol
                )
        except IntegrityError:
            logger.exception('Datos duplicados al registrar usuario con email %s', email)
            messages.error(request, 'No se pudo registrar: correo, usuario o DNI ya existe.')
            return redirect('signup')
        except DatabaseError:
            logger.exception('Error registrando usuario con email %s', email)
            messages.error(request, 'No se pudo completar el registro. Intentalo nuevamente.')
            return redirect('signup')
        
        # Iniciar sesión automáticamente tras el registro
        login(request, user)
        messages.success(request, f"¡Bienvenido {user.first_name}! Te has registrado correctamente.")
        return redirect_por_rol(user)

def signout(request):
    logout(request)
    return redirect('signin')


@admin_required
def lista_usuarios(request):
    query = request.GET.get('q', '').strip()
    rol = request.GET.get('rol', '').strip()
    try:
        usuarios = Usuario.objects.select_related('rol').order_by('first_name', 'last_name', 'email')
        if query:
            usuarios = usuarios.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(dni__icontains=query)
                | Q(telefono__icontains=query)
            )
        if rol:
            usuarios = usuarios.filter(rol_id=rol)

        roles = Rol.objects.filter(nombre__in=Rol.ROLES_VALIDOS).order_by('nombre')
    except DatabaseError:
        logger.exception('Error listando usuarios')
        messages.error(request, 'No se pudieron cargar los usuarios.')
        usuarios = roles = []
    return render(
        request,
        'usuarios/lista.html',
        {'usuarios': usuarios, 'roles': roles, 'query': query, 'rol_actual': rol},
    )


@admin_required
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, 'Usuario creado correctamente.')
                return redirect('usuarios:lista')
            except IntegrityError:
                logger.exception('Datos duplicados creando usuario')
                messages.error(request, 'No se pudo crear: correo, usuario o DNI ya existe.')
            except DatabaseError:
                logger.exception('Error creando usuario')
                messages.error(request, 'No se pudo crear el usuario.')
    else:
        cliente, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)
        form = UsuarioCreateForm(initial={'rol': cliente, 'activo': True})

    return render(
        request,
        'usuarios/form.html',
        {'form': form, 'titulo': 'Crear usuario', 'accion': 'Crear'},
    )


@admin_required
def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario.objects.select_related('rol'), pk=user_id)

    if request.method == 'POST':
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, 'Usuario actualizado correctamente.')
                return redirect('usuarios:lista')
            except IntegrityError:
                logger.exception('Datos duplicados editando usuario %s', user_id)
                messages.error(request, 'No se pudo actualizar: correo, usuario o DNI ya existe.')
            except DatabaseError:
                logger.exception('Error editando usuario %s', user_id)
                messages.error(request, 'No se pudo actualizar el usuario.')
    else:
        form = UsuarioUpdateForm(instance=usuario)

    return render(
        request,
        'usuarios/form.html',
        {'form': form, 'titulo': 'Editar usuario', 'accion': 'Guardar'},
    )


@admin_required
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, pk=user_id)
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta desde aqui.')
        return redirect('usuarios:lista')

    if request.method == 'POST':
        try:
            usuario.delete()
            messages.success(request, 'Usuario eliminado correctamente.')
            return redirect('usuarios:lista')
        except DatabaseError:
            logger.exception('Error eliminando usuario %s', user_id)
            messages.error(request, 'No se pudo eliminar el usuario porque puede tener datos asociados.')

    return render(request, 'usuarios/confirm_delete.html', {'usuario': usuario})


@operador_required
def lista_clientes(request):
    query = request.GET.get('q', '').strip()
    try:
        clientes = (
            Usuario.objects
            .select_related('rol')
            .filter(rol__nombre=Rol.CLIENTE)
            .annotate(reservas_total=Count('reserva'))
            .order_by('first_name', 'last_name', 'email')
        )
        if query:
            clientes = clientes.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(dni__icontains=query)
                | Q(telefono__icontains=query)
            )
    except DatabaseError:
        logger.exception('Error listando clientes')
        messages.error(request, 'No se pudieron cargar los clientes.')
        clientes = []

    return render(
        request,
        'clientes/lista.html',
        {'clientes': clientes, 'query': query},
    )


@operador_required
def crear_cliente(request):
    initial = {}
    dni = request.GET.get('dni')
    if dni:
        initial['dni'] = dni

    if request.method == 'POST':
        form = ClienteRecepcionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cliente = form.save()
                messages.success(request, 'Cliente registrado correctamente.')
                next_url = request.POST.get('next')
                if next_url == 'reserva':
                    return redirect(f"{reverse('reservas:recepcion_crear')}?cliente={cliente.id}")
                return redirect('usuarios:clientes')
            except IntegrityError:
                logger.exception('Datos duplicados registrando cliente')
                messages.error(request, 'No se pudo registrar: correo o DNI ya existe.')
            except DatabaseError:
                logger.exception('Error registrando cliente')
                messages.error(request, 'No se pudo registrar el cliente.')
    else:
        form = ClienteRecepcionForm(initial=initial)

    return render(request, 'clientes/form.html', {'form': form})
