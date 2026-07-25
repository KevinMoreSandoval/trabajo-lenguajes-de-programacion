"""
Middleware de Seguridad
Implementa auditoría, logging y protecciones adicionales
"""

import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache

security_logger = logging.getLogger("app.security")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Agrega headers de seguridad adicionales
    """

    def process_response(self, request, response):
        # Content Security Policy
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:"
        )

        # Prevenir MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # Prevenir Clickjacking
        response["X-Frame-Options"] = "DENY"

        # Prevenir XSS
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (antiguamente Feature Policy)
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Strict Transport Security (solo en producción con HTTPS)
        # response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        return response


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Registra todas las solicitudes para auditoría
    """

    SENSITIVE_PATHS = ["/signin", "/signup", "/password", "/api/auth"]

    def process_request(self, request):
        # Información básica
        audit_data = {
            "method": request.method,
            "path": request.path,
            "ip": self.get_client_ip(request),
            "user": str(request.user) if request.user.is_authenticated else "Anonymous",
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        }

        # No registrar datos sensibles en rutas protegidas
        if any(
            sensitive_path in request.path for sensitive_path in self.SENSITIVE_PATHS
        ):
            if request.method == "POST":
                audit_data["has_sensitive_data"] = True
                security_logger.info(
                    f"Sensitive POST request: {json.dumps(audit_data)}"
                )
        else:
            security_logger.info(f"Request: {json.dumps(audit_data)}")

        return None

    def process_response(self, request, response):
        # Registrar respuestas de error
        if response.status_code >= 400:
            error_data = {
                "path": request.path,
                "status_code": response.status_code,
                "user": (
                    str(request.user) if request.user.is_authenticated else "Anonymous"
                ),
                "ip": self.get_client_ip(request),
            }
            security_logger.warning(f"Error response: {json.dumps(error_data)}")

        return response

    @staticmethod
    def get_client_ip(request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    """
    Implementa rate limiting para prevenir ataques de fuerza bruta
    """

    # Rutas sensibles con límites estrictos
    RATE_LIMIT_PATHS = {
        "/signin": {"max_attempts": 5, "time_window": 300},  # 5 intentos en 5 min
        "/signup": {"max_attempts": 10, "time_window": 3600},  # 10 intentos en 1 hora
    }

    def process_request(self, request):
        # Obtener ruta
        path = request.path

        # Verificar si la ruta tiene límite de velocidad
        for rate_path, config in self.RATE_LIMIT_PATHS.items():
            if path == rate_path and request.method == "POST":
                # Obtener identificador único (IP o usuario)
                client_id = AuditLoggingMiddleware.get_client_ip(request)

                # Crear clave de caché
                cache_key = f"rate_limit:{path}:{client_id}"

                # Obtener intentos del caché
                attempts = cache.get(cache_key, 0)

                # Verificar límite
                if attempts >= config["max_attempts"]:
                    security_logger.critical(
                        f"Rate limit exceeded for {client_id} on {path}"
                    )
                    return JsonResponse(
                        {"error": "Demasiados intentos. Intente más tarde."}, status=429
                    )

                # Incrementar contador
                cache.set(cache_key, attempts + 1, config["time_window"])

        return None


class InputSanitizationMiddleware(MiddlewareMixin):
    """
    Sanitiza entrada de datos POST/GET
    """

    def process_request(self, request):
        from djangocrud.security import SecurityValidator

        if request.method in ["POST", "GET"]:
            data = request.POST if request.method == "POST" else request.GET

            for key, value in data.items():
                # Validar contra inyección SQL
                if not SecurityValidator.validate_input_against_injection(value):
                    security_logger.critical(
                        f"SQL Injection attempt detected in {key}: {value[:50]}"
                    )
                    return JsonResponse(
                        {"error": "Entrada inválida detectada."}, status=400
                    )

        return None


class XSSProtectionMiddleware(MiddlewareMixin):
    """
    Protege contra XSS escapando variables en templates
    """

    def process_response(self, request, response):
        # Agregar header de protección XSS
        response["X-XSS-Protection"] = "1; mode=block"

        return response


class ClickjackingProtectionMiddleware(MiddlewareMixin):
    """
    Previene ataques de Clickjacking
    """

    def process_response(self, request, response):
        # Solo permitir framing desde el mismo origen
        response["X-Frame-Options"] = "SAMEORIGIN"

        return response
