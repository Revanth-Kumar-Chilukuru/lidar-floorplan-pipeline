import os
import json
import subprocess
import markdown

def main():
    # Load JSON files
    with open("results/subset/c00a170fe1_lidar_plan.json", "r") as f:
        subset_data = json.load(f)
    with open("results/full/c00a170fe1_lidar_plan.json", "r") as f:
        full_data = json.load(f)

    subset_area = subset_data["total_floor_area"]["value"]
    full_area = full_data["total_floor_area"]["value"]

    # Read markdown
    with open("docs/SUBMISSION_GUIDE.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    # Replace placeholders if any, or directly replace the sentence
    import re
    md_content = re.sub(r'\(33\.4 m2 vs 27\.3 m2\)', f'({full_area:.1f} m² vs {subset_area:.1f} m²)', md_content)
    
    # Save the dynamically updated content back to markdown
    with open("docs/SUBMISSION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    # Make the list rendering a real list and table rendering a real table using python-markdown extensions
    html_body = markdown.markdown(md_content, extensions=['tables', 'sane_lists', 'fenced_code'])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Submission Guide</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 4px; font-family: monospace; }}
        pre code {{ display: block; padding: 10px; overflow-x: auto; }}
        h1, h2, h3 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    with open("docs/SUBMISSION_GUIDE.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # Print to PDF via edge
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    
    abs_html = os.path.abspath("docs/SUBMISSION_GUIDE.html")
    abs_pdf = os.path.abspath("docs/SUBMISSION_GUIDE.pdf")
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={abs_pdf}",
        f"file:///{abs_html}"
    ]
    subprocess.run(cmd, check=True)
    
if __name__ == "__main__":
    main()
