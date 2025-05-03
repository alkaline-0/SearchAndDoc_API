import json

from services.interfaces.create_documentation_content_service_interface import (
    CreateDocumentationContentServiceInterface,
)
from services.interfaces.machine_learning_model_interface import (
    MachineLearningModelInterface,
)


class CreateDocumentationContentService(CreateDocumentationContentServiceInterface):
    def __init__(self, ml_client: MachineLearningModelInterface) -> None:
        self._ml_client = ml_client

    async def create_document_content_from_messages(
        self, documents: list[str], server_id: str
    ) -> list[str]:
        records = json.dumps(documents, indent=2)
        messages = [
            {
                "role": "system",
                "content": """You are a helpful and knowledgeable team member in a software development team. Your role is to create clear, accurate, detailed and well-structured README.md about the project and its development process, using only the relevant technical content shared between team members in chat channels. Please organize the documentation logically (for example: Overview, Requirements, Architecture, Implementation Details, Development process etc.), and ensure it is suitable for other developers who may join the project. Ignore any off-topic or non-technical messages and make sure you are as detailed as possible.""",
            },
            {
                "role": "user",
                "content": f"""Create a clear, detailed and well-structured README.md about the project mentioned in the chat messages by rephrasing and organizing the information from the message_content fields of Discord chat messages. Rephrase the technical discussions into coherent sections made of paragraphs which are as detailed as possible (such as Overview, Features, Implementation Details, Project process and Next Steps). Ensure the document is suitable for developers who may join the project in the future. Given a Discord server with the name {server_id} and the following records: {records}. For each point or section in the README, include a reference or link to the original Discord message using its message_id, channel_id, and server name. Where possible, format these references as Discord message links in the form: https://discord.com/channels/<server_id>/<channel_id>/<message_id>. Exclude any off-topic messages.
                  After you are done reiterate on the document to make sure it's well written detailed and covers all the relevant points.
                  """,
            },
        ]

        return await self._ml_client.create(messages)
