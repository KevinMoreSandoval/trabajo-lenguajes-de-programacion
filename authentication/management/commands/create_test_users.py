"""
Management command para crear usuarios de prueba
Crea 3 usuarios: Admin, Cliente, Recepcionista
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Rol, Cliente, Admin, Recepcionista
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = "Crea 3 usuarios de prueba con roles diferentes"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("🚀 CREANDO USUARIOS DE PRUEBA"))
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))

        # Crear roles si no existen
        self.stdout.write("📋 Verificando roles...")
        roles = {
            "Admin": Rol.objects.get_or_create(nombre="Admin")[0],
            "Cliente": Rol.objects.get_or_create(nombre="Cliente")[0],
            "Recepcionista": Rol.objects.get_or_create(nombre="Recepcionista")[0],
        }
        self.stdout.write(self.style.SUCCESS("✅ Roles verificados\n"))

        # Datos de los usuarios de prueba
        usuarios = [
            {
                "tipo": "Admin",
                "username": "admin_demo",
                "email": "admin@example.com",
                "password": "AdminSecure123!",
                "first_name": "Carlos",
                "last_name": "Administrador",
                "dni": "12345678",
                "telefono": "987654321",
                "rol": roles["Admin"],
                "crear_profile": True,
            },
            {
                "tipo": "Cliente",
                "username": "cliente_demo",
                "email": "cliente@example.com",
                "password": "ClienteSecure123!",
                "first_name": "Juan",
                "last_name": "Pérez García",
                "dni": "87654321",
                "telefono": "912345678",
                "rol": roles["Cliente"],
                "crear_profile": True,
            },
            {
                "tipo": "Recepcionista",
                "username": "recepcionista_demo",
                "email": "recepcionista@example.com",
                "password": "RecepcionSecure123!",
                "first_name": "María",
                "last_name": "Gómez López",
                "dni": "11223344",
                "telefono": "945678901",
                "rol": roles["Recepcionista"],
                "crear_profile": True,
            },
        ]

        # Crear usuarios
        for usuario_data in usuarios:
            try:
                tipo = usuario_data.pop("tipo")
                crear_profile = usuario_data.pop("crear_profile")

                # Verificar si el usuario ya existe
                if User.objects.filter(email=usuario_data["email"]).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Usuario {tipo} ({usuario_data['email']}) ya existe. Saltando..."
                        )
                    )
                    continue

                # Crear usuario
                user = User.objects.create_user(**usuario_data)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Usuario {tipo} creado exitosamente")
                )

                # Crear perfil específico
                if crear_profile:
                    if tipo == "Admin":
                        Admin.objects.get_or_create(usuario=user)
                    elif tipo == "Cliente":
                        Cliente.objects.get_or_create(usuario=user)
                    elif tipo == "Recepcionista":
                        Recepcionista.objects.get_or_create(usuario=user)

                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Perfil de {tipo} creado\n")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creando usuario: {str(e)}\n")
                )

        # Mostrar resumen
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN DE USUARIOS DE PRUEBA"))
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))

        usuarios_creados = User.objects.all().order_by("-fecha_creacion")[:3]

        for user in usuarios_creados:
            rol = user.rol.nombre if user.rol else "Sin rol"
            profile_type = "N/A"

            if hasattr(user, "admin"):
                profile_type = "Admin"
            elif hasattr(user, "cliente"):
                profile_type = "Cliente"
            elif hasattr(user, "recepcionista"):
                profile_type = "Recepcionista"

            self.stdout.write(f"""
╔══════════════════════════════════════════════════════════════════╗
║ 👤 Usuario: {user.get_full_name():<53}║
╠══════════════════════════════════════════════════════════════════╣
║ Email:        {user.email:<53}║
║ Username:     {user.username:<53}║
║ Rol:          {rol:<53}║
║ Tipo Perfil:  {profile_type:<53}║
║ DNI:          {user.dni:<53}║
║ Teléfono:     {user.telefono:<53}║
║ Activo:       {'Sí' if user.activo else 'No':<53}║
║ Creado:       {user.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S'):<53}║
╚══════════════════════════════════════════════════════════════════╝
""")

        # Datos de login
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("🔑 CREDENCIALES DE ACCESO"))
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))

        for usuario_data in usuarios:
            self.stdout.write(f"""
📧 {usuario_data.get('tipo', 'Usuario').upper()}:
   Email:    {usuario_data.get('email', 'N/A')}
   Password: {usuario_data.get('password', 'N/A')}
""")

        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(
            self.style.SUCCESS("\n✅ ¡Usuarios de prueba creados exitosamente!\n")
        )
        self.stdout.write(
            self.style.WARNING(
                "⚠️  IMPORTANTE: Cambiar estas contraseñas antes de usar en producción\n"
            )
        )
