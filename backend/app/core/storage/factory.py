from app.core.storage.local import LocalStorage


class StorageFactory:

    @staticmethod
    def create(
        provider: str,
    ):

        if provider == "local":
            return LocalStorage()

        raise ValueError(
            "Unsupported Storage Provider"
        )