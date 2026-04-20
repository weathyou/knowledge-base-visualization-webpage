from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Plan, PlanBlock, PlanBlockCell, PlanPage
from ..schemas import SyncResult


class DocEditError(RuntimeError):
    pass


def update_plan_cell(session: Session, plan_id: int, block_id: int, row_index: int, cell_order: int, text: str) -> SyncResult:
    plan = session.query(Plan).filter(Plan.id == plan_id).one_or_none()
    if plan is None:
        raise DocEditError("预案不存在")

    cell = (
        session.query(PlanBlockCell)
        .join(PlanBlock, PlanBlock.id == PlanBlockCell.block_id)
        .join(PlanPage, PlanPage.id == PlanBlock.page_id)
        .join(Plan, Plan.id == PlanPage.plan_id)
        .filter(
            Plan.id == plan_id,
            PlanBlockCell.block_id == block_id,
            PlanBlockCell.row_index == row_index,
            PlanBlockCell.cell_order == cell_order,
        )
        .one_or_none()
    )
    if cell is None:
        raise DocEditError("目标单元格不存在")
    if not cell.is_editable:
        raise DocEditError("当前单元格不允许编辑")

    cell.text = str(text)
    plan.synced_at = datetime.utcnow()
    plan.sync_status = "success"
    plan.sync_message = "数据库主存已更新"
    plan.content_version = (plan.content_version or 0) + 1
    session.commit()

    return SyncResult(scanned=0, synced=1, skipped=0, failed=0, errors=[])
