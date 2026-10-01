import importlib
import pkgutil
from typing import Callable, Any
from app.contracts.models import ToolSpec, ToolArgs, Evidence

_TOOL_REGISTRY: dict[str, tuple[ToolSpec, Callable[[ToolArgs], Evidence]]] = {}


def register_tool(spec: ToolSpec):
    """Decorator to register a tool specification and its handler function."""
    def decorator(fn: Callable[[ToolArgs], Evidence]):
        _TOOL_REGISTRY[spec.name] = (spec, fn)
        return fn
    return decorator


def get_registry() -> dict[str, tuple[ToolSpec, Callable[[ToolArgs], Evidence]]]:
    """Return the current tool registry map."""
    return _TOOL_REGISTRY


def discover(package_name: str = "app.tools") -> dict[str, tuple[ToolSpec, Callable[[ToolArgs], Evidence]]]:
    """Auto-discover and import all modules inside the specified tools package."""
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return _TOOL_REGISTRY

    if hasattr(package, "__path__"):
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            if not module_name.startswith("_"):
                try:
                    importlib.import_module(f"{package_name}.{module_name}")
                except Exception:
                    pass
    return _TOOL_REGISTRY
