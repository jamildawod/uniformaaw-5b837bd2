from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Uniforma Backend"
    project_slug: str = "uniforma"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "uniforma"
    db_user: str = "uniforma"
    db_password: str = Field(..., min_length=8)
    db_echo: bool = False

    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_minutes: int = 10080
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_refresh_secret_key: str = Field(..., min_length=32)
    admin_auth_cookie_name: str = "uniforma_admin_access_token"
    admin_refresh_cookie_name: str = "uniforma_admin_refresh_token"
    admin_auth_cookie_domain: str = ".livosys.se"
    admin_auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    default_admin_email: str = "admin@uniforma.app"
    default_admin_password: str = Field(..., min_length=12)

    pim_csv_path: Path = Path("/opt/uniforma/data/PIMexport_catalog_sv-SE.csv")
    pim_csv_delimiter: str = ";"
    pim_batch_size: int = 200
    pim_sync_enabled: bool = True
    pim_sync_cron_hour: int = 2
    pim_sync_cron_minute: int = 0

    ftp_protocol: Literal["ftp", "sftp"] = "sftp"
    ftp_host: str | None = None
    ftp_port: int | None = None
    ftp_username: str | None = None
    ftp_password: str | None = None
    ftp_remote_base_path: str = "/"
    ftp_timeout_seconds: int = 30

    redis_url: str | None = None
    filters_cache_ttl_seconds: int = 300
    auth_login_rate_limit_attempts: int = 5
    auth_login_rate_limit_window_seconds: int = 300
    default_supplier_code: str = "hejco"
    default_supplier_name: str = "Hejco"

    storage_root: Path = Path("/opt/uniforma/storage")
    api_base_url: str = ""  # e.g. http://api.uniforma.livosys.se
    image_download_timeout_seconds: int = 30
    image_max_width: int = 1600
    image_max_height: int = 1600
    image_webp_quality: int = 82

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def alembic_database_uri(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image_storage_root(self) -> Path:
        return self.storage_root / "images"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def uploads_root(self) -> Path:
        return self.storage_root / "uploads"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def product_upload_root(self) -> Path:
        return self.uploads_root / "products"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_auth_cookie_secure(self) -> bool:
        return self.app_env != "development"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_auth_cookie_domain_effective(self) -> str | None:
        return None if self.app_env == "development" else self.admin_auth_cookie_domain


@lru_cache
def get_settings() -> Settings:
    return Settings()
