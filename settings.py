from dotenv import load_dotenv
import os

load_dotenv()

TK = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")
ADDQUOTE = "/addquote@telegaanote_bot"
DELETE = "/delete@telegaanote_bot"