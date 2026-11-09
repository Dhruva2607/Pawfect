"""
Application configuration — loads environment variables from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# [FROM MARKDOWN] Google Gemini API key for gemini-1.5-flash and text-embedding-004
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# [FROM MARKDOWN] MongoDB Atlas connection string
MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

# Database name — [ASSUMPTION] not specified in markdown, using project name
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "pawfect")
