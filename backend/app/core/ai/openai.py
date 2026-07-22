from app.core.ai.base import BaseAIProvider


class OpenAIProvider(BaseAIProvider):

    async def generate(
        self,
        prompt: str,
    ):

        raise NotImplementedError