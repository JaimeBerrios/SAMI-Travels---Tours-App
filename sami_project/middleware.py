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
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://esm.sh https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "font-src 'self' data: https://cdnjs.cloudflare.com; img-src 'self' data: https:; "
            "frame-src https://www.google.com; connect-src 'self' https://esm.sh; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'self'; form-action 'self'",
        )
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        return response
