from src.shared.errors import UnknownRouteError
from src.specs.models import FormatSpec


class RouteRegistry:
    def __init__(self, specs: dict[tuple[str, str], FormatSpec] | None = None):
        self._specs: dict[tuple[str, str], FormatSpec] = specs or {}

    def register(self, specs: dict[tuple[str, str], FormatSpec]) -> None:
        self._specs.update(specs)

    def resolve(self, artifact_type: str, surface: str) -> FormatSpec:
        key = (artifact_type, surface)
        if key not in self._specs:
            raise UnknownRouteError(
                artifact_type, surface, available=list(self._specs.keys())
            )
        return self._specs[key]

    def list_routes(self) -> list[tuple[str, str]]:
        return list(self._specs.keys())


# Singleton populated at startup
registry = RouteRegistry()
