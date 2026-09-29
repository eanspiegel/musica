import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class FileManager:
    """Filesystem utilities with path-traversal protection."""

    def ensure_dir(self, path: str) -> Path:
        """Create directory if it does not exist and return resolved Path."""
        resolved = Path(path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory: %s", resolved)
        return resolved

    def safe_join(self, base: str, filename: str) -> Path:
        """Join base and filename, raising ValueError if the result escapes base."""
        base_path = Path(base).resolve()
        joined = (base_path / filename).resolve()
        if not str(joined).startswith(str(base_path)):
            raise ValueError(
                f"Path traversal detected: '{filename}' escapes base directory '{base_path}'"
            )
        return joined

    def sanitize_filename(self, name: str) -> str:
        """Remove path separators and dangerous characters from a filename."""
        sanitized = _UNSAFE_CHARS.sub("_", name)
        # Collapse multiple underscores
        sanitized = re.sub(r"_+", "_", sanitized).strip("_")
        return sanitized or "unnamed"
