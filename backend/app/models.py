from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import SOURCE_DOC_DIR
from .database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source_doc_path: Mapped[str] = mapped_column(String(1024), unique=True)
    source_docx_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_modified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sync_status: Mapped[str] = mapped_column(String(32), default="success")
    sync_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_version: Mapped[int] = mapped_column(Integer, default=1)
    content_source_mode: Mapped[str] = mapped_column(String(32), default="database")

    details: Mapped[list["PlanDetail"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanDetail.id",
    )
    images: Mapped[list["PlanImage"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanImage.id",
    )
    pages: Mapped[list["PlanPage"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanPage.sort_order",
    )

    @property
    def relative_path(self) -> str:
        try:
            return str(Path(self.source_doc_path).resolve().relative_to(SOURCE_DOC_DIR.resolve()))
        except Exception:
            return Path(self.source_doc_path).name

    @property
    def relative_dir(self) -> str:
        relative = Path(self.relative_path)
        return "" if str(relative.parent) == "." else str(relative.parent)

    @property
    def category_parts(self) -> list[str]:
        return [part for part in Path(self.relative_dir).parts if part not in ("", ".")]

    @property
    def brigade(self) -> str | None:
        return self.category_parts[0] if len(self.category_parts) >= 1 else None

    @property
    def battalion(self) -> str | None:
        return self.category_parts[1] if len(self.category_parts) >= 2 else None

    @property
    def station(self) -> str | None:
        return self.category_parts[2] if len(self.category_parts) >= 3 else None

    @property
    def category_path(self) -> str:
        return " / ".join(self.category_parts)


class PlanDetail(Base):
    __tablename__ = "plan_details"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "table_index",
            "row_index",
            "pair_index",
            "key",
            "value",
            name="uq_plan_detail_position",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    section_name: Mapped[str] = mapped_column(String(255), default="其他信息")
    table_index: Mapped[int] = mapped_column(Integer)
    row_index: Mapped[int] = mapped_column(Integer)
    pair_index: Mapped[int] = mapped_column(Integer, default=0)
    key: Mapped[str] = mapped_column(String(512))
    value: Mapped[str] = mapped_column(Text)
    raw_row: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["Plan"] = relationship(back_populates="details")


class PlanImage(Base):
    __tablename__ = "plan_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    image_name: Mapped[str] = mapped_column(String(255))
    image_path: Mapped[str] = mapped_column(String(1024))
    doc_media_path: Mapped[str] = mapped_column(String(255))

    plan: Mapped["Plan"] = relationship(back_populates="images")


class PlanPage(Base):
    __tablename__ = "plan_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(255))
    parent_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    plan: Mapped["Plan"] = relationship(back_populates="pages")
    blocks: Mapped[list["PlanBlock"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="PlanBlock.sort_order",
    )


class PlanBlock(Base):
    __tablename__ = "plan_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("plan_pages.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    page: Mapped["PlanPage"] = relationship(back_populates="blocks")
    cells: Mapped[list["PlanBlockCell"]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="PlanBlockCell.row_index, PlanBlockCell.cell_order",
    )
    images: Mapped[list["PlanBlockImage"]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="PlanBlockImage.sort_order",
    )


class PlanBlockCell(Base):
    __tablename__ = "plan_block_cells"
    __table_args__ = (
        UniqueConstraint("block_id", "row_index", "cell_order", name="uq_plan_block_cell_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("plan_blocks.id", ondelete="CASCADE"), index=True)
    row_index: Mapped[int] = mapped_column(Integer)
    cell_order: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")
    colspan: Mapped[int] = mapped_column(Integer, default=1)
    rowspan: Mapped[int] = mapped_column(Integer, default=1)
    table_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_cell_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_editable: Mapped[int] = mapped_column(Integer, default=0)

    block: Mapped["PlanBlock"] = relationship(back_populates="cells")


class PlanBlockImage(Base):
    __tablename__ = "plan_block_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("plan_blocks.id", ondelete="CASCADE"), index=True)
    image_name: Mapped[str] = mapped_column(String(255))
    image_path: Mapped[str] = mapped_column(String(1024))
    doc_media_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    block: Mapped["PlanBlock"] = relationship(back_populates="images")
