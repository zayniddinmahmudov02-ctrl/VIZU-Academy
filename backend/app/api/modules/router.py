from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.module import (
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
)
from app.services.module import ModuleService

router = APIRouter(
    prefix="/modules",
    tags=["Modules"],
)


@router.get("", response_model=list[ModuleResponse])
def get_modules(db: Session = Depends(get_db)):
    return ModuleService(db).get_all()


@router.get("/{module_id}", response_model=ModuleResponse)
def get_module(module_id: str, db: Session = Depends(get_db)):
    module = ModuleService(db).get(module_id)

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return module


@router.post("", response_model=ModuleResponse)
def create_module(
    data: ModuleCreate,
    db: Session = Depends(get_db),
):
    return ModuleService(db).create(data)


@router.put("/{module_id}", response_model=ModuleResponse)
def update_module(
    module_id: str,
    data: ModuleUpdate,
    db: Session = Depends(get_db),
):
    module = ModuleService(db).update(module_id, data)

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return module


@router.delete("/{module_id}")
def delete_module(
    module_id: str,
    db: Session = Depends(get_db),
):
    deleted = ModuleService(db).delete(module_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"message": "Module deleted"}