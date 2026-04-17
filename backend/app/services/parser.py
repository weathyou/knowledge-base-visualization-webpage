from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from docx import Document

from ..config import IMAGES_DIR


SECTION_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("基本情况", ("单位名称", "建筑高度", "建筑面积", "使用性质", "地址", "消防安全责任人", "重点单位")),
    ("重点部位", ("重点部位", "部位名称", "重点区域", "重点岗位")),
    ("风险评估", ("危险性", "火灾危险", "风险", "危险源", "爆炸", "储罐", "仓库", "可燃", "处置对策", "灾情假设")),
    ("力量编成", ("力量编成", "第一出动", "增援力量", "联动单位", "消防救援站", "专职消防队")),
    ("疏散救人", ("人员总数", "疏散", "避难", "被困", "救人", "医护")),
    ("消防设施", ("消火栓", "喷淋", "报警系统", "消防控制室", "消防电梯", "防排烟", "灭火器")),
    ("水源部署", ("水源", "天然水源", "市政消火栓", "取水口", "水池", "水鹤")),
    ("平面图纸", ("平面图", "分布图", "部署图", "示意图")),
]


@dataclass
class ParsedKV:
    section_name: str
    table_index: int
    row_index: int
    pair_index: int
    key: str
    value: str
    raw_row: str


@dataclass
class ParsedImage:
    image_name: str
    image_path: str
    doc_media_path: str


@dataclass
class ParsedPlan:
    name: str
    code: str | None
    details: list[ParsedKV]
    images: list[ParsedImage]


def normalize_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value.replace("\x07", " ")).strip()
    return value.strip("：: ")


def infer_section_name(key: str, row_text: str) -> str:
    haystack = f"{key} {row_text}"
    for section_name, keywords in SECTION_PATTERNS:
        if any(keyword in haystack for keyword in keywords):
            return section_name
    return "其他信息"


def compact_row_cells(cells: list[str]) -> list[str]:
    compacted: list[str] = []
    for cell in cells:
        if not cell:
            continue
        if compacted and compacted[-1] == cell:
            continue
        compacted.append(cell)
    return compacted


def looks_like_row_prefix(value: str) -> bool:
    prefix_keywords = (
        "基本情况",
        "单位基本",
        "内部",
        "消防设施",
        "消防水源",
        "重点部位",
        "力量编成",
        "风险评估",
        "平面图",
        "部署",
        "编成",
    )
    return any(keyword in value for keyword in prefix_keywords)


def is_generic_subkey(value: str) -> bool:
    generic_keywords = (
        "位置",
        "数量",
        "流量",
        "扬程",
        "总容量",
        "补给",
        "方式",
        "容量",
        "分布",
    )
    return any(keyword in value for keyword in generic_keywords)


def is_directional_value(value: str) -> bool:
    return bool(re.match(r"^[东西南北][:：]", value))


def parse_table_kv_pairs(document: Document) -> list[ParsedKV]:
    results: list[ParsedKV] = []
    for table_index, table in enumerate(document.tables):
        pending_single_label: str | None = None
        try:
            for row_index, row in enumerate(table.rows):
                original_cells = [normalize_text(cell.text) for cell in row.cells]
                cells = compact_row_cells(original_cells)
                if len(cells) == 1:
                    cell_value = cells[0]
                    if pending_single_label and pending_single_label != cell_value:
                        section_name = infer_section_name(pending_single_label, cell_value)
                        results.append(
                            ParsedKV(
                                section_name=section_name,
                                table_index=table_index,
                                row_index=row_index,
                                pair_index=0,
                                key=pending_single_label,
                                value=cell_value,
                                raw_row=cell_value,
                            )
                        )
                        pending_single_label = None
                    else:
                        pending_single_label = cell_value
                    continue

                pending_single_label = None
                if len(cells) < 2:
                    continue
                if len(set(cells)) == 1:
                    continue

                raw_row = " | ".join(cells)
                pair_index = 0
                seen_pairs: set[tuple[str, str]] = set()
                start_index = 0
                if len(cells) >= 3 and (len(cells) % 2 == 1 or looks_like_row_prefix(cells[0])):
                    start_index = 1
                row_prefix = cells[0] if start_index == 1 else ""
                remaining_cells = cells[start_index:]
                subgroup = ""
                if row_prefix and len(remaining_cells) >= 3 and len(remaining_cells) % 2 == 1:
                    subgroup = remaining_cells[0]
                    remaining_cells = remaining_cells[1:]

                if subgroup and len(remaining_cells) == 2:
                    first, second = remaining_cells
                    if first and not is_generic_subkey(first) and is_generic_subkey(second):
                        section_name = infer_section_name(subgroup, f"{row_prefix} {subgroup} {raw_row}".strip())
                        results.append(
                            ParsedKV(
                                section_name=section_name,
                                table_index=table_index,
                                row_index=row_index,
                                pair_index=pair_index,
                                key=subgroup,
                                value=first,
                                raw_row=raw_row,
                            )
                        )
                        pair_index += 1
                        remaining_cells = [second]

                all_directional = bool(remaining_cells) and all(is_directional_value(cell) for cell in remaining_cells)

                for column_index in range(0, len(remaining_cells) - 1, 2):
                    if all_directional:
                        break
                    key = remaining_cells[column_index]
                    value = remaining_cells[column_index + 1]
                    if not key or not value:
                        continue
                    if key == value:
                        continue
                    if is_generic_subkey(value) and "：" not in value and ":" not in value:
                        continue
                    pair_signature = (key, value)
                    if pair_signature in seen_pairs:
                        continue
                    seen_pairs.add(pair_signature)
                    final_key = key
                    if subgroup and is_generic_subkey(key):
                        final_key = f"{subgroup} {key}"
                    section_name = infer_section_name(final_key, f"{row_prefix} {subgroup} {raw_row}".strip())
                    results.append(
                        ParsedKV(
                            section_name=section_name,
                            table_index=table_index,
                            row_index=row_index,
                            pair_index=pair_index,
                            key=final_key,
                            value=value,
                            raw_row=raw_row,
                        )
                    )
                    pair_index += 1

                for column_index, cell_value in enumerate(remaining_cells):
                    if not cell_value:
                        continue
                    if "：" not in cell_value and ":" not in cell_value:
                        continue
                    key, value = re.split(r"[：:]", cell_value, maxsplit=1)
                    key = normalize_text(key)
                    value = normalize_text(value)
                    if not key or not value:
                        continue
                    if key == value:
                        continue
                    pair_signature = (key, value)
                    if pair_signature in seen_pairs:
                        continue
                    seen_pairs.add(pair_signature)
                    final_key = key
                    if subgroup and is_generic_subkey(key):
                        final_key = f"{subgroup} {key}"
                    section_name = infer_section_name(final_key, f"{row_prefix} {subgroup} {raw_row}".strip())
                    results.append(
                        ParsedKV(
                            section_name=section_name,
                            table_index=table_index,
                            row_index=row_index,
                            pair_index=pair_index,
                            key=final_key,
                            value=value,
                            raw_row=raw_row,
                        )
                    )
                    pair_index += 1
        except Exception:
            continue
    return results


def extract_images(docx_path: Path, plan_slug: str) -> list[ParsedImage]:
    output_dir = IMAGES_DIR / plan_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    images: list[ParsedImage] = []

    with zipfile.ZipFile(docx_path, "r") as archive:
        media_names = [name for name in archive.namelist() if name.startswith("word/media/")]
        for index, media_name in enumerate(media_names, start=1):
            suffix = Path(media_name).suffix or ".bin"
            filename = f"{index:02d}{suffix.lower()}"
            target_path = output_dir / filename
            with archive.open(media_name) as src, target_path.open("wb") as dst:
                dst.write(src.read())
            images.append(
                ParsedImage(
                    image_name=filename,
                    image_path=f"/static/images/{plan_slug}/{filename}",
                    doc_media_path=media_name,
                )
            )
    return images


def parse_plan_docx(docx_path: Path) -> ParsedPlan:
    document = Document(str(docx_path))
    details = parse_table_kv_pairs(document)
    match = re.match(r"^(?P<code>\d+)[\s_-]*(?P<name>.+)$", docx_path.stem)
    code = match.group("code") if match else None
    name = match.group("name").strip() if match else docx_path.stem.strip()
    plan_slug = re.sub(r"[^\w\-]+", "_", docx_path.stem)
    images = extract_images(docx_path, plan_slug)
    return ParsedPlan(name=name, code=code, details=details, images=images)
