from sqlalchemy.orm import Session

from app.repositories.module import ModuleRepository
from app.schemas.module import ModuleCreate, ModuleUpdate


class ModuleService:

    def __init__(self, db: Session):
        self.repository = ModuleRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, module_id: str):
        return self.repository.get(module_id)

    def create(self, data: ModuleCreate):
        return self.repository.create(data)

    def update(self, module_id: str, data: ModuleUpdate):
        module = self.repository.get(module_id)

        if not module:
            return None

        return self.repository.update(module, data)

    def delete(self, module_id: str):
        module = self.repository.get(module_id)

        if not module:
            return False

        self.repository.delete(module)

        return True