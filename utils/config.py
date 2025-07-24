import os
from typing import Optional

from pydantic import PostgresDsn
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


env = find_config()



if __name__ == "__main__":
    print(env)