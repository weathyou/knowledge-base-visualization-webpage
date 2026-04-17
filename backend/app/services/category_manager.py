from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import DOCX_CACHE_DIR, SOURCE_DOC_DIR
from ..models import Plan
from ..schemas import CategoryNode, CategoryTreeResponse


def list_doc_files(source_dir: Path | None = None) -> list[Path]:
    source_dir = (source_dir or SOURCE_DOC_DIR).resolve()
    return [
        path
        for path in sorted(source_dir.rglob("*.doc"))
        if path.is_file() and not path.name.startswith("~$")
    ]


def build_category_tree(source_dir: Path | None = None) -> CategoryTreeResponse:
    source_dir = (source_dir or SOURCE_DOC_DIR).resolve()
    tree: dict = {}

    for doc_path in list_doc_files(source_dir):
        relative = doc_path.relative_to(source_dir)
        current = tree
        for depth, part in enumerate(relative.parts[:-1], start=1):
            current = current.setdefault(
                part,
                {"__path__": str(Path(*relative.parts[:depth])), "__children__": {}},
            )["__children__"]

    def to_nodes(children: dict, level: int) -> list[CategoryNode]:
        nodes: list[CategoryNode] = []
        for name in sorted(children):
            item = children[name]
            nodes.append(
                CategoryNode(
                    name=name,
                    path=item["__path__"],
                    level=level,
                    children=to_nodes(item["__children__"], level + 1),
                )
            )
        return nodes

    return CategoryTreeResponse(root=str(source_dir), categories=to_nodes(tree, 1))


def ensure_category_folders(brigade: str | None, battalion: str | None, station: str | None) -> Path:
    parts = [part.strip() for part in [brigade, battalion, station] if part and part.strip()]
    target_dir = SOURCE_DOC_DIR.joinpath(*parts)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def move_plan_to_category(session: Session, plan_id: int, target_path: str) -> Plan:
    plan = session.query(Plan).filter(Plan.id == plan_id).one()
    source = Path(plan.source_doc_path).resolve()
    target_dir = SOURCE_DOC_DIR.joinpath(target_path).resolve() if target_path else SOURCE_DOC_DIR.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path_obj = target_dir / source.name

    if source == target_path_obj:
      return plan

    if target_path_obj.exists():
        raise FileExistsError(f"目标位置已存在同名文件: {target_path_obj.name}")

    shutil.move(str(source), str(target_path_obj))

    cached_docx = DOCX_CACHE_DIR / f"{source.stem}.docx"
    if cached_docx.exists():
        cached_docx.unlink()

    plan.source_doc_path = str(target_path_obj)
    plan.source_docx_path = None
    plan.file_modified_at = None
    plan.synced_at = plan.synced_at
    session.commit()
    return plan
