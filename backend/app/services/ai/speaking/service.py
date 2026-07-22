from app.services.ai.client import AIClient


class AISpeakingService:

    def __init__(self):

        self.client = AIClient()

    async def evaluate(
        self,
        transcript: str,
    ):

        prompt = f"""
Evaluate German speaking.

{transcript}
"""

        return await self.client.generate(
            prompt,
        )