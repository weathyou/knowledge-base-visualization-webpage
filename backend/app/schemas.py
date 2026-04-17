from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PlanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str | None
    name: str
    source_doc_path: str
    source_docx_path: str | None
    file_modified_at: datetime | None
    synced_at: datetime
    sync_status: str
    sync_message: str | None
    relative_path: str
    relative_dir: str
    category_path: str
    brigade: str | None
    battalion: str | None
    station: str | None


class PlanDetailItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_name: str
    table_index: int
    row_index: int
    pair_index: int
    key: str
    value: str
    raw_row: str | None


class PlanImageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_name: str
    image_path: str
    doc_media_path: str


class PlanDetailResponse(PlanListItem):
    details: list[PlanDetailItem]
    images: list[PlanImageItem]


class SyncResult(BaseModel):
    scanned: int
    synced: int
    skipped: int
    failed: int
    errors: list[str]


class DocumentTableCell(BaseModel):
    text: str
    colspan: int = 1
    rowspan: int = 1
    table_index: int | None = None
    row_index: int | None = None
    cell_index: int | None = None


class DocumentBlock(BaseModel):
    type: str
    title: str
    rows: list[list[DocumentTableCell]] | None = None
    content: str | None = None
    images: list[PlanImageItem] | None = None


class DocumentPage(BaseModel):
    key: str
    title: str
    parent_key: str | None = None
    blocks: list[DocumentBlock]


class DocumentNavItem(BaseModel):
    key: str
    title: str
    children: list["DocumentNavItem"] | None = None


class PlanDocumentResponse(BaseModel):
    plan_id: int
    plan_name: str
    pages: list[DocumentPage]
    navigation: list[DocumentNavItem]


class UpdateCellRequest(BaseModel):
    table_index: int
    row_index: int
    cell_index: int
    text: str


class CategoryNode(BaseModel):
    name: str
    path: str
    level: int
    children: list["CategoryNode"] = []


class CategoryCreateRequest(BaseModel):
    brigade: str | None = None
    battalion: str | None = None
    station: str | None = None


class PlanMoveRequest(BaseModel):
    target_path: str = ""


class CategoryTreeResponse(BaseModel):
    root: str
    categories: list[CategoryNode]


DocumentNavItem.model_rebuild()
CategoryNode.model_rebuild()
