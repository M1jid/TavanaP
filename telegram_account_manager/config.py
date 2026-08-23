from dotenv import load_dotenv
import os


load_dotenv()


PROXY_HOST = os.getenv("PROXY_HOST", None)
PROXY_PORT = int(os.getenv("PROXY_PORT", None))
PROXY_PROTOCOL = os.getenv("PROXY_PROTOCOL", None)
SESSION_PATH = os.getenv('TELEGRAM_SESSION_PATH')
