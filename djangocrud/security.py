"""
Módulo de Seguridad para la Aplicación
Implementa protecciones contra vulnerabilidades comunes
"""

import re
import logging
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.contrib.auth.hashers import make_password

# Logger de seguridad
security_logger = logging.getLogger("app.security")


class SecurityValidator:
    """
    Validador de seguridad para entrada de datos
    Protege contra: SQL Injection, XSS, Unicode Exploits, etc.
    """

    # Patrones de SQL Injection común
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(--|#|\/\*|\*\/)",  # Comentarios SQL
        r"(;\s*DROP|;\s*DELETE|;\s*UPDATE|;\s*INSERT)",
        r"(\bOR\b.*=.*)",  # OR 1=1
        r"(\bAND\b.*=.*)",  # AND 1=1
    ]

    # Patrones de XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # onclick, onload, etc
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    # Caracteres peligrosos
    DANGEROUS_CHARS = ["<", ">", '"', "'", "%", ";", "--", "/*", "*/", "xp_", "sp_"]

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Valida y sanitiza email
        Protección contra: inyección SQL, XSS
        """
        if not email:
            raise ValidationError("El email no puede estar vacío.")

        # Expresión regular estricta para email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValidationError("Email inválido.")

        # Escapar caracteres HTML
        email = escape(email)

        if len(email) > 254:  # Límite RFC 5321
            raise ValidationError("Email demasiado largo.")

        security_logger.info(f"Email validado: {email[:50]}")
        return email

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Valida contraseña con criterios de seguridad
        Mínimo: 8 caracteres, mayúscula, minúscula, número, símbolo
        """
        if not password:
            raise ValidationError("La contraseña no puede estar vacía.")

        if len(password) < 8:
            raise ValidationError("La contraseña debe tener mínimo 8 caracteres.")

        if not re.search(r"[A-Z]", password):
            raise ValidationError("La contraseña debe contener al menos una mayúscula.")

        if not re.search(r"[a-z]", password):
            raise ValidationError("La contraseña debe contener al menos una minúscula.")

        if not re.search(r"\d", password):
            raise ValidationError("La contraseña debe contener al menos un número.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "La contraseña debe contener al menos un símbolo especial."
            )

        # Revisar si está en lista común de contraseñas débiles
        weak_passwords = ["Password1!", "Admin123!", "Test1234!", "Django1!"]
        if password in weak_passwords:
            raise ValidationError("Esta contraseña es demasiado común.")

        security_logger.info("Contraseña validada exitosamente")
        return password

    @staticmethod
    def validate_dni(dni: str) -> str:
        """
        Valida DNI peruano
        Protección contra: inyección SQL, formato inválido
        """
        if not dni:
            raise ValidationError("El DNI no puede estar vacío.")

        # Solo números, exactamente 8 dígitos
        if not re.match(r"^\d{8}$", dni):
            raise ValidationError("El DNI debe tener exactamente 8 dígitos.")

        # Validación del dígito verificador (algoritmo peruano)
        dni_int = int(dni)
        if dni_int == 0:
            raise ValidationError("DNI inválido.")

        security_logger.info("DNI validado exitosamente")
        return dni

    @staticmethod
    def validate_telefono(telefono: str) -> str:
        """
        Valida número de teléfono peruano
        Protección contra: inyección SQL, formato inválido
        """
        if not telefono:
            raise ValidationError("El teléfono no puede estar vacío.")

        # Solo números, exactamente 9 dígitos para Perú
        if not re.match(r"^\d{9}$", telefono):
            raise ValidationError("El teléfono debe tener exactamente 9 dígitos.")

        # Validar que sea un número válido (primera cifra)
        if not telefono.startswith(("9", "1")):
            raise ValidationError("Número de teléfono inválido.")

        security_logger.info("Teléfono validado exitosamente")
        return telefono

    @staticmethod
    def validate_text(
        text: str, max_length: int = 500, allow_html: bool = False
    ) -> str:
        """
        Valida y sanitiza texto general
        Protección contra: SQL Injection, XSS
        """
        if not isinstance(text, str):
            raise ValidationError("El texto debe ser una cadena.")

        if len(text) > max_length:
            raise ValidationError(f"El texto no puede exceder {max_length} caracteres.")

        if len(text.strip()) == 0:
            raise ValidationError("El texto no puede estar vacío.")

        # Verificar SQL Injection
        text_upper = text.upper()
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                security_logger.warning(
                    f"Intento de SQL Injection detectado: {text[:50]}"
                )
                raise ValidationError("Contiene caracteres o patrones no permitidos.")

        # Verificar XSS
        if not allow_html:
            for pattern in SecurityValidator.XSS_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    security_logger.warning(f"Intento de XSS detectado: {text[:50]}")
                    raise ValidationError("No se permiten caracteres HTML.")

        # Escapar HTML
        text = escape(text)

        security_logger.info("Texto validado exitosamente")
        return text

    @staticmethod
    def validate_input_against_injection(user_input: str) -> bool:
        """
        Detecta intentos de inyección SQL
        Retorna True si es seguro, False si detecta inyección
        """
        if not user_input:
            return True

        user_input_upper = user_input.upper()

        # Revisar patrones peligrosos
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, user_input_upper, re.IGNORECASE):
                security_logger.critical(f"SQL INJECTION ATTEMPT: {user_input[:100]}")
                return False

        # Revisar caracteres peligrosos excesivos
        dangerous_count = sum(
            user_input.count(char) for char in SecurityValidator.DANGEROUS_CHARS
        )
        if dangerous_count > 3:
            security_logger.warning(
                f"High amount of dangerous chars detected: {user_input[:50]}"
            )
            return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza nombre de archivo
        Protección contra: path traversal, inyección
        """
        # Eliminar caracteres peligrosos
        filename = re.sub(r"[^\w\s.-]", "", filename)
        # Remover path traversal
        filename = filename.replace("..", "")
        filename = filename.replace("/", "")
        filename = filename.replace("\\", "")

        return filename


class RateLimiter:
    """
    Limitador de velocidad para prevenir ataques de fuerza bruta
    """

    def __init__(self):
        self.attempts = {}

    def check_rate_limit(
        self, identifier: str, max_attempts: int = 5, time_window: int = 300
    ) -> bool:
        """
        Verifica si se excedió el límite de intentos
        identifier: IP, email, user_id, etc
        max_attempts: máximo de intentos permitidos
        time_window: ventana de tiempo en segundos
        """
        import time

        current_time = time.time()

        if identifier not in self.attempts:
            self.attempts[identifier] = []

        # Limpiar intentos fuera de la ventana de tiempo
        self.attempts[identifier] = [
            timestamp
            for timestamp in self.attempts[identifier]
            if current_time - timestamp < time_window
        ]

        # Verificar si se exceede el límite
        if len(self.attempts[identifier]) >= max_attempts:
            security_logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        # Registrar nuevo intento
        self.attempts[identifier].append(current_time)
        return True


# Instancia global del limitador de velocidad
rate_limiter = RateLimiter()
