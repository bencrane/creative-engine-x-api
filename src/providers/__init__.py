from src.providers.elevenlabs_provider import ElevenLabsProvider
from src.providers.elevenlabs_provider import ProviderResult as ElevenLabsProviderResult
from src.providers.remotion_provider import RemotionProvider
from src.providers.remotion_provider import ProviderResult as RemotionProviderResult

# Backwards-compatible alias
ProviderResult = ElevenLabsProviderResult

__all__ = [
    "ElevenLabsProvider",
    "ElevenLabsProviderResult",
    "RemotionProvider",
    "RemotionProviderResult",
    "ProviderResult",
]
