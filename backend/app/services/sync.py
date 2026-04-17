from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import SOURCE_DOC_DIR
from ..models import Plan, PlanDetail, PlanImage
from ..schemas import SyncResult
from .category_manager import list_doc_files
from .doc_converter import DocConversionError, convert_doc_to_docx
from .parser import parse_plan_docx


def _upsert_plan(session: Session, source_doc: Path) -> Plan:
    plan = session.query(Plan).filter(Plan.source_doc_path == str(source_doc)).one_or_none()
    if plan is None:
        plan = Plan(name=source_doc.stem, source_doc_path=str(source_doc))
        session.add(plan)
        session.flush()
    return plan


def remove_missing_plans(session: Session, source_dir: Path | None = None) -> int:
    source_dir = (source_dir or SOURCE_DOC_DIR).resolve()
    removed = 0
    for plan in session.query(Plan).all():
        path = Path(plan.source_doc_path)
        try:
            inside_root = path.resolve().is_relative_to(source_dir)
        except Exception:
            try:
                path.resolve().relative_to(source_dir)
                inside_root = True
            except Exception:
                inside_root = False
        if inside_root and not path.exists():
            session.delete(plan)
            removed += 1
    if removed:
        session.commit()
    return removed


def sync_plan_directory(session: Session, source_dir: Path | None = None) -> SyncResult:
    source_dir = source_dir or SOURCE_DOC_DIR
    remove_missing_plans(session, source_dir)
    docs = list_doc_files(source_dir)

    scanned = len(docs)
    synced = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    for doc_path in docs:
        modified_at = datetime.fromtimestamp(doc_path.stat().st_mtime)
        plan = _upsert_plan(session, doc_path.resolve())
        if (
            plan.file_modified_at
            and plan.file_modified_at >= modified_at
            and plan.sync_status == "success"
        ):
            skipped += 1
            continue

        try:
            docx_path = convert_doc_to_docx(doc_path)
            parsed = parse_plan_docx(docx_path)

            plan.code = parsed.code
            plan.name = parsed.name
            plan.source_docx_path = str(docx_path)
            plan.file_modified_at = modified_at
            plan.synced_at = datetime.utcnow()
            plan.sync_status = "success"
            plan.sync_message = None

            session.query(PlanDetail).filter(PlanDetail.plan_id == plan.id).delete()
            session.query(PlanImage).filter(PlanImage.plan_id == plan.id).delete()

            for item in parsed.details:
                session.add(
                    PlanDetail(
                        plan_id=plan.id,
                        section_name=item.section_name,
                        table_index=item.table_index,
                        row_index=item.row_index,
                        pair_index=item.pair_index,
                        key=item.key,
                        value=item.value,
                        raw_row=item.raw_row,
                    )
                )

            for image in parsed.images:
                session.add(
                    PlanImage(
                        plan_id=plan.id,
                        image_name=image.image_name,
                        image_path=image.image_path,
                        doc_media_path=image.doc_media_path,
                    )
                )

            synced += 1
            session.commit()
        except (DocConversionError, Exception) as exc:
            failed += 1
            session.rollback()
            plan = _upsert_plan(session, doc_path.resolve())
            plan.file_modified_at = modified_at
            plan.synced_at = datetime.utcnow()
            plan.sync_status = "failed"
            plan.sync_message = str(exc)
            session.commit()
            errors.append(f"{doc_path.name}: {exc}")

    return SyncResult(
        scanned=scanned,
        synced=synced,
        skipped=skipped,
        failed=failed,
        errors=errors,
    )


def sync_single_plan(session: Session, doc_path: Path) -> SyncResult:
    source_dir = doc_path.parent
    docs = [doc_path.resolve()]
    scanned = len(docs)
    synced = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    for doc_path in docs:
        modified_at = datetime.fromtimestamp(doc_path.stat().st_mtime)
        plan = _upsert_plan(session, doc_path.resolve())
        try:
            docx_path = convert_doc_to_docx(doc_path)
            parsed = parse_plan_docx(docx_path)

            plan.code = parsed.code
            plan.name = parsed.name
            plan.source_docx_path = str(docx_path)
            plan.file_modified_at = modified_at
            plan.synced_at = datetime.utcnow()
            plan.sync_status = "success"
            plan.sync_message = None

            session.query(PlanDetail).filter(PlanDetail.plan_id == plan.id).delete()
            session.query(PlanImage).filter(PlanImage.plan_id == plan.id).delete()

            for item in parsed.details:
                session.add(
                    PlanDetail(
                        plan_id=plan.id,
                        section_name=item.section_name,
                        table_index=item.table_index,
                        row_index=item.row_index,
                        pair_index=item.pair_index,
                        key=item.key,
                        value=item.value,
                        raw_row=item.raw_row,
                    )
                )
            for image in parsed.images:
                session.add(
                    PlanImage(
                        plan_id=plan.id,
                        image_name=image.image_name,
                        image_path=image.image_path,
                        doc_media_path=image.doc_media_path,
                    )
                )
            synced += 1
            session.commit()
        except (DocConversionError, Exception) as exc:
            failed += 1
            session.rollback()
            plan = _upsert_plan(session, doc_path.resolve())
            plan.file_modified_at = modified_at
            plan.synced_at = datetime.utcnow()
            plan.sync_status = "failed"
            plan.sync_message = str(exc)
            session.commit()
            errors.append(f"{doc_path.name}: {exc}")

    return SyncResult(scanned=scanned, synced=synced, skipped=skipped, failed=failed, errors=errors)
