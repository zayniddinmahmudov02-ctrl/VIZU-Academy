from app.core.ai import AIProviderFactory


class AIClient:

    def __init__(
        self,
        provider: str = "openai",
    ):

        self.provider = (
            AIProviderFactory.create(
                provider,
            )
        )

    async def generate(
        self,
        prompt: str,
    ):

        return await self.provider.generate(
            prompt,
        )