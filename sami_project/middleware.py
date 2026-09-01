class SecurityHeadersMiddleware:
    """Add a conservative CSP and permissions policy to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/sami-admin/"):
            response["X-Robots-Tag"] = "noindex, nofollow"
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://esm.sh https://cdn.jsdelivr.net "
            "https://www.googletagmanager.com https://tagmanager.google.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net "
            "https://www.googletagmanager.com "
            "https://tagmanager.google.com https://fonts.googleapis.com; "
            "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "frame-src https://www.google.com https://www.googletagmanager.com; "
            "connect-src 'self' https://esm.sh https://www.googletagmanager.com https://www.google.com "
            "https://*.google-analytics.com https://*.analytics.google.com; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'self'; form-action 'self'",
        )
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        return response
