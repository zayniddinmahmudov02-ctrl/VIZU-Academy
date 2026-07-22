from sqlalchemy.orm import Session

from app.models.module import Module
from app.schemas.module import ModuleCreate, ModuleUpdate


class ModuleRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return (
            self.db.query(Module)
            .order_by(Module.order_index)
            .all()
        )

    def get(self, module_id: str):
        return (
            self.db.query(Module)
            .filter(Module.id == module_id)
            .first()
        )

    def create(self, data: ModuleCreate):
        module = Module(**data.model_dump())

        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)

        return module

    def update(self, module: Module, data: ModuleUpdate):
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(module, key, value)

        self.db.commit()
        self.db.refresh(module)

        return module

    def delete(self, module: Module):
        self.db.delete(module)
        self.db.commit()