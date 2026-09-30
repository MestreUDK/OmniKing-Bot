import os
from pathlib import Path
from dotenv import load_dotenv
from kingcore.settings import Settings

APP_NAME = "OmniKing"

def load_settings():
    load_dotenv(Path(__file__).resolve().with_name(".env"), override=False)
    return Settings.from_env(APP_NAME, os.environ)
