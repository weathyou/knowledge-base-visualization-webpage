from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .database import get_db
from .models import Plan
from .schemas import (
    CategoryCreateRequest,
    CategoryTreeResponse,
    PlanDetailResponse,
    PlanDocumentResponse,
    PlanListItem,
    PlanMoveRequest,
    SyncResult,
    UpdateCellRequest,
)
from .services.category_manager import build_category_tree, ensure_category_folders, move_plan_to_category
from .services.doc_editor import DocEditError, update_plan_cell
from .services.document_view import build_plan_document
from .services.sync import sync_plan_directory, sync_single_plan


router = APIRouter(prefix="/api", tags=["plans"])


@router.get("/plans", response_model=list[PlanListItem])
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).order_by(Plan.code.asc().nullslast(), Plan.name.asc()).all()


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = (
        db.query(Plan)
        .options(selectinload(Plan.details), selectinload(Plan.images))
        .filter(Plan.id == plan_id)
        .one_or_none()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/plans/{plan_id}/document", response_model=PlanDocumentResponse)
def get_plan_document(plan_id: int, db: Session = Depends(get_db)):
    try:
        return build_plan_document(db, plan_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sync", response_model=SyncResult)
def sync_plans(db: Session = Depends(get_db)):
    return sync_plan_directory(db)


@router.get("/categories", response_model=CategoryTreeResponse)
def get_categories():
    return build_category_tree()


@router.post("/categories", response_model=dict)
def create_category_folders(payload: CategoryCreateRequest):
    target = ensure_category_folders(payload.brigade, payload.battalion, payload.station)
    return {"created": str(target)}


@router.post("/plans/{plan_id}/move", response_model=PlanListItem)
def move_plan(plan_id: int, payload: PlanMoveRequest, db: Session = Depends(get_db)):
    try:
        plan = move_plan_to_category(db, plan_id, payload.target_path)
        sync_single_plan(db, Path(plan.source_doc_path))
        db.refresh(plan)
        return plan
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/plans/{plan_id}/document/cell", response_model=SyncResult)
def update_document_cell(plan_id: int, payload: UpdateCellRequest, db: Session = Depends(get_db)):
    try:
        return update_plan_cell(
            db,
            plan_id=plan_id,
            table_index=payload.table_index,
            row_index=payload.row_index,
            cell_index=payload.cell_index,
            text=payload.text,
        )
    except DocEditError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
