from django.conf import settings

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",                       # no inline scripts, no third-party scripts
    "style-src 'self' 'unsafe-inline'",        # templates use a few style="" attributes
    "img-src 'self' data: blob:",              # blob: = photo preview before upload
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
PERMISSIONS = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

class SecurityHeadersMiddleware:
    """Adds CSP + Permissions-Policy. The Django admin is skipped (it has its own inline code)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def _is_admin(self, path):
        marker = "/" + settings.ADMIN_URL
        return path.startswith(marker) or any(path.startswith("/" + code + marker) for code, _ in settings.LANGUAGES)

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Permissions-Policy", PERMISSIONS)
        if not self._is_admin(request.path):
            response.headers.setdefault("Content-Security-Policy", CSP)
        return response
