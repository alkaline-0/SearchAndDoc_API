from logging import Logger

from groq import AsyncGroq

from services.config.config import MachineLearningModelConfig
from utils.interfaces.machine_learning_model_interface import (
    MachineLearningModelInterface,
)


class AsyncGroqModel(MachineLearningModelInterface):
    def __init__(self, cfg: MachineLearningModelConfig) -> None:
        self._model = AsyncGroq(api_key=cfg.API_TOKEN)
        self._cfg = cfg

    async def create(self, messages, logger: Logger):
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
            logger.info("Created README successfully.")
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(e, exc_info=True, stack_info=True)
            raise e
