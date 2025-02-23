"""Content Security Policy (CSP) configuration for the Edify application."""


def get_csp_policy(filebase_url: str) -> dict:
    """
    Get the Content Security Policy configuration.

    Args:
        filebase_url: The Filebase URL from environment variables

    Returns:
        dict: The CSP policy configuration
    """
    return {
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "https://ajax.googleapis.com",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://code.jquery.com",  # allow jQuery CDN
            "https://cdn.socket.io/",  # allow SocketIO
            "https://www.googletagmanager.com/",  # allow analytics
            "'unsafe-inline'",  # Use hashes or nonces in production
        ],
        "style-src": [
            "'self'",
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "'unsafe-inline'",  # Required for inline styles and dynamic styling
        ],
        "font-src": [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdn.jsdelivr.net",  # Bootstrap 4 fonts
            "https://cdnjs.cloudflare.com",  # Font Awesome fonts
            "data:",  # Allow data URIs for fonts
        ],
        "img-src": [
            "'self'",
            "data:",
            "https://cdnjs.cloudflare.com",
            "https://robohash.org",
            filebase_url,
            "https://*.googleusercontent.com",  # Allow Google user profile images
        ],
        "connect-src": [
            "'self'",
            "wss://*.ilummu.com",  # Allow WebSocket connections
            "https://*.ilummu.com",  # Allow HTTP/HTTPS connections
            "https://www.google-analytics.com",
            "https://www.googletagmanager.com",  # Required for Google Analytics
            "https://accounts.google.com",  # Google OAuth
            "https://oauth2.googleapis.com",  # Google OAuth token endpoint
            "https://www.googleapis.com",  # Google APIs
        ],
        "form-action": [
            "'self'",
            "https://accounts.google.com",  # Allow form submissions to Google OAuth
        ],
        "frame-src": [
            "'self'",
            "https://accounts.google.com",  # Allow Google OAuth popup/iframe
        ],
        "worker-src": ["'self'", "blob:"],  # Allow Web Workers if needed
        "child-src": ["'self'", "blob:"],  # Allow blob: for dynamic scripts
    }


def generate_csp_header(policy: dict) -> str:
    """
    Generate the CSP header string from the policy dictionary.

    Args:
        policy: The CSP policy dictionary

    Returns:
        str: The formatted CSP header string
    """
    return "; ".join(
        f"{key} {' '.join(value) if isinstance(value, list) else value}"
        for key, value in policy.items()
    )
