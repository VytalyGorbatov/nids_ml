"""NIDS ML training package."""

from importlib import import_module
from typing import Any

__all__ = (
	"DatasetBuilder", "TwoWayDatasetBuilder", "ClassifierPipeline",
	"TwoWayPipeline", "Trainer", "TwoWayTrainer",
)


def __getattr__(name: str) -> Any:
	"""Preserve public re-exports without importing Torch for lightweight tools."""
	modules = {
		"DatasetBuilder": (".data", "DatasetBuilder"),
		"TwoWayDatasetBuilder": (".data", "TwoWayDatasetBuilder"),
		"ClassifierPipeline": (".pipelines", "ClassifierPipeline"),
		"TwoWayPipeline": (".pipelines", "TwoWayPipeline"),
		"Trainer": (".training", "Trainer"),
		"TwoWayTrainer": (".training", "TwoWayTrainer"),
	}
	if name not in modules:
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
	module_name, attribute = modules[name]
	return getattr(import_module(module_name, __name__), attribute)
