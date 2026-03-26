from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": ""}

    # Core
    database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # AI
    anthropic_api_key: str = ""

    # Video
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    remotion_function_name: str = ""
    remotion_serve_url: str = ""

    # Audio
    elevenlabs_api_key: str = ""
    elevenlabs_default_voice_id: str = ""

    # Analytics
    rudderstack_write_key: str = ""
    rudderstack_data_plane_url: str = ""

    # Auth
    api_key_salt: str = ""
    jwt_secret: str = ""

    # Optional
    lob_api_key: str = ""


settings = Settings()
