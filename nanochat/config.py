import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager for NanoChat Desktop

    Loads settings from:
    1. Environment variables (.env file)
    2. User config file (~/.config/nanochat/config.ini)
    3. Defaults
    """

    DEFAULT_API_BASE_URL = "https://nano-gpt.com/api"
    DEFAULT_MODEL = "gpt-4"
    DEFAULT_DB_PATH = "~/.local/share/nanochat/conversations.db"
    DEFAULT_LOG_LEVEL = "INFO"

    def __init__(self):
        """Initialize configuration"""
        # Load .env file if exists
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded .env from {env_file}")

        # Initialize values
        self._api_key: Optional[str] = None
        self._api_base_url: Optional[str] = None
        self._model: Optional[str] = None
        self._db_path: Optional[str] = None

        # Try to load from config file
        self._load_from_file()

    def _load_from_file(self):
        """Load configuration from user config file"""
        config_dir = Path.home() / ".config" / "nanochat"
        config_file = config_dir / "config.ini"

        if config_file.exists():
            try:
                # Simple key=value parsing
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            if key == 'api_key':
                                self._api_key = value
                            elif key == 'api_base_url':
                                self._api_base_url = value
                            elif key == 'model':
                                self._model = value

                logger.info(f"Loaded config from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

    def save_to_file(self, api_key: str, api_base_url: str = None, model: str = None):
        """
        Save configuration to user config file

        Args:
            api_key: API key to save
            api_base_url: API base URL (optional)
            model: Model name (optional)
        """
        config_dir = Path.home() / ".config" / "nanochat"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.ini"

        try:
            with open(config_file, 'w') as f:
                f.write(f"api_key={api_key}\n")
                if api_base_url:
                    f.write(f"api_base_url={api_base_url}\n")
                if model:
                    f.write(f"model={model}\n")

            # Update cached values
            self._api_key = api_key
            if api_base_url:
                self._api_base_url = api_base_url
            if model:
                self._model = model

            logger.info(f"Saved config to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    @property
    def api_key(self) -> str:
        """Get API key from environment or config file"""
        if self._api_key:
            return self._api_key

        # Try environment variable
        api_key = os.getenv("NANOCHAT_API_KEY")
        if api_key:
            return api_key

        return ""

    @property
    def api_base_url(self) -> str:
        """Get API base URL"""
        if self._api_base_url:
            return self._api_base_url

        return os.getenv("NANOCHAT_API_BASE_URL", self.DEFAULT_API_BASE_URL)

    @property
    def model(self) -> str:
        """Get default model"""
        if self._model:
            return self._model

        return os.getenv("NANOCHAT_MODEL", self.DEFAULT_MODEL)

    @property
    def db_path(self) -> str:
        """Get database path"""
        if self._db_path:
            return self._db_path

        path = os.getenv("NANOCHAT_DB_PATH", self.DEFAULT_DB_PATH)
        # Expand ~ to home directory
        return str(Path(path).expanduser())

    @property
    def log_level(self) -> str:
        """Get log level"""
        return os.getenv("NANOCHAT_LOG_LEVEL", self.DEFAULT_LOG_LEVEL)

    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and len(self.api_key) > 10)

    def clear_api_key(self):
        """Clear stored API key"""
        self._api_key = None
        # Also remove from config file
        config_file = Path.home() / ".config" / "nanochat" / "config.ini"
        if config_file.exists():
            try:
                lines = []
                with open(config_file, 'r') as f:
                    for line in f:
                        if not line.strip().startswith('api_key='):
                            lines.append(line)

                with open(config_file, 'w') as f:
                    f.writelines(lines)

                logger.info("Cleared API key from config")
            except Exception as e:
                logger.error(f"Failed to clear API key: {e}")


# Global config instance
config = Config()
