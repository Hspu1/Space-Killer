class BaseAppError(Exception):
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class RedisNotReachableError(BaseAppError):
    message: str = "Redis isn't reachable/initialized"


class PostgresNotReachableError(BaseAppError):
    message: str = "Postgres isn't reachable/initialized"


class ProviderIDMissingError(BaseAppError):
    message: str = "Provider data is missing a unique ID"


class HttpServiceNotConnectedError(BaseAppError):
    message: str = "HttpService isn't connected"


class ScyllaNotReachableError(BaseAppError):
    message: str = "Scylla isn't reachable/initialized"
