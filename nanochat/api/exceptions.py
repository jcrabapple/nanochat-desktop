class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(APIError):
    """Raised when API key is invalid"""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded"""
    pass


class ConnectionError(APIError):
    """Raised when connection fails"""
    pass


class TimeoutError(APIError):
    """Raised when request times out"""
    pass


class InvalidRequestError(APIError):
    """Raised when request is invalid"""
    pass
