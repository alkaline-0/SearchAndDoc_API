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
                "content": """You are a helpful and knowledgeable team member in a software development team. Your role is to create clear, accurate, and well-structured documentation about the project and its development process, using only the relevant technical content shared between team members in chat channels. Please organize the documentation logically (for example: Overview, Requirements, Architecture, Implementation Details, Development process etc.), and ensure it is suitable for other developers who may join the project. Ignore any off-topic or non-technical messages.""",
            },
            {
                "role": "user",
                "content": f"""Create a clear and well-structured document about the project mentioned in the chat messages by synthesizing, rephrasing and organizing the information from the message_content fields of Discord chat messages. Rephrase the technical discussions into coherent sections (such as Overview, Features, Implementation Details, Project process and Next Steps). Ensure the document is suitable for developers who may join the project in the future. Given a Discord server with the name {server_id} and the following records: {records}. For each point or section in the document, include a reference or link to the original Discord message using its message_id, channel_id, and server name. Where possible, format these references as Discord message links in the form: https://discord.com/channels/<server_id>/<channel_id>/<message_id>. Exclude any off-topic or non-technical messages, and ensure the document is suitable for developers joining the project.""",
            },
        ]

        return await self._ml_client.create(messages)

    async def finalize_document(
        self, records: list[dict], topic: str, document: list[str]
    ) -> list[str]:
        discord_messages = json.dumps(records, indent=2)
        ai_result = json.dumps(document, indent=2)
        messages = [
            {
                "role": "system",
                "content": """You are a helpful and knowledgeable team member in a software development team. Your role is to create clear, accurate, and well-structured documentation about the project and its development process, using only the relevant technical content shared between team members in chat channels. Please organize the documentation logically (for example: Overview, Requirements, Architecture, Implementation Details, Development process etc.), and ensure it is suitable for other developers who may join the project. Ignore any off-topic or non-technical messages.""",
            },
            {
                "role": "user",
                "content": f"""Given this document: {ai_result}, check that it covers all relevant details about {topic} as found in the provided {discord_messages} (a list of Discord messages). If you find any important information about {topic} in {discord_messages} that is not already in the document, update the technical document to include it. Make sure the final document is accurate and complete regarding {topic}. These versions are concise, clear, and provide explicit instructions for both content creation and validation, while ensuring technical traceability and relevance.""",
            },
        ]
        
        res = await self._ml_client.create(messages)
        print(res, flush=True)
        return res
