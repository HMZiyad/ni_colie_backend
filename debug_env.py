import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

print(f"DATABASE_URL: {env('DATABASE_URL')}")
print(f"Parsed DB Config: {env.db()}")
