import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    ENV: str = "local"
    NAMESPACE: str = "local"
    SERVICE_NAME: str = "search-agent"
    SERVICE_VERSION: str = "service-version"

    LLM_API_KEY: str
    LLM_BASE_URL: str
    LLM_NAME: str = "gpt-4o"

    EXA_API_KEY: str
    TAVILY_API_KEY: str
    FINANCIAL_API_KEY: str
    ALPHAVANTAGE_API_KEY: str

class LocalDevSettings(EnvSettings):

    model_config = SettingsConfigDict(env_file="config")


class DeployedSettings(EnvSettings):
    # takes in env vars from the pod
    ...


def find_config() -> EnvSettings:
    if os.getenv("ENV"):
        return DeployedSettings()
    else:
        return LocalDevSettings()


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup centralized logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()  # Console output
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    
    # Create main logger
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")


env = find_config()

# Setup logging when config is imported
setup_logging()

if __name__ == "__main__":
    print(env)