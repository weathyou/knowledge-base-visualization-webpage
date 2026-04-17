from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from docx import Document
from sqlalchemy.orm import Session

from ..models import Plan, PlanImage
from ..schemas import DocumentBlock, DocumentNavItem, DocumentPage, DocumentTableCell, PlanDocumentResponse


NAVIGATION = [
    {
        "key": "basic",
        "title": "基本情况",
        "children": [
            {"key": "basic_unit", "title": "单位基本情况"},
            {"key": "basic_facilities", "title": "单位主要消防设施"},
            {"key": "basic_key_parts", "title": "重点部位情况"},
            {"key": "basic_tips", "title": "重点提示"},
        ],
    },
    {
        "key": "images",
        "title": "图像资料",
        "children": [
            {"key": "images_route", "title": "行车路线图"},
            {"key": "images_site", "title": "单位总平面图"},
            {"key": "images_water", "title": "水源图"},
            {"key": "images_floor", "title": "楼层平面图"},
        ],
    },
    {
        "key": "assist",
        "title": "辅助决策",
        "children": [
            {"key": "assist_scenario", "title": "灾情假设"},
            {"key": "assist_communication", "title": "现场通信"},
            {"key": "assist_initial", "title": "首战力量部署图"},
            {"key": "assist_reinforce", "title": "增援力量部署图"},
        ],
    },
]


def _normalize(value: str) -> str:
    return " ".join(value.replace("\x07", " ").replace("\n", " ").split()).strip()


def _table_cell_text(tc) -> str:
    texts = [node.text or "" for node in tc.xpath(".//w:t")]
    return _normalize("".join(texts))


def _display_table(table, table_index: int) -> list[list[DocumentTableCell]]:
    rendered: list[list[DocumentTableCell]] = []
    active_merges: dict[int, DocumentTableCell] = {}

    for row_index, tr in enumerate(table._tbl.tr_lst):
        row_cells: list[DocumentTableCell] = []
        col_index = 0
        for _, tc in enumerate(tr.tc_lst):
            while col_index in active_merges and tc.tcPr is not None and tc.tcPr.vMerge is None:
                active_merges.pop(col_index, None)
                col_index += 1

            text = _table_cell_text(tc)
            colspan = int(tc.tcPr.gridSpan.val) if tc.tcPr is not None and tc.tcPr.gridSpan is not None else 1
            vmerge = tc.tcPr.vMerge.val if tc.tcPr is not None and tc.tcPr.vMerge is not None else None

            if vmerge == "continue":
                merged_cell = active_merges.get(col_index)
                if merged_cell is not None:
                    merged_cell.rowspan += 1
                col_index += colspan
                continue

            cell = DocumentTableCell(
                text=text,
                colspan=colspan,
                rowspan=1,
                table_index=table_index,
                row_index=row_index,
                cell_index=col_index,
            )
            row_cells.append(cell)

            if tc.tcPr is not None and tc.tcPr.vMerge is not None:
                for offset in range(colspan):
                    active_merges[col_index + offset] = cell
            else:
                for offset in range(colspan):
                    active_merges.pop(col_index + offset, None)

            col_index += colspan

        if row_cells:
            rendered.append(row_cells)

    return rendered


def _rows_to_block(title: str, rows: list[list[DocumentTableCell]]) -> DocumentBlock:
    return DocumentBlock(type="table", title=title, rows=rows)


def _filter_table_rows(rows: list[list[str]], predicate) -> list[list[str]]:
    return [row for row in rows if row and predicate(_normalize(row[0]))]


def _table_slice(rows: list[list[str]], start_keywords: tuple[str, ...], end_keywords: tuple[str, ...]) -> list[list[str]]:
    start_index = None
    end_index = len(rows)
    for idx, row in enumerate(rows):
        first = _normalize(row[0]) if row else ""
        if start_index is None and any(keyword in first for keyword in start_keywords):
            start_index = idx
            continue
        if start_index is not None and any(keyword in first for keyword in end_keywords):
            end_index = idx
            break
    if start_index is None:
        return []
    return rows[start_index:end_index]


def _table_slice_indices(rows: list[list[str]], start_keywords: tuple[str, ...], end_keywords: tuple[str, ...]) -> tuple[int | None, int]:
    start_index = None
    end_index = len(rows)
    for idx, row in enumerate(rows):
        joined = " ".join(_normalize(cell) for cell in row if cell)
        if start_index is None and any(keyword in joined for keyword in start_keywords):
            start_index = idx
            continue
        if start_index is not None and end_keywords and any(keyword in joined for keyword in end_keywords):
            end_index = idx
            break
    return start_index, end_index


def _categorize_images(images: list[PlanImage]) -> dict[str, list[PlanImage]]:
    ordered = sorted(images, key=lambda item: item.image_name)
    categories = {
        "行车路线图": [],
        "单位总平面图": [],
        "水源图": [],
        "楼层平面图": [],
        "首战力量部署图": [],
        "增援力量部署图": [],
    }
    if not ordered:
        return categories

    if len(ordered) >= 1:
        categories["行车路线图"] = [ordered[0]]
    if len(ordered) >= 2:
        categories["单位总平面图"] = [ordered[1]]
    if len(ordered) >= 3:
        categories["水源图"] = [ordered[2]]

    if len(ordered) >= 6:
        categories["楼层平面图"] = ordered[3:-2]
        categories["首战力量部署图"] = [ordered[-2]]
        categories["增援力量部署图"] = [ordered[-1]]
    else:
        categories["楼层平面图"] = ordered[3:]
    return categories


def _image_block(title: str, images: list[PlanImage]) -> DocumentBlock:
    return DocumentBlock(type="image_gallery", title=title, images=images)


def _rows_to_plain_text(rows: list[list[DocumentTableCell]]) -> list[list[str]]:
    return [[cell.text for cell in row] for row in rows]


def _match_image_category(title: str) -> str | None:
    normalized = _normalize(title)
    if not normalized:
        return None
    if "路线图" in normalized:
        return "行车路线图"
    if "总平面图" in normalized:
        return "单位总平面图"
    if "水源" in normalized:
        return "水源图"
    if "平面图" in normalized:
        return "楼层平面图"
    if "初战部署图" in normalized or "首战力量部署图" in normalized:
        return "首战力量部署图"
    if "增援力量部署图" in normalized:
        return "增援力量部署图"
    return None


def _extract_image_categories(docx_path: Path, images: list[PlanImage]) -> dict[str, list[PlanImage]]:
    categories = {
        "行车路线图": [],
        "单位总平面图": [],
        "水源图": [],
        "楼层平面图": [],
        "首战力量部署图": [],
        "增援力量部署图": [],
    }
    image_by_media = {image.doc_media_path: image for image in images}

    with ZipFile(docx_path) as archive:
        document_root = ET.fromstring(archive.read("word/document.xml"))
        rel_root = ET.fromstring(archive.read("word/_rels/document.xml.rels"))

        rel_map = {}
        for rel in rel_root:
            rel_id = rel.attrib.get("Id")
            target = rel.attrib.get("Target", "")
            if rel_id and "image" in rel.attrib.get("Type", ""):
                rel_map[rel_id] = f"word/{target}"

        ns = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "v": "urn:schemas-microsoft-com:vml",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        }
        r_ns = "{%s}id" % ns["r"]

        image_sizes: dict[str, tuple[int, int]] = {}
        try:
            from PIL import Image
            import io

            Image.MAX_IMAGE_PIXELS = None
            for media_path in rel_map.values():
                try:
                    with archive.open(media_path) as src:
                        img = Image.open(io.BytesIO(src.read()))
                        image_sizes[media_path] = img.size
                except Exception:
                    continue
        except Exception:
            image_sizes = {}

        rid_usage: dict[str, int] = {}
        pending_category: str | None = None

        def filtered_media_paths(rids: list[str]) -> list[str]:
            media_paths = [rel_map[rid] for rid in rids if rid in rel_map]
            unique_paths: list[str] = []
            for media_path in media_paths:
                width, height = image_sizes.get(media_path, (1000, 1000))
                if width < 120 or height < 120:
                    continue
                unique_paths.append(media_path)
            if len(unique_paths) > 1:
                unique_paths = [path for path in unique_paths if sum(1 for rid, mp in rel_map.items() if mp == path and rid_usage.get(rid, 0) <= 1)]
            return unique_paths or media_paths

        body = document_root.find("w:body", ns)
        if body is None:
            return categories

        children = list(body)
        for child in children:
            tag = child.tag.split("}")[-1]
            if tag == "p":
                text = _normalize("".join(node.text or "" for node in child.findall(".//w:t", ns)))
                rids = [node.attrib.get(r_ns) for node in child.findall(".//v:imagedata", ns)]
                rids = [rid for rid in rids if rid]
                for rid in rids:
                    rid_usage[rid] = rid_usage.get(rid, 0) + 1
                category = _match_image_category(text)
                if rids and pending_category:
                    for media_path in filtered_media_paths(rids):
                        image = image_by_media.get(media_path)
                        if image and image not in categories[pending_category]:
                            categories[pending_category].append(image)
                    pending_category = None
                    if category:
                        pending_category = category
                    continue
                if category:
                    pending_category = category
                continue

            if tag == "tbl":
                for tr in child.findall("./w:tr", ns):
                    row_text = _normalize(" ".join(_normalize("".join(node.text or "" for node in tc.findall('.//w:t', ns))) for tc in tr.findall("./w:tc", ns)))
                    category = _match_image_category(row_text)
                    rids = [node.attrib.get(r_ns) for node in tr.findall(".//v:imagedata", ns)]
                    rids = [rid for rid in rids if rid]
                    for rid in rids:
                        rid_usage[rid] = rid_usage.get(rid, 0) + 1
                    if category and rids:
                        for media_path in filtered_media_paths(rids):
                            image = image_by_media.get(media_path)
                            if image and image not in categories[category]:
                                categories[category].append(image)

    return categories


def build_plan_document(session: Session, plan_id: int) -> PlanDocumentResponse:
    plan = session.query(Plan).filter(Plan.id == plan_id).one()
    if not plan.source_docx_path:
        raise FileNotFoundError("该预案未生成 docx 缓存")

    docx_path = Path(plan.source_docx_path)
    document = Document(str(docx_path))
    tables = [_display_table(table, table_index) for table_index, table in enumerate(document.tables)]
    basic_table = tables[0] if tables else []
    assist_table = tables[1] if len(tables) > 1 else []
    images = session.query(PlanImage).filter(PlanImage.plan_id == plan.id).order_by(PlanImage.id.asc()).all()
    image_categories = _extract_image_categories(docx_path, images)

    basic_table_plain = _rows_to_plain_text(basic_table)
    assist_table_plain = _rows_to_plain_text(assist_table)

    basic_unit_start, basic_unit_end = _table_slice_indices(basic_table_plain, ("单位基本情况",), ("单位内部主要消防设施",))
    basic_facility_start, basic_facility_end = _table_slice_indices(basic_table_plain, ("单位内部主要消防设施",), ("重点部位情况",))
    basic_key_start, basic_key_end = _table_slice_indices(basic_table_plain, ("重点部位情况",), ("重点提示",))
    basic_tip_start, basic_tip_end = _table_slice_indices(basic_table_plain, ("重点提示",), ())

    basic_unit_rows = basic_table[basic_unit_start:basic_unit_end] if basic_unit_start is not None else []
    basic_facility_rows = basic_table[basic_facility_start:basic_facility_end] if basic_facility_start is not None else []
    basic_key_rows = basic_table[basic_key_start:basic_key_end] if basic_key_start is not None else []
    basic_tip_rows = basic_table[basic_tip_start:basic_tip_end] if basic_tip_start is not None else []

    scenario_plain = _table_slice(assist_table_plain, ("灾情假设",), ("现场通信",))
    communication_plain = _table_slice(assist_table_plain, ("现场通信",), ("初战力量编成", "首战力量部署图", "初战部署图"))
    initial_plain = _table_slice(assist_table_plain, ("初战力量编成", "初战部署图"), ("增援力量编成",))
    reinforce_plain = _table_slice(assist_table_plain, ("增援力量编成", "增援部署图"), ())
    risk_plain = assist_table_plain[:4] if len(assist_table_plain) >= 4 else assist_table_plain

    scenario_rows = [row for row in assist_table if [cell.text for cell in row] in scenario_plain]
    communication_rows = [row for row in assist_table if [cell.text for cell in row] in communication_plain]
    initial_rows = [row for row in assist_table if [cell.text for cell in row] in initial_plain]
    reinforce_rows = [row for row in assist_table if [cell.text for cell in row] in reinforce_plain]
    risk_rows = assist_table[:len(risk_plain)]

    pages = [
        DocumentPage(
            key="basic",
            title="基本情况",
            blocks=[
                _rows_to_block("单位基本情况", basic_unit_rows),
                _rows_to_block("单位主要消防设施", basic_facility_rows),
                _rows_to_block("重点部位情况", basic_key_rows),
                _rows_to_block("重点提示", basic_tip_rows),
            ],
        ),
        DocumentPage(key="basic_unit", title="单位基本情况", parent_key="basic", blocks=[_rows_to_block("单位基本情况", basic_unit_rows)]),
        DocumentPage(key="basic_facilities", title="单位主要消防设施", parent_key="basic", blocks=[_rows_to_block("单位主要消防设施", basic_facility_rows)]),
        DocumentPage(key="basic_key_parts", title="重点部位情况", parent_key="basic", blocks=[_rows_to_block("重点部位情况", basic_key_rows)]),
        DocumentPage(key="basic_tips", title="重点提示", parent_key="basic", blocks=[_rows_to_block("重点提示", basic_tip_rows)]),
        DocumentPage(
            key="images",
            title="图像资料",
            blocks=[
                _image_block("行车路线图", image_categories["行车路线图"]),
                _image_block("单位总平面图", image_categories["单位总平面图"]),
                _image_block("水源图", image_categories["水源图"]),
                _image_block("楼层平面图", image_categories["楼层平面图"]),
            ],
        ),
        DocumentPage(key="images_route", title="行车路线图", parent_key="images", blocks=[_image_block("行车路线图", image_categories["行车路线图"])]),
        DocumentPage(key="images_site", title="单位总平面图", parent_key="images", blocks=[_image_block("单位总平面图", image_categories["单位总平面图"])]),
        DocumentPage(key="images_water", title="水源图", parent_key="images", blocks=[_image_block("水源图", image_categories["水源图"])]),
        DocumentPage(key="images_floor", title="楼层平面图", parent_key="images", blocks=[_image_block("楼层平面图", image_categories["楼层平面图"])]),
        DocumentPage(
            key="assist",
            title="辅助决策",
            blocks=[
                _rows_to_block("风险评估", risk_rows),
                _rows_to_block("灾情假设", scenario_rows),
                _rows_to_block("现场通信", communication_rows),
                _rows_to_block("首战力量部署", initial_rows),
                _image_block("首战力量部署图", image_categories["首战力量部署图"]),
                _rows_to_block("增援力量部署", reinforce_rows),
                _image_block("增援力量部署图", image_categories["增援力量部署图"]),
            ],
        ),
        DocumentPage(key="assist_scenario", title="灾情假设", parent_key="assist", blocks=[_rows_to_block("灾情假设", scenario_rows)]),
        DocumentPage(key="assist_communication", title="现场通信", parent_key="assist", blocks=[_rows_to_block("现场通信", communication_rows)]),
        DocumentPage(
            key="assist_initial",
            title="首战力量部署图",
            parent_key="assist",
            blocks=[_rows_to_block("首战力量部署", initial_rows), _image_block("首战力量部署图", image_categories["首战力量部署图"])],
        ),
        DocumentPage(
            key="assist_reinforce",
            title="增援力量部署图",
            parent_key="assist",
            blocks=[_rows_to_block("增援力量部署", reinforce_rows), _image_block("增援力量部署图", image_categories["增援力量部署图"])],
        ),
    ]

    navigation = [
        DocumentNavItem(
            key=item["key"],
            title=item["title"],
            children=[DocumentNavItem(**child) for child in item.get("children", [])],
        )
        for item in NAVIGATION
    ]

    return PlanDocumentResponse(
        plan_id=plan.id,
        plan_name=plan.name,
        pages=pages,
        navigation=navigation,
    )
