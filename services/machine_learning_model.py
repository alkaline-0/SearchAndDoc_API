from groq import APIError, AsyncGroq

from services.config.config import MachineLearningModelConfig
from services.interfaces.machine_learning_model_interface import (
    MachineLearningModelInterface,
)


class MachineLearningApiException(APIError):
    """Raised when validation fails."""


class AsyncGroqModel(MachineLearningModelInterface):
    def __init__(self, cfg: MachineLearningModelConfig) -> None:
        self._model = AsyncGroq(api_key=cfg.API_TOKEN)
        self._cfg = cfg

    async def create(self, messages):
        try:
            chat_completion = await self._model.chat.completions.create(
                messages=messages,
                model=self._cfg.MODEL,
                temperature=self._cfg.TEMPERATURE,
                max_completion_tokens=self._cfg.MAX_COMPLETION_TOKEN,
                top_p=self._cfg.TOP_P,
                stop=self._cfg.STOP,
                stream=self._cfg.STREAM,
            )
            return chat_completion.choices[0].message.content
        except MachineLearningApiException as e:
            raise e
