"""
Tests de Seguridad
Valida que todas las medidas de protección funcionen correctamente
"""

from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from djangocrud.security import SecurityValidator, rate_limiter
from authentication.models import Rol

User = get_user_model()


class SQLInjectionProtectionTests(TestCase):
    """Tests para protección contra inyección SQL"""
    
    def test_sql_injection_union_select(self):
        """Detecta UNION SELECT"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "user' UNION SELECT * FROM usuarios--"
            )
    
    def test_sql_injection_or_condition(self):
        """Detecta OR 1=1"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "' OR '1'='1"
            )
    
    def test_sql_injection_drop_table(self):
        """Detecta DROP TABLE"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "'; DROP TABLE usuarios;--"
            )
    
    def test_sql_injection_insert_into(self):
        """Detecta INSERT INTO"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "'; INSERT INTO usuarios VALUES (...)--"
            )
    
    def test_valid_text_no_injection(self):
        """Texto válido no lanza error"""
        result = SecurityValidator.validate_text("Usuario normal")
        self.assertEqual(result, "Usuario normal")


class XSSProtectionTests(TestCase):
    """Tests para protección contra XSS"""
    
    def test_xss_script_tag(self):
        """Detecta <script> tags"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "<script>alert('XSS')</script>"
            )
    
    def test_xss_onclick(self):
        """Detecta onclick handlers"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "<img src=x onerror='alert(1)'>"
            )
    
    def test_xss_javascript_protocol(self):
        """Detecta javascript: protocol"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_text(
                "<a href='javascript:alert(1)'>click</a>"
            )
    
    def test_valid_text_no_xss(self):
        """Texto válido sin XSS"""
        result = SecurityValidator.validate_text("Contenido normal")
        self.assertIsNotNone(result)


class EmailValidationTests(TestCase):
    """Tests para validación de email"""
    
    def test_valid_email(self):
        """Email válido"""
        result = SecurityValidator.validate_email("user@example.com")
        self.assertEqual(result, "user@example.com")
    
    def test_invalid_email_format(self):
        """Email con formato inválido"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_email("not-an-email")
    
    def test_empty_email(self):
        """Email vacío"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_email("")
    
    def test_email_too_long(self):
        """Email demasiado largo"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_email("a" * 300 + "@example.com")
    
    def test_email_with_sql_injection(self):
        """Email con intento de SQL injection"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_email("test' OR '1'='1@example.com")


class PasswordValidationTests(TestCase):
    """Tests para validación de contraseñas fuertes"""
    
    def test_valid_strong_password(self):
        """Contraseña fuerte válida"""
        result = SecurityValidator.validate_password("MySecure123!Pass")
        self.assertEqual(result, "MySecure123!Pass")
    
    def test_password_too_short(self):
        """Contraseña muy corta"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_password("Short1!")
    
    def test_password_no_uppercase(self):
        """Contraseña sin mayúsculas"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_password("nouppercas3!")
    
    def test_password_no_lowercase(self):
        """Contraseña sin minúsculas"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_password("NOLOWERCASE3!")
    
    def test_password_no_number(self):
        """Contraseña sin números"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_password("NoNumbers!")
    
    def test_password_no_special_char(self):
        """Contraseña sin caracteres especiales"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_password("NoSpecialChar1")
    
    def test_common_password(self):
        """Contraseña común no permitida"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_password("Password1!")


class DNIValidationTests(TestCase):
    """Tests para validación de DNI peruano"""
    
    def test_valid_dni(self):
        """DNI válido"""
        result = SecurityValidator.validate_dni("12345678")
        self.assertEqual(result, "12345678")
    
    def test_dni_too_short(self):
        """DNI demasiado corto"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_dni("1234567")
    
    def test_dni_with_letters(self):
        """DNI con letras"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_dni("1234567A")
    
    def test_dni_with_spaces(self):
        """DNI con espacios"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_dni("1234 5678")


class TelefonoValidationTests(TestCase):
    """Tests para validación de teléfono peruano"""
    
    def test_valid_telefono(self):
        """Teléfono válido"""
        result = SecurityValidator.validate_telefono("987654321")
        self.assertEqual(result, "987654321")
    
    def test_telefono_too_short(self):
        """Teléfono muy corto"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_telefono("98765432")
    
    def test_telefono_with_letters(self):
        """Teléfono con letras"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_telefono("98765432A")
    
    def test_invalid_starting_digit(self):
        """Teléfono con dígito inicial inválido"""
        with self.assertRaises(ValidationError):
            SecurityValidator.validate_telefono("234567890")


class LoginSecurityTests(TestCase):
    """Tests para seguridad en login"""
    
    def setUp(self):
        # Crear rol cliente
        self.rol = Rol.objects.create(nombre='Cliente')
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
            rol=self.rol
        )
        self.client = Client()
    
    def test_login_with_sql_injection(self):
        """Login rechaza inyección SQL"""
        response = self.client.post('/signin', {
            'email': "test@example.com' OR '1'='1",
            'password': 'anything'
        })
        # Debe rechazar o no autenticar
        self.assertFalse(response.wsgi_request.user.is_authenticated \
                        if hasattr(response, 'wsgi_request') else True)
    
    def test_login_valid_credentials(self):
        """Login exitoso con credenciales válidas"""
        response = self.client.post('/signin', {
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_login_invalid_credentials(self):
        """Login rechaza credenciales inválidas"""
        response = self.client.post('/signin', {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, 200)


class SignupSecurityTests(TestCase):
    """Tests para seguridad en registro"""
    
    def setUp(self):
        # Crear rol cliente
        self.rol = Rol.objects.create(nombre='Cliente')
        self.client = Client()
    
    def test_signup_weak_password(self):
        """Signup rechaza contraseña débil"""
        response = self.client.post('/signup', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123456',
            'confirm_password': '123456',
            'first_name': 'New',
            'last_name': 'User',
            'dni': '12345678',
            'telefono': '987654321',
            'fecha_nacimiento': '1990-01-01'
        })
        # Debe rechazar por contraseña débil
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_signup_invalid_dni(self):
        """Signup rechaza DNI inválido"""
        response = self.client.post('/signup', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'dni': 'ABCDEFGH',  # DNI inválido
            'telefono': '987654321',
            'fecha_nacimiento': '1990-01-01'
        })
        # Debe rechazar por DNI inválido
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_signup_invalid_telefono(self):
        """Signup rechaza teléfono inválido"""
        response = self.client.post('/signup', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'dni': '12345678',
            'telefono': 'invalid',  # Teléfono inválido
            'fecha_nacimiento': '1990-01-01'
        })
        # Debe rechazar por teléfono inválido
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_signup_success(self):
        """Signup exitoso con datos válidos"""
        response = self.client.post('/signup', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'dni': '12345678',
            'telefono': '987654321',
            'fecha_nacimiento': '1990-01-01'
        }, follow=True)
        # Debe crear el usuario
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())


class RateLimiterTests(TestCase):
    """Tests para rate limiting"""
    
    def test_rate_limiter_allow_within_limit(self):
        """Rate limiter permite intentos dentro del límite"""
        result = rate_limiter.check_rate_limit('test_user', max_attempts=5, time_window=300)
        self.assertTrue(result)
    
    def test_rate_limiter_exceed_limit(self):
        """Rate limiter rechaza cuando se excede el límite"""
        identifier = 'test_user_2'
        max_attempts = 3
        
        # Hacer 3 intentos (permitidos)
        for _ in range(max_attempts):
            result = rate_limiter.check_rate_limit(identifier, max_attempts=max_attempts, time_window=300)
            self.assertTrue(result)
        
        # El 4to intento debe ser rechazado
        result = rate_limiter.check_rate_limit(identifier, max_attempts=max_attempts, time_window=300)
        self.assertFalse(result)
