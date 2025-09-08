from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class Settings:
    telegram_token: str
    gemini_api_key: str
    removebg_api_key: str
    huggingface_api_key: str
    tavily_api_key: str
    fish_audio_api_key: str

    gemini_model_name: str = "gemini-1.0-pro"

    @classmethod
    def load_from_env(cls):
        load_dotenv()
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            removebg_api_key=os.getenv("REMOVEBG_API_KEY"),
            huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            fish_audio_api_key=os.getenv("FISH_AUDIO_API_KEY"),
        )
