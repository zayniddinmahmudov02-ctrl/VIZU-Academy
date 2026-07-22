from app.core.ai.openai import OpenAIProvider


class AIProviderFactory:

    @staticmethod
    def create(
        provider: str,
    ):

        if provider == "openai":
            return OpenAIProvider()

        raise ValueError(
            "Unsupported AI Provider"
        )