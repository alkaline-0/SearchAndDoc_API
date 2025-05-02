import os

from dotenv import load_dotenv

load_dotenv()


class GroqConfig:
    MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.5
    MAX_COMPLETION_TOKEN = 1024
    TOP_P = 1
    STOP = None
    STREAM = True
    ROLE_CONTET = """You are a helpful and knowledgeable team member in a software development team. Your role is to create clear, accurate, and well-structured documentation about the project and its development process, using only the relevant technical content shared between team members in chat channels. Please organize the documentation logically (for example: Overview, Requirements, Architecture, Implementation Details, Development process etc.), and ensure it is suitable for other developers who may join the project. Ignore any off-topic or non-technical messages."""
    API_TOKEN: str = os.getenv("GROQ_API_KEY")
