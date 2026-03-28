class BaseAppError(Exception):
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class SafeStartError(BaseAppError):
    message: str = "Application failed to start -> infrastructure is down"

    def __init__(self, error_count: int | None = None) -> None:
        msg = f"Startup failed with {error_count} errors" if error_count else self.message
        super().__init__(message=msg)


class RedisNotReachableError(BaseAppError):
    message: str = "Redis isn't reachable/initialized"


class PostgresNotReachableError(BaseAppError):
    message: str = "Postgres isn't reachable/initialized"


class ProviderIDMissingError(BaseAppError):
    message: str = "Provider data is missing a unique ID"


class HttpServiceNotConnectedError(BaseAppError):
    message: str = "HttpService isn't connected"
