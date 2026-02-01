from dotenv import load_dotenv
import os


load_dotenv()

TK = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")
ENCODE = "utf-8"
SECRET_KEY = os.getenv("SECRET_KEY").encode(ENCODE)
WEBAPP_URL = os.getenv("WEBAPP_URL")
AI_URL = os.getenv("AI_URL")
AI_GENERATE_ROUTER = os.getenv("AI_GENERATE_ROUTER")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JSON_PROMT_FILENAME = os.getenv("JSON_PROMT_FILENAME")