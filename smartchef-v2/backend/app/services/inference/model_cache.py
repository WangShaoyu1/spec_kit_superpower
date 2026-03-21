from collections import OrderedDict

from app.services.inference.engine import IntentSlotInferenceEngine

MAX_CACHED_MODELS = 5


class ModelCache:
    """LRU cache for loaded ONNX inference engines."""

    _cache: OrderedDict[str, IntentSlotInferenceEngine] = OrderedDict()

    @classmethod
    def get_or_load(cls, model_dir: str) -> IntentSlotInferenceEngine:
        if model_dir in cls._cache:
            cls._cache.move_to_end(model_dir)
            return cls._cache[model_dir]
        if len(cls._cache) >= MAX_CACHED_MODELS:
            cls._cache.popitem(last=False)
        engine = IntentSlotInferenceEngine(model_dir)
        cls._cache[model_dir] = engine
        return engine

    @classmethod
    def evict(cls, model_dir: str) -> None:
        cls._cache.pop(model_dir, None)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()
