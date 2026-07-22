class BaseService:

    def __init__(
        self,
        repository,
    ):
        self.repository = repository

    def get(self, object_id):

        return self.repository.get(object_id)

    def get_all(self):

        return self.repository.get_all()

    def create(
        self,
        data,
    ):

        return self.repository.create(data)

    def update(
        self,
        object_id,
        data,
    ):

        obj = self.repository.get(object_id)

        if not obj:
            return None

        return self.repository.update(
            obj,
            data,
        )

    def delete(
        self,
        object_id,
    ):

        obj = self.repository.get(object_id)

        if not obj:
            return False

        self.repository.delete(obj)

        return True