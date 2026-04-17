from __future__ import annotations

from pathlib import Path

from ..config import DOCX_CACHE_DIR


class DocConversionError(RuntimeError):
    """Raised when a legacy .doc file cannot be converted."""


def convert_doc_to_docx(doc_path: Path) -> Path:
    doc_path = doc_path.resolve()
    DOCX_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_path = DOCX_CACHE_DIR / f"{doc_path.stem}.docx"

    if target_path.exists() and target_path.stat().st_mtime >= doc_path.stat().st_mtime:
        return target_path

    try:
        import pythoncom
        import win32com.client
    except Exception as exc:  # pragma: no cover
        raise DocConversionError(f"缺少 pywin32 或 Word COM 环境: {exc}") from exc

    pythoncom.CoInitialize()
    word = None
    document = None
    conversion_error: Exception | None = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(str(doc_path), False, True)
        document.SaveAs2(str(target_path), FileFormat=16)
    except Exception as exc:  # pragma: no cover
        conversion_error = exc
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

    if target_path.exists():
        return target_path

    if conversion_error is not None:
        raise DocConversionError(f"转换失败: {doc_path.name}: {conversion_error}") from conversion_error

    raise DocConversionError(f"转换后未生成 docx 文件: {target_path}")
