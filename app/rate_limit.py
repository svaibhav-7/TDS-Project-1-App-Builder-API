from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI

# Shared limiter instance
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])  # default global limit

# Helper to wire middleware and handler

def setup_rate_limiting(app: FastAPI) -> None:
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
