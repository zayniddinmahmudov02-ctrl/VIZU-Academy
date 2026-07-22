from abc import ABC
from abc import abstractmethod


class BaseStorage(ABC):

    @abstractmethod
    async def upload(
        self,
        file,
        path: str,
    ):
        pass

    @abstractmethod
    async def delete(
        self,
        path: str,
    ):
        pass

    @abstractmethod
    def url(
        self,
        path: str,
    ):
        pass