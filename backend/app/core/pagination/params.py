from fastapi import Query


class Pagination:

    def __init__(

        self,

        page: int = Query(
            1,
            ge=1,
        ),

        size: int = Query(
            20,
            ge=1,
            le=100,
        ),
    ):

        self.page = page

        self.size = size

    @property
    def offset(self):

        return (
            self.page - 1
        ) * self.size