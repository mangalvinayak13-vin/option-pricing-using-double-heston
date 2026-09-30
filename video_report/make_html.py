"""Minimal, dependency-free Markdown -> HTML converter, just enough for this one report."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
md = (HERE / "double_heston_report.md").read_text()

def inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s

lines = md.split("\n")
html, i, in_ul, in_table = [], 0, False, False

def close_ul():
    global in_ul
    if in_ul:
        html.append("</ul>")
        in_ul = False

def close_table():
    global in_table
    if in_table:
        html.append("</tbody></table>")
        in_table = False

while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    if stripped.startswith("!["):
        m = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
        if m:
            close_ul(); close_table()
            html.append(f'<figure><img src="{m.group(2)}" alt="{m.group(1)}"></figure>')
        i += 1; continue

    if stripped.startswith("#"):
        close_ul(); close_table()
        level = len(stripped) - len(stripped.lstrip("#"))
        text = inline(stripped[level:].strip())
        html.append(f"<h{level}>{text}</h{level}>")
        i += 1; continue

    if stripped.startswith("|"):
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if re.match(r"^:?-+:?$", cells[0].replace(" ", "")):
            i += 1; continue  # separator row
        if not in_table:
            close_ul()
            html.append('<table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
            in_table = True
        else:
            html.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        i += 1; continue
    else:
        close_table()

    if stripped.startswith("- "):
        if not in_ul:
            html.append("<ul>")
            in_ul = True
        html.append(f"<li>{inline(stripped[2:])}</li>")
        i += 1; continue
    else:
        close_ul()

    if stripped == "":
        i += 1; continue

    html.append(f"<p>{inline(stripped)}</p>")
    i += 1

close_ul(); close_table()

page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Double Heston Report</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 780px; margin: 40px auto;
         color: #1a1a1a; line-height: 1.55; font-size: 15px; }}
  h1 {{ font-size: 26px; border-bottom: 2px solid #333; padding-bottom: 8px; }}
  h2 {{ font-size: 20px; margin-top: 34px; color: #8a4b00; }}
  h3 {{ font-size: 16px; margin-top: 22px; }}
  p {{ margin: 10px 0; text-align: justify; }}
  strong {{ color: #6b3500; }}
  table {{ border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 13px; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f3ede2; }}
  figure {{ margin: 18px 0; text-align: center; page-break-inside: avoid; }}
  img {{ max-width: 100%; border: 1px solid #ddd; }}
  ul {{ margin: 8px 0; }}
  li {{ margin: 4px 0; }}
  h2 {{ page-break-before: auto; }}
</style></head><body>
{chr(10).join(html)}
</body></html>"""

(HERE / "double_heston_report.html").write_text(page)
print("wrote", HERE / "double_heston_report.html")
