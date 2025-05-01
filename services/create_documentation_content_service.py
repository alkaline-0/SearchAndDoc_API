import json

from groq import AsyncGroq

from services.config.groq_config import GroqConfig
from services.interfaces.create_documentation_content_service_interface import (
    CreateDocumentationContentServiceInterface,
)


class CreateDocumentationContentService(CreateDocumentationContentServiceInterface):
    def __init__(self, groq_client: AsyncGroq, groq_config: GroqConfig) -> None:
        self._groq_client = groq_client
        self._groq_config = groq_config

    async def create_document_content_from_messages(
        self, documents: list[str], server_id: str
    ) -> list[str]:
        records = json.dumps(documents, indent=2)

        stream = await self._groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": self._groq_config.ROLE_CONTET},
                {
                    "role": "user",
                    "content": f"""Create a clear and well-structured technical document by synthesizing and organizing the information from the message_content fields of Discord chat messages. Summarize and rephrase the technical discussions into coherent sections (such as Overview, Features, Implementation Details, and Next Steps). Ensure the document is suitable for developers who may join the project in the future. Given a discord server with the name {server_id} and those {records}
                  For each point or section in the document, include a reference or link to the original Discord message using its message_id, channel_id, and server name. Where possible, format these references as Discord message links in the form: https://discord.com/channels/<server_id>/<channel_id>/<message_id>). Exclude any off-topic or non-technical messages, and ensure the document is suitable for developers joining the project
                """,
                },
            ],
            model=self._groq_config.MODEL,
            temperature=self._groq_config.TEMPERATURE,
            max_completion_tokens=self._groq_config.MAX_COMPLETION_TOKEN,
            top_p=self._groq_config.TOP_P,
            stop=self._groq_config.STOP,
            stream=self._groq_config.STREAM,
        )

        results_of_first_iteration = []
        async for chunk in stream:
            results_of_first_iteration.append(chunk.choices[0].delta.content, end="")

        return results_of_first_iteration

    async def finalize_document(self, records: list[dict], topic: str) -> list[str]:
        server_documents = json.dumps(records, indent=2)

        stream = await self._groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": self._groq_config.ROLE_CONTET},
                {
                    "role": "user",
                    "content": f"""Given the technical document below, check that it covers all relevant details about {topic} as found in the provided {server_documents} (a list of Discord messages). If you find any important information about {topic} in {server_documents} that is not already in the document, update the technical document to include it. Make sure the final document is accurate and complete regarding {topic}
                """,
                },
            ],
            model=self._groq_config.MODEL,
            temperature=self._groq_config.TEMPERATURE,
            max_completion_tokens=self._groq_config.MAX_COMPLETION_TOKEN,
            top_p=self._groq_config.TOP_P,
            stop=self._groq_config.STOP,
            stream=self._groq_config.STREAM,
        )

        finalized_document = []
        async for chunk in stream:
            finalized_document.append(chunk.choices[0].delta.content, end="")

        return finalized_document
