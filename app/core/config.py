"""应用配置管理。

项目配置统一通过环境变量注入，避免把数据库密码、模型密钥等敏感信息
直接写在代码中。Pydantic Settings 会负责读取和校验配置。
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """RentFlow AI 应用配置。

    字段的默认值适合本地开发。生产环境可以通过环境变量覆盖，
    例如将 APP_DEBUG 设置为 false。
    """

    model_config = SettingsConfigDict(
        # 本地开发时自动读取项目根目录中的 .env。
        env_file=".env",
        env_file_encoding="utf-8",
        # 环境变量统一使用 APP_ 前缀，避免与系统变量发生名称冲突。
        env_prefix="APP_",
        # 环境变量名称不区分大小写。
        case_sensitive=False,
        # 暂时忽略 .env 中尚未定义的字段，便于后续逐步增加配置。
        extra="ignore",
    )

    name: str = "RentFlow AI API"
    version: str = "0.1.0"
    description: str = "企业级智能租赁 Agent 平台后端服务"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    database_url: str = (
        "postgresql+asyncpg://rentflow:rentflow_dev_password@127.0.0.1:5432/rentflow"
    )

    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    deepseek_timeout_seconds: float = 30.0
    deepseek_max_tokens: int = 1_000


@lru_cache
def get_settings() -> Settings:
    """返回应用配置单例。

    配置对象在进程生命周期内只创建一次，避免每个请求都重复读取
    和解析环境变量。测试时可以通过 get_settings.cache_clear() 清除缓存。
    """
    return Settings()
