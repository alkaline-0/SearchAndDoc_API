from abc import ABC, abstractmethod

from services.config.config import MachineLearningModelConfig


class MachineLearningModelInterface(ABC):
    @abstractmethod
    def __init__(self, cfg: MachineLearningModelConfig):
      pass
    @abstractmethod
    async def create(messages):
      pass
        
