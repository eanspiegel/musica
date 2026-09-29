import logging
from typing import Optional

from app.core.ports.recognition import IAudioRecognition

logger = logging.getLogger(__name__)


class RecognitionService:
    """Thin service wrapping IAudioRecognition for use as a FastAPI dependency."""

    def __init__(self, recognition: IAudioRecognition) -> None:
        self._recognition = recognition

    async def recognize(self, file_path: str) -> Optional[dict]:
        logger.debug("RecognitionService.recognize: %s", file_path)
        return await self._recognition.recognize(file_path)
