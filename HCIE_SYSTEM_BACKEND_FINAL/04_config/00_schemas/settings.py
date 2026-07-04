"""
HCIE System Configuration
Production-ready settings with environment variable support
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "HCIE Real System V2"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://hcie_user:hcie_password@postgres:5432/hcie",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_max_connections: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_topic_prefix: str = Field(default="hcie", env="KAFKA_TOPIC_PREFIX")
    kafka_consumer_group: str = Field(default="hcie-system", env="KAFKA_CONSUMER_GROUP")
    kafka_auto_offset_reset: str = Field(default="earliest", env="KAFKA_AUTO_OFFSET_RESET")
    
    # HCIE Algorithm Configuration
    default_policy_mode: str = Field(default="hcie", env="DEFAULT_POLICY_MODE")
    hcie_mastery_threshold: float = Field(default=0.45, env="HCIE_MASTERY_THRESHOLD")
    
    # Worker Configuration
    enable_background_workers: bool = Field(default=False, env="ENABLE_BACKGROUND_WORKERS")
    enable_analytics_worker: bool = Field(default=False, env="ENABLE_ANALYTICS_WORKER")
    enable_outbox_processor: bool = Field(default=False, env="ENABLE_OUTBOX_PROCESSOR")
    
    # Deterministic Mode Configuration
    enable_deterministic_mode: bool = Field(default=False, env="ENABLE_DETERMINISTIC_MODE")
    deterministic_seed: int = Field(default=42, env="DETERMINISTIC_SEED")
    deterministic_uuids: bool = Field(default=True, env="DETERMINISTIC_UUIDS")
    deterministic_time: bool = Field(default=True, env="DETERMINISTIC_TIME")
    trajectory_determinism: bool = Field(default=True, env="TRAJECTORY_DETERMINISM")
    
    # Learning Multipliers (Phase 7 calibrated)
    hcie_learning_multiplier: float = Field(default=1.12, env="HCIE_LEARNING_MULTIPLIER")
    dag_learning_multiplier: float = Field(default=1.05, env="DAG_LEARNING_MULTIPLIER")
    random_learning_multiplier: float = Field(default=0.97, env="RANDOM_LEARNING_MULTIPLIER")
    
    # Forgetting Multipliers (Phase 7 calibrated)
    hcie_forgetting_multiplier: float = Field(default=0.8, env="HCIE_FORGETTING_MULTIPLIER")
    dag_forgetting_multiplier: float = Field(default=1.0, env="DAG_FORGETTING_MULTIPLIER")
    random_forgetting_multiplier: float = Field(default=1.2, env="RANDOM_FORGETTING_MULTIPLIER")
    
    # Bandit Configuration
    uncertainty_weight: float = Field(default=0.1, env="UNCERTAINTY_WEIGHT")
    learning_gain_weight: float = Field(default=0.05, env="LEARNING_GAIN_WEIGHT")
    
    # Reward Configuration
    correctness_weight: float = Field(default=0.5, env="CORRECTNESS_WEIGHT")
    speed_weight: float = Field(default=0.3, env="SPEED_WEIGHT")
    difficulty_weight: float = Field(default=0.2, env="DIFFICULTY_WEIGHT")
    time_threshold: float = Field(default=30.0, env="TIME_THRESHOLD")
    
    # Representations
    available_representations: List[str] = Field(
        default=["text", "visual", "interactive", "table"],
        env="AVAILABLE_REPRESENTATIONS"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Security Configuration
    secret_key: str = Field(default="hcie-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Performance Configuration
    request_timeout: float = Field(default=30.0, env="REQUEST_TIMEOUT")
    max_concurrent_requests: int = Field(default=1000, env="MAX_CONCURRENT_REQUESTS")
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Analytics Configuration
    analytics_enabled: bool = Field(default=True, env="ANALYTICS_ENABLED")
    analytics_batch_size: int = Field(default=100, env="ANALYTICS_BATCH_SIZE")
    analytics_flush_interval: int = Field(default=60, env="ANALYTICS_FLUSH_INTERVAL")
    
    # Dataset Configuration
    dataset_path: str = Field(default="data", env="DATASET_PATH")
    max_users_per_dataset: int = Field(default=10000, env="MAX_USERS_PER_DATASET")
    max_interactions_per_user: int = Field(default=100, env="MAX_INTERACTIONS_PER_USER")
    
    # Validation Configuration
    validation_enabled: bool = Field(default=True, env="VALIDATION_ENABLED")
    validation_strict_mode: bool = Field(default=False, env="VALIDATION_STRICT_MODE")
    
    # OpenTelemetry Configuration
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317",  # Use localhost for Windows host access
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_exporter_otlp_protocol: str = Field(default="grpc", env="OTEL_EXPORTER_OTLP_PROTOCOL")

    # Trajectory Recorder Configuration
    enable_trajectory_recording: bool = Field(default=True, env="ENABLE_TRAJECTORY_RECORDING")
    trajectory_batch_size: int = Field(default=100, env="TRAJECTORY_BATCH_SIZE")
    trajectory_flush_interval: int = Field(default=60, env="TRAJECTORY_FLUSH_INTERVAL")

    # Docker-Safe Configuration (Phase 2)
    docker_env: bool = Field(default=False, env="DOCKER_ENV")
    v3_api_base_url: str = Field(default="", env="V3_API_BASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def is_development() -> bool:
    """Check if running in development mode"""
    return settings.debug

def is_production() -> bool:
    """Production-like check (consistent with config.env.is_production_environment).

    Treats docker/staging as production for SECURITY gating, so insecure dev-only fallbacks
    do not silently activate under ENVIRONMENT=docker. Was `not settings.debug`, which disagreed
    with the environment-string detector.
    """
    return str(getattr(settings, "environment", "")).lower() in ("production", "docker", "staging")

# Database configuration helper
def get_database_url() -> str:
    """Get database URL with proper encoding"""
    return settings.database_url

# Redis configuration helper
def get_redis_config() -> dict:
    """Get Redis configuration"""
    return {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "db": settings.redis_db,
        "password": settings.redis_password,
        "max_connections": settings.redis_max_connections,
        "decode_responses": True
    }

# Kafka configuration helper
def get_kafka_config() -> dict:
    """Get Kafka configuration"""
    return {
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "group_id": settings.kafka_consumer_group,
        "auto_offset_reset": settings.kafka_auto_offset_reset,
        "enable_auto_commit": True,
        "auto_commit_interval_ms": 1000
    }
