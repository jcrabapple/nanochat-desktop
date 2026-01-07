"""Model list caching for NanoChat Desktop"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ModelCache:
    """
    Cache for storing available models from the API

    Caches models locally to avoid frequent API calls.
    Cache expires after 24 hours.
    """

    CACHE_VERSION = 1  # Increment if cache format changes
    CACHE_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize model cache

        Args:
            cache_dir: Directory to store cache file (default: ~/.config/nanochat/)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".config" / "nanochat"

        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "models_cache.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_models(self) -> Optional[List[str]]:
        """
        Get cached models if available and not expired

        Returns:
            List of model IDs if cache is valid, None otherwise
        """
        if not self.cache_file.exists():
            logger.debug("No models cache file found")
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check cache version
            if cache_data.get('version') != self.CACHE_VERSION:
                logger.info("Models cache version mismatch, ignoring")
                return None

            # Check expiry
            cached_time = cache_data.get('timestamp', 0)
            if time.time() - cached_time > self.CACHE_EXPIRY_SECONDS:
                logger.info("Models cache expired")
                return None

            models = cache_data.get('models', [])
            logger.info(f"Loaded {len(models)} models from cache")
            return models

        except Exception as e:
            logger.warning(f"Failed to load models cache: {e}")
            return None

    def save_models(self, models: List[str]) -> None:
        """
        Save models to cache

        Args:
            models: List of model IDs to cache
        """
        try:
            cache_data = {
                'version': self.CACHE_VERSION,
                'timestamp': time.time(),
                'models': models
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Cached {len(models)} models to {self.cache_file}")

        except Exception as e:
            logger.error(f"Failed to save models cache: {e}")
            raise

    def clear_cache(self) -> None:
        """Clear cached models"""
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                logger.info("Cleared models cache")
            except Exception as e:
                logger.warning(f"Failed to clear models cache: {e}")
        else:
            logger.debug("No models cache to clear")

    def is_cache_valid(self) -> bool:
        """
        Check if cached models are available and valid

        Returns:
            True if cache exists and is not expired
        """
        return self.get_cached_models() is not None
