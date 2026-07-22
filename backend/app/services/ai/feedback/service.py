from app.services.ai.client import AIClient


class AIFeedbackService:

    def __init__(self):

        self.client = AIClient()

    async def improve(
        self,
        text: str,
    ):

        prompt = f"""
Improve this German text.

{text}
"""

        return await self.client.generate(
            prompt,
        )