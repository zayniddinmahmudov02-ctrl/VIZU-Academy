from app.services.ai.client import AIClient


class AIChatService:

    def __init__(self):

        self.client = AIClient()

    async def ask(
        self,
        message: str,
    ):

        return await self.client.generate(
            message,
        )