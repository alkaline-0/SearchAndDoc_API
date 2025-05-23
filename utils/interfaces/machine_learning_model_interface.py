from abc import ABC, abstractmethod
from logging import Logger

from services.config.config import MachineLearningModelConfig


class MachineLearningModelInterface(ABC):
    @abstractmethod
    def __init__(self, cfg: MachineLearningModelConfig):
        pass

    @abstractmethod
    async def create(self, messages, logger: Logger):
        pass
