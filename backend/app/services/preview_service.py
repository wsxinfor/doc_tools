"""简化 HTML 预览生成服务（近似效果，非像素级还原）。"""
from pathlib import Path


def generate_html_preview(docx_path: str) -> str:
    """读取生成好的 docx，转换为简化 HTML 预览字符串。"""
    import mammoth  # noqa: PLC0415

    path = Path(docx_path)
    if not path.exists():
        return "<p>Preview not available.</p>"

    with path.open("rb") as f:
        result = mammoth.convert_to_html(f)

    html_body = result.value

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }}
  h1, h2, h3, h4 {{ font-weight: bold; }}
  h1 {{ font-size: 1.8em; page-break-before: always; }}
  h2 {{ font-size: 1.5em; page-break-before: always; }}
  h3 {{ font-size: 1.2em; }}
  p {{ text-indent: 2em; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #ccc; padding: 6px; }}
  th {{ background: #4472C4; color: #fff; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
