from abc import ABC
from abc import abstractmethod


class BaseAIProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        prompt: str,
    ):
        pass