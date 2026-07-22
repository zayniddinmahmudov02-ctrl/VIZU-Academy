from app.services.ai.client import AIClient


class AIWritingService:

    def __init__(self):

        self.client = AIClient()

    async def check(
        self,
        text: str,
    ):

        prompt = f"""
You are a German writing examiner.

Evaluate this text.

{text}
"""

        return await self.client.generate(
            prompt,
        )