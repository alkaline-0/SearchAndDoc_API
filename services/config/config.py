import os

from dotenv import load_dotenv

load_dotenv()


class MachineLearningModelConfig:
    MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.5
    MAX_COMPLETION_TOKEN = 1024
    TOP_P = 1
    STOP = None
    STREAM = False
    API_TOKEN: str = os.getenv("GROQ_API_KEY")
