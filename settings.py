from dotenv import load_dotenv
import os

load_dotenv()

TK = os.getenv("BOT_TOKEN")
FIRST_ID = os.getenv("FIRST_TID")
SEC_ID = os.getenv("SECOND_TID")
IDS_LIST = list(map(int, os.getenv("IDS_LIST").split()))
DB_URL = os.getenv("DB_URL")
ADDQUOTE = "/addquote@telegaanote_bot"