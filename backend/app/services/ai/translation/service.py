from app.services.ai.client import AIClient


class AITranslationService:

    def __init__(self):

        self.client = AIClient()

    async def translate(
        self,
        text: str,
        language: str,
    ):

        prompt = f"""
Translate into {language}

{text}
"""

        return await self.client.generate(
            prompt,
        )