#!/usr/bin/env python3
"""Convert PESO_Capstone_Structured.md to DOCX with rendered mxGraph diagrams."""

import re
import os
import math
import html as html_module
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from PIL import Image, ImageDraw, ImageFont

# ─── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR  = Path(r"C:\Users\user\Documents\CAPSTONE\PAPER\PAPER")
MD_FILE   = BASE_DIR / "PESO_Capstone_Structured.md"
OUT_FILE  = BASE_DIR / "PESO_Capstone.docx"
DIAG_DIR  = BASE_DIR / "diagrams"

FIGURE_XML = {
    1:  DIAG_DIR / "conceptualframework.drawio.xml",
    3:  DIAG_DIR / "dfdlvl0.xml",
    4:  DIAG_DIR / "dfdlvl1.xml",
    5:  DIAG_DIR / "usecase.xml",
    6:  DIAG_DIR / "erd.xml",
    7:  DIAG_DIR / "architecture.xml",
    8:  DIAG_DIR / "flowcharts" / "flowchart_system.xml",
    9:  DIAG_DIR / "flowcharts" / "data_preprocessing_flowchart.xml",
    10: DIAG_DIR / "flowcharts" / "ml_algorithm_flowchart.xml",
}

# ─── mxGraph Renderer ────────────────────────────────────────────────────────

def _get_font(size_pt=11):
    candidates = [
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, max(8, int(size_pt)))
            except Exception:
                pass
    return ImageFont.load_default()


def _clean_label(raw):
    """Strip HTML and decode entities from a draw.io cell value."""
    if not raw:
        return ""
    # Decode XML/HTML character references and entities
    text = html_module.unescape(raw)
    # Replace common line-break tags
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Collapse multiple blank lines to one
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _parse_style(s):
    d = {}
    for item in s.split(';'):
        item = item.strip()
        if '=' in item:
            k, v = item.split('=', 1)
            d[k.strip()] = v.strip()
        elif item:
            d[item] = '1'
    return d


def _hex_color(h, default=(255, 255, 255)):
    if not h or h in ('none', 'default', 'inherit'):
        return default
    h = h.lstrip('#')
    if len(h) == 6:
        try:
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            pass
    return default


def _arrowhead(draw, x1, y1, x2, y2, size=9, color=(50, 50, 50)):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    tip = (x2, y2)
    b1  = (x2 - size * ux + size * 0.4 * px, y2 - size * uy + size * 0.4 * py)
    b2  = (x2 - size * ux - size * 0.4 * px, y2 - size * uy - size * 0.4 * py)
    draw.polygon([tip, b1, b2], fill=color)


def _wrap(text, font, max_w):
    lines = []
    for para in text.split('\n'):
        words = para.split() if para.strip() else ['']
        cur = ''
        for w in words:
            candidate = (cur + ' ' + w).strip()
            try:
                bb = font.getbbox(candidate)
                w_px = bb[2] - bb[0]
            except Exception:
                w_px = len(candidate) * 7
            if w_px <= max_w or not cur:
                cur = candidate
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def render_diagram(xml_path, target_w=1100):
    """Return a PIL Image rendering the mxGraph XML, or None on failure."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"  [WARN] Cannot parse {xml_path.name}: {e}")
        return None

    gm = root.find('.//mxGraphModel')
    if gm is None:
        return None

    # ── Collect vertices ──────────────────────────────────────────────────
    verts = {}   # id → dict
    edges = []

    for cell in root.findall('.//mxCell'):
        cid   = cell.get('id', '')
        style = _parse_style(cell.get('style', ''))
        value = _clean_label(cell.get('value', ''))

        if cell.get('vertex') == '1':
            g = cell.find('mxGeometry')
            if g is None:
                continue
            verts[cid] = {
                'x': float(g.get('x', 0)),
                'y': float(g.get('y', 0)),
                'w': float(g.get('width', 80)),
                'h': float(g.get('height', 40)),
                'style': style,
                'value': value,
            }
        elif cell.get('edge') == '1':
            g = cell.find('mxGeometry')
            pts = []
            sp = tp = None
            if g is not None:
                for pt in g.findall('.//mxPoint'):
                    role = pt.get('as', '')
                    px, py = float(pt.get('x', 0)), float(pt.get('y', 0))
                    if role == 'sourcePoint':
                        sp = (px, py)
                    elif role == 'targetPoint':
                        tp = (px, py)
                    else:
                        pts.append((px, py))
                arr_el = g.find("Array[@as='points']")
                for pt in (arr_el if arr_el is not None else []):
                    pts.append((float(pt.get('x', 0)), float(pt.get('y', 0))))
            edges.append({
                'src': cell.get('source', ''), 'tgt': cell.get('target', ''),
                'pts': pts, 'sp': sp, 'tp': tp,
                'value': value, 'style': style,
            })

    if not verts:
        return None

    # ── Compute bounds ────────────────────────────────────────────────────
    xs = [v['x'] for v in verts.values()] + [v['x'] + v['w'] for v in verts.values()]
    ys = [v['y'] for v in verts.values()] + [v['y'] + v['h'] for v in verts.values()]
    # also include edge waypoints
    for e in edges:
        for (px, py) in e['pts']:
            xs.append(px); ys.append(py)

    PAD = 30
    min_x = min(xs) - PAD
    min_y = min(ys) - PAD
    max_x = max(xs) + PAD
    max_y = max(ys) + PAD
    content_w = max(1.0, max_x - min_x)
    content_h = max(1.0, max_y - min_y)

    scale = target_w / content_w
    img_w = int(target_w)
    img_h = max(300, int(content_h * scale))

    img  = Image.new('RGB', (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    def tx(x): return int((x - min_x) * scale)
    def ty(y): return int((y - min_y) * scale)
    def ts(v): return max(1, int(v * scale))

    STROKE = (50, 50, 50)
    BG_FILL = (235, 235, 245)   # light blue-grey for containers

    # ── Draw edges ────────────────────────────────────────────────────────
    for e in edges:
        src_v = verts.get(e['src'])
        tgt_v = verts.get(e['tgt'])

        # Determine start/end points
        if e['sp']:
            start = (tx(e['sp'][0]), ty(e['sp'][1]))
        elif src_v:
            start = (tx(src_v['x'] + src_v['w'] / 2), ty(src_v['y'] + src_v['h'] / 2))
        else:
            continue

        if e['tp']:
            end = (tx(e['tp'][0]), ty(e['tp'][1]))
        elif tgt_v:
            end = (tx(tgt_v['x'] + tgt_v['w'] / 2), ty(tgt_v['y'] + tgt_v['h'] / 2))
        else:
            continue

        waypoints = [(tx(p[0]), ty(p[1])) for p in e['pts']]
        path = [start] + waypoints + [end]

        try:
            sw_e = float(e['style'].get('strokeWidth', '1.5'))
            if not math.isfinite(sw_e): sw_e = 1.5
        except (ValueError, TypeError):
            sw_e = 1.5
        lw = max(1, int(sw_e * scale * 0.7))
        sc_hex = e['style'].get('strokeColor', '#333333')
        sc = _hex_color(sc_hex, STROKE)

        for i in range(len(path) - 1):
            draw.line([path[i], path[i + 1]], fill=sc, width=lw)

        end_arrow = e['style'].get('endArrow', 'classic')
        start_arrow = e['style'].get('startArrow', 'none')

        if end_arrow not in ('none', ''):
            p1, p2 = path[-2], path[-1]
            _arrowhead(draw, p1[0], p1[1], p2[0], p2[1], size=max(6, ts(9)), color=sc)
        if start_arrow not in ('none', ''):
            p1, p2 = path[1], path[0]
            _arrowhead(draw, p1[0], p1[1], p2[0], p2[1], size=max(6, ts(9)), color=sc)

        # Edge label
        if e['value']:
            mid = path[len(path) // 2]
            ef = _get_font(max(8, int(9 * scale)))
            draw.text((mid[0] + 3, mid[1] - 10), e['value'], fill=(80, 80, 80), font=ef)

    # ── Draw vertices ─────────────────────────────────────────────────────
    for cid, v in verts.items():
        if cid in ('0', '1'):
            continue

        ix, iy = tx(v['x']), ty(v['y'])
        iw, ih = ts(v['w']), ts(v['h'])
        st   = v['style']
        val  = v['value']

        fill_hex   = st.get('fillColor', '#FFFFFF')
        stroke_hex = st.get('strokeColor', '#000000')
        try:
            sw_v = float(st.get('strokeWidth', '1'))
            if not math.isfinite(sw_v): sw_v = 1.0
        except (ValueError, TypeError):
            sw_v = 1.0
        lw = max(1, int(sw_v * scale * 0.8))

        # Empty large containers get a background tint
        fill = _hex_color(fill_hex, (255, 255, 255))
        if not val and iw > ts(200):
            fill = BG_FILL

        stroke_c = _hex_color(stroke_hex, (50, 50, 50))

        # Detect shape
        shape_raw = st.get('shape', '')
        if 'ellipse' in st or st.get('ellipse') == '1':
            shape = 'ellipse'
        elif 'rhombus' in st or st.get('rhombus') == '1':
            shape = 'rhombus'
        elif 'parallelogram' in shape_raw:
            shape = 'parallelogram'
        elif 'cylinder' in shape_raw:
            shape = 'cylinder'
        elif 'swimlane' in st:
            shape = 'swimlane'
        else:
            shape = 'rect'

        rounded = st.get('rounded', '0') == '1'

        if shape == 'ellipse':
            draw.ellipse([ix, iy, ix + iw, iy + ih], fill=fill, outline=stroke_c, width=lw)

        elif shape == 'rhombus':
            cx, cy = ix + iw // 2, iy + ih // 2
            pts = [(cx, iy), (ix + iw, cy), (cx, iy + ih), (ix, cy)]
            draw.polygon(pts, fill=fill, outline=None)
            for i in range(4):
                draw.line([pts[i], pts[(i + 1) % 4]], fill=stroke_c, width=lw)

        elif shape == 'parallelogram':
            off = min(iw // 6, ts(15))
            pts = [(ix + off, iy), (ix + iw, iy), (ix + iw - off, iy + ih), (ix, iy + ih)]
            draw.polygon(pts, fill=fill, outline=None)
            for i in range(4):
                draw.line([pts[i], pts[(i + 1) % 4]], fill=stroke_c, width=lw)

        elif shape == 'cylinder':
            ell_h = max(8, ih // 6)
            draw.rectangle([ix, iy + ell_h // 2, ix + iw, iy + ih - ell_h // 2], fill=fill)
            draw.ellipse([ix, iy + ih - ell_h, ix + iw, iy + ih], fill=fill, outline=stroke_c, width=lw)
            draw.ellipse([ix, iy, ix + iw, iy + ell_h], fill=fill, outline=stroke_c, width=lw)
            draw.line([(ix, iy + ell_h // 2), (ix, iy + ih - ell_h // 2)], fill=stroke_c, width=lw)
            draw.line([(ix + iw, iy + ell_h // 2), (ix + iw, iy + ih - ell_h // 2)], fill=stroke_c, width=lw)

        elif shape == 'swimlane':
            draw.rectangle([ix, iy, ix + iw, iy + ih], fill=(220, 225, 235), outline=stroke_c, width=lw)
            hdr = max(20, ih // 6)
            draw.rectangle([ix, iy, ix + iw, iy + hdr], fill=(180, 190, 215), outline=stroke_c, width=lw)

        else:  # rect (possibly rounded)
            if rounded:
                r = min(iw, ih, max(4, ts(8)))
                try:
                    draw.rounded_rectangle([ix, iy, ix + iw, iy + ih], radius=r, fill=fill, outline=stroke_c, width=lw)
                except AttributeError:
                    draw.rectangle([ix, iy, ix + iw, iy + ih], fill=fill, outline=stroke_c, width=lw)
            else:
                draw.rectangle([ix, iy, ix + iw, iy + ih], fill=fill, outline=stroke_c, width=lw)

        # ── Draw label ────────────────────────────────────────────────────
        if val:
            fs_raw = float(st.get('fontSize', '11'))
            fs = max(8, int(fs_raw * scale * 0.85))
            font = _get_font(fs)
            h_align = st.get('align', 'center')
            v_align = st.get('verticalAlign', 'middle')

            pad = max(4, ts(4))
            text_w = max(20, iw - pad * 2)
            lines = _wrap(val, font, text_w)

            # Measure total text height
            line_h = fs + 2
            total_th = len(lines) * line_h

            if v_align == 'top':
                start_y = iy + pad
            elif v_align == 'bottom':
                start_y = iy + ih - total_th - pad
            else:
                start_y = iy + (ih - total_th) // 2

            t_color = _hex_color(st.get('fontColor', '#000000'), (0, 0, 0))

            cur_y = max(iy, start_y)
            for line in lines:
                if not line:
                    cur_y += line_h // 2
                    continue
                try:
                    bb = font.getbbox(line)
                    lw_px = bb[2] - bb[0]
                except Exception:
                    lw_px = len(line) * fs // 2

                if h_align == 'center':
                    lx = ix + (iw - lw_px) // 2
                elif h_align == 'right':
                    lx = ix + iw - lw_px - pad
                else:
                    lx = ix + pad

                if cur_y + line_h <= iy + ih + 5:
                    draw.text((lx, cur_y), line, fill=t_color, font=font)
                cur_y += line_h

    return img


def make_placeholder(fig_num, description, w=900, h=200):
    """Create a labeled placeholder image for figures without XML."""
    img  = Image.new('RGB', (w, h), (248, 248, 248))
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, w - 3, h - 3], outline=(180, 180, 180), width=2)
    font_big  = _get_font(16)
    font_small = _get_font(11)
    title = f"Figure {fig_num}"
    draw.text((w // 2 - 40, h // 2 - 30), title, fill=(100, 100, 100), font=font_big)
    draw.text((10, h // 2), description[:100], fill=(130, 130, 130), font=font_small)
    draw.text((10, h // 2 + 20), "(Export from draw.io and replace this placeholder)", fill=(160, 160, 160), font=font_small)
    return img


def get_figure_image(fig_num, description):
    """Return PIL Image for a figure (rendered or placeholder)."""
    xml_path = FIGURE_XML.get(fig_num)
    if xml_path and xml_path.exists():
        print(f"  Rendering Figure {fig_num} from {xml_path.name}...")
        img = render_diagram(xml_path)
        if img:
            return img
        print(f"  [WARN] Render failed; using placeholder.")
    return make_placeholder(fig_num, description)


# ─── Inline Markdown Parser ───────────────────────────────────────────────────

def parse_inline(text):
    """Return list of (fragment, bold, italic) from markdown inline markup."""
    segments = []
    pos = 0
    pat = re.compile(r'\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*([^*\n]+?)\*', re.DOTALL)
    for m in pat.finditer(text):
        if m.start() > pos:
            segments.append((text[pos:m.start()], False, False))
        if m.group(1) is not None:
            segments.append((m.group(1), True, True))
        elif m.group(2) is not None:
            segments.append((m.group(2), True, False))
        else:
            segments.append((m.group(3), False, True))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], False, False))
    return segments


# ─── DOCX Helpers ─────────────────────────────────────────────────────────────

BODY_FONT   = 'Times New Roman'
BODY_SIZE   = 12
LINE_SPACING = 24   # 24pt ≈ double-spaced for 12pt body

def _set_para_fmt(para, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0,
                  space_after=6, line_spacing=LINE_SPACING, first_indent=None):
    pf = para.paragraph_format
    para.alignment = align
    pf.space_before = Pt(space_before)
    pf.space_after  = Pt(space_after)
    pf.line_spacing = Pt(line_spacing)
    if first_indent is not None:
        pf.first_line_indent = Inches(first_indent)


def _run(para, text, bold=False, italic=False, size=BODY_SIZE, font=BODY_FONT, color=None):
    if not text:
        return
    r = para.add_run(text)
    r.bold   = bold
    r.italic = italic
    r.font.name = font
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor(*color)
    return r


def add_body_para(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                  first_indent=0.5, space_after=0):
    para = doc.add_paragraph()
    _set_para_fmt(para, align=align, first_indent=first_indent, space_after=space_after)
    for frag, bold, italic in parse_inline(text):
        _run(para, frag, bold, italic)
    return para


def add_heading(doc, text, level):
    """level 1..5 maps to our custom heading sizes."""
    sizes = {1: 14, 2: 13, 3: 12, 4: 12, 5: 12}
    aligns = {1: WD_ALIGN_PARAGRAPH.CENTER, 2: WD_ALIGN_PARAGRAPH.CENTER,
              3: WD_ALIGN_PARAGRAPH.LEFT, 4: WD_ALIGN_PARAGRAPH.LEFT, 5: WD_ALIGN_PARAGRAPH.LEFT}
    bolds   = {1: True, 2: True, 3: True, 4: True, 5: True}
    italics = {1: False, 2: False, 3: False, 4: False, 5: False}

    para = doc.add_paragraph()
    _set_para_fmt(para, align=aligns[level], space_before=12, space_after=6,
                  line_spacing=LINE_SPACING, first_indent=None)
    content = text.upper() if level == 1 else text
    r = para.add_run(content)
    r.bold   = bolds[level]
    r.italic = italics[level]
    r.font.name = BODY_FONT
    r.font.size = Pt(sizes[level])
    return para


def add_figure(doc, fig_num, description):
    img = get_figure_image(fig_num, description)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_para_fmt(para, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=6,
                  line_spacing=LINE_SPACING, first_indent=None)
    run = para.add_run()
    run.add_picture(buf, width=Inches(6.0))
    return para


def add_figure_caption(doc, text):
    # Remove surrounding * markers
    clean = text.strip().strip('*').strip()
    para = doc.add_paragraph()
    _set_para_fmt(para, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0,
                  space_after=12, line_spacing=LINE_SPACING, first_indent=None)
    r = para.add_run(clean)
    r.italic = True
    r.font.name = BODY_FONT
    r.font.size = Pt(BODY_SIZE)
    return para


def add_table(doc, header_row, data_rows, table_title=None):
    if table_title:
        tp = doc.add_paragraph()
        _set_para_fmt(tp, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=12, space_after=3,
                      line_spacing=LINE_SPACING, first_indent=None)
        for frag, bold, italic in parse_inline(table_title):
            _run(tp, frag, bold, italic)

    ncols = len(header_row)
    nrows = 1 + len(data_rows)
    tbl = doc.add_table(rows=nrows, cols=ncols)
    tbl.style = 'Table Grid'

    # Header row
    for j, cell_text in enumerate(header_row):
        cell = tbl.cell(0, j)
        cell.text = ''
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for frag, bold, italic in parse_inline(cell_text.strip()):
            r = para.add_run(frag)
            r.bold = True
            r.font.name = BODY_FONT
            r.font.size = Pt(10)

    # Data rows
    for i, row in enumerate(data_rows):
        for j, cell_text in enumerate(row):
            if j >= ncols:
                break
            cell = tbl.cell(i + 1, j)
            cell.text = ''
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            ct = cell_text.strip()
            for frag, bold, italic in parse_inline(ct):
                r = para.add_run(frag)
                r.bold   = bold
                r.italic = italic
                r.font.name = BODY_FONT
                r.font.size = Pt(10)

    # Add spacing after table
    doc.add_paragraph()
    return tbl


def add_blockquote(doc, text):
    para = doc.add_paragraph()
    _set_para_fmt(para, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6,
                  space_after=6, line_spacing=LINE_SPACING, first_indent=None)
    para.paragraph_format.left_indent  = Inches(0.5)
    para.paragraph_format.right_indent = Inches(0.5)
    r = para.add_run(text.strip())
    r.bold = True
    r.font.name = BODY_FONT
    r.font.size = Pt(BODY_SIZE)
    return para


def add_list_item(doc, text, ordered=False, num=None):
    para = doc.add_paragraph()
    _set_para_fmt(para, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0,
                  space_after=3, line_spacing=LINE_SPACING, first_indent=None)
    para.paragraph_format.left_indent       = Inches(0.5)
    para.paragraph_format.first_line_indent = Inches(-0.3)
    prefix = f"{num}.\t" if ordered and num else "•\t"
    r = para.add_run(prefix)
    r.font.name = BODY_FONT
    r.font.size = Pt(BODY_SIZE)
    for frag, bold, italic in parse_inline(text.strip()):
        _run(para, frag, bold, italic)
    return para


def insert_horiz_rule(doc):
    # A thin paragraph with bottom border acts as a horizontal rule
    para = doc.add_paragraph()
    _set_para_fmt(para, space_before=0, space_after=0, line_spacing=12, first_indent=None)
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'AAAAAA')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return para


# ─── Page Setup ───────────────────────────────────────────────────────────────

def setup_page(doc):
    sec = doc.sections[0]
    sec.page_width  = Inches(8.27)   # A4
    sec.page_height = Inches(11.69)
    sec.top_margin    = Inches(1.0)
    sec.bottom_margin = Inches(1.0)
    sec.left_margin   = Inches(1.5)  # wider left for binding
    sec.right_margin  = Inches(1.0)


# ─── Main Converter ───────────────────────────────────────────────────────────

def convert(md_path, out_path):
    text = md_path.read_text(encoding='utf-8')
    lines = text.splitlines()

    doc = Document()
    setup_page(doc)

    # Remove default empty paragraph that python-docx adds
    for p in doc.paragraphs:
        p._element.getparent().remove(p._element)

    i = 0
    in_table = False
    table_rows = []
    table_title = None
    list_counter = 0

    def flush_table():
        nonlocal in_table, table_rows, table_title
        if not table_rows:
            in_table = False
            return
        # First row is header, second row is separator → skip it
        header = [c.strip() for c in table_rows[0].split('|') if c.strip()]
        data = []
        for row in table_rows[2:]:    # skip separator row
            cells = [c for c in row.split('|')]
            # strip leading/trailing empty from split
            if cells and cells[0].strip() == '':
                cells = cells[1:]
            if cells and cells[-1].strip() == '':
                cells = cells[:-1]
            if cells:
                data.append(cells)
        add_table(doc, header, data, table_title)
        in_table = False
        table_rows = []
        table_title = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Table detection ───────────────────────────────────────────────
        if stripped.startswith('|'):
            if not in_table:
                # Check if previous non-empty line was a table title (**Table X. ...**)
                j = i - 1
                while j >= 0 and not lines[j].strip():
                    j -= 1
                if j >= 0 and re.match(r'^\*\*Table\s+\d+', lines[j].strip()):
                    table_title = lines[j].strip()
                else:
                    table_title = None
                in_table = True
                table_rows = []
            table_rows.append(stripped)
            i += 1
            continue
        elif in_table:
            flush_table()

        # ── Heading detection ─────────────────────────────────────────────
        m = re.match(r'^(#{1,5})\s+(.*)', stripped)
        if m:
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            # Skip if it's a table title (handled separately)
            if not heading_text.startswith('Table'):
                add_heading(doc, heading_text, min(level, 5))
            i += 1
            continue

        # ── Horizontal rule ────────────────────────────────────────────────
        if stripped == '---':
            # Skip — used as section separator in source; page breaks handled by headings
            i += 1
            continue

        # ── Empty line ────────────────────────────────────────────────────
        if not stripped:
            list_counter = 0  # reset list counter on blank line
            i += 1
            continue

        # ── Figure insert placeholder ─────────────────────────────────────
        m = re.match(r'^\*\[Insert Figure (\d+):\s*(.+?)\]\*$', stripped)
        if m:
            fig_num = int(m.group(1))
            desc = m.group(2).strip()
            add_figure(doc, fig_num, desc)
            i += 1
            continue

        # ── Figure caption line ───────────────────────────────────────────
        if re.match(r'^\*Figure \d+\.', stripped) and stripped.endswith('*'):
            add_figure_caption(doc, stripped)
            i += 1
            continue

        # ── Table title line (standalone **Table X. ...**) ────────────────
        if re.match(r'^\*\*Table\s+\d+', stripped):
            # Will be picked up when the table is processed
            i += 1
            continue

        # ── Block quote / formula ─────────────────────────────────────────
        if stripped.startswith('>'):
            add_blockquote(doc, stripped[1:].strip())
            i += 1
            continue

        # ── Ordered list item ─────────────────────────────────────────────
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            add_list_item(doc, m.group(2), ordered=True, num=int(m.group(1)))
            i += 1
            continue

        # ── Unordered list item ───────────────────────────────────────────
        if stripped.startswith('- ') or stripped.startswith('* '):
            add_list_item(doc, stripped[2:], ordered=False)
            i += 1
            continue

        # ── Regular paragraph ─────────────────────────────────────────────
        # Accumulate continuation lines
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt == '---' or nxt.startswith('#') or
                    nxt.startswith('|') or nxt.startswith('>') or
                    re.match(r'^\d+\.\s', nxt) or
                    re.match(r'^[-*]\s', nxt) or
                    re.match(r'^\*\[Insert Figure', nxt) or
                    re.match(r'^\*Figure \d+\.', nxt) or
                    re.match(r'^\*\*Table\s+\d+', nxt)):
                break
            para_lines.append(nxt)
            i += 1
        full_text = ' '.join(para_lines)
        add_body_para(doc, full_text, first_indent=0.5)

    # Flush any remaining table
    if in_table:
        flush_table()

    doc.save(out_path)
    print(f"\nSaved: {out_path}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Converting PESO_Capstone_Structured.md -> PESO_Capstone.docx")
    print(f"Source : {MD_FILE}")
    print(f"Output : {OUT_FILE}")
    print()
    convert(MD_FILE, OUT_FILE)
