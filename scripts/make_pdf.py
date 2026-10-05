import os
import re
import subprocess
from markdown_it import MarkdownIt

def build_pdf():
    md = MarkdownIt()
    with open("TECHNICAL_REPORT.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    body_html = md.render(md_text)
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Technical Report</title>
<style>
@page {{
    size: A4;
    margin: 1.5cm;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #1a1a1a;
}}
h1 {{ font-size: 17pt; margin-top: 0; margin-bottom: 8px; border-bottom: 1.5px solid #222; padding-bottom: 4px; }}
h2 {{ font-size: 13pt; margin-top: 14px; margin-bottom: 6px; border-bottom: 1px solid #ddd; padding-bottom: 2px; color: #0f172a; }}
h3 {{ font-size: 11pt; margin-top: 10px; margin-bottom: 4px; color: #1e293b; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; }}
th, td {{ border: 1px solid #cbd5e1; padding: 5px 8px; text-align: left; }}
th {{ background-color: #f1f5f9; font-weight: 600; }}
pre {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px; font-size: 8.5pt; border-radius: 4px; overflow-x: auto; font-family: Consolas, monospace; }}
code {{ font-family: Consolas, monospace; font-size: 9pt; background: #f1f5f9; padding: 2px 4px; border-radius: 3px; }}
p, ul {{ margin: 5px 0; }}
li {{ margin-bottom: 2px; }}
</style>
</head>
<body>
{body_html}
</body>
</html>"""

    html_file = "TECHNICAL_REPORT.html"
    pdf_file = "TECHNICAL_REPORT.pdf"

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(full_html)

    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)
    if not edge_exe:
        print("Edge executable not found.")
        return

    abs_html = os.path.abspath(html_file)
    abs_pdf = os.path.abspath(pdf_file)

    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={abs_pdf}",
        abs_html
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0 and os.path.exists(pdf_file):
        print(f"Generated {pdf_file} successfully! Size: {os.path.getsize(pdf_file)} bytes")
        # Estimate / extract page count
        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()
        page_matches = re.findall(rb"/Type\s*/Page[^s]", pdf_bytes)
        print(f"Page count in PDF: {len(page_matches)} pages")
    else:
        print(f"Failed to generate PDF. Return code: {res.returncode}")

if __name__ == "__main__":
    build_pdf()
