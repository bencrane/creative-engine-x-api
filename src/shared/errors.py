class SpecNotFoundError(Exception):
    def __init__(self, spec_id: str):
        self.spec_id = spec_id
        super().__init__(f"Spec not found: {spec_id}")


class UnknownRouteError(Exception):
    def __init__(
        self,
        artifact_type: str,
        surface: str,
        available: list[tuple[str, str]] | None = None,
    ):
        self.artifact_type = artifact_type
        self.surface = surface
        self.available = available or []
        super().__init__(
            f"No spec for artifact_type={artifact_type!r}, surface={surface!r}"
        )


class AuthenticationError(Exception):
    def __init__(self, detail: str = "Authentication required"):
        self.detail = detail
        super().__init__(detail)


class RateLimitExceededError(Exception):
    def __init__(self, detail: str = "Rate limit exceeded"):
        self.detail = detail
        super().__init__(detail)


class StorageError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class JobNotFoundError(Exception):
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class ValidationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
