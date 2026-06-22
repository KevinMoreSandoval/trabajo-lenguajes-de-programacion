from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Usuario, Rol



def signin(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'signin.html')
    
    if request.method == 'POST':
        email = request.POST.get('email') or request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
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

        # Asignar automáticamente el rol 'Cliente'
        rol = Rol.objects.filter(nombre='Cliente').first()

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
        
        # Iniciar sesión automáticamente tras el registro
        login(request, user)
        messages.success(request, f"¡Bienvenido {user.first_name}! Te has registrado correctamente.")
        return redirect('signin') # Redirige a la página principal (que es signin según tu urls.py)

def signout(request):
    logout(request)
    return redirect('signin')