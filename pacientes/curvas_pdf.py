"""
pacientes/curvas_pdf.py
PDF de curvas de crecimiento OMS.
Membrete idéntico al récipe: logo + nombre médico + especialidad + watermark + firma al pie.
"""
import io
import base64
import urllib.request as ur
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ── Paleta (igual que recipe_pdf) ────────────────────────────────────────────
NEGRO      = colors.HexColor('#111827')
GRIS       = colors.HexColor('#6B7280')
GRIS_CLARO = colors.HexColor('#9CA3AF')
TEAL       = colors.HexColor('#2AACA8')
LINEA      = colors.HexColor('#D1D5DB')
FONDO      = colors.HexColor('#F9FAFB')

MARGIN  = 1.5 * cm
FIRMA_H = 2.6 * cm   # espacio reservado para la firma al pie

# ── Estilos ───────────────────────────────────────────────────────────────────
_ctr = [0]
def _sty(**kw):
    _ctr[0] += 1
    base = dict(fontName='Helvetica', fontSize=9, textColor=NEGRO,
                spaceAfter=0, spaceBefore=0, leading=12)
    base.update(kw)
    return ParagraphStyle(f'cp_{_ctr[0]}', **base)

S_DR_NOM  = _sty(fontName='Helvetica-Bold', fontSize=15, textColor=NEGRO, leading=18, spaceAfter=1)
S_DR_ESP  = _sty(fontSize=9, textColor=GRIS, leading=12)
S_DR_DIR  = _sty(fontSize=8, textColor=GRIS, leading=11)
S_TITULO  = _sty(fontName='Helvetica-Bold', fontSize=11, textColor=TEAL, leading=14, spaceAfter=2)
S_LABEL   = _sty(fontName='Helvetica-Bold', fontSize=8, textColor=GRIS, leading=11)
S_VALOR   = _sty(fontSize=8, textColor=NEGRO, leading=11)
S_NOTA    = _sty(fontSize=7.5, textColor=GRIS, leading=10)
S_FECHA_R = _sty(fontSize=8, textColor=GRIS, leading=11, alignment=TA_RIGHT)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_bytes(url):
    try:
        return ur.urlopen(url, timeout=5).read()
    except Exception:
        return None


def _transparent_png(raw_bytes, alpha=0.08, max_px=300):
    try:
        from PIL import Image as PILImg
        img = PILImg.open(io.BytesIO(raw_bytes)).convert('RGBA')
        img.thumbnail((max_px, max_px), PILImg.LANCZOS)
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * alpha))
        out = io.BytesIO()
        PILImg.merge('RGBA', (r, g, b, a)).save(out, 'PNG')
        out.seek(0)
        return out.read()
    except Exception:
        return None


def _membrete(page_w, margin, nombre_medico, especialidad, direccion, logo_bytes, banner_bytes=None):
    """Header: logo a la izquierda + nombre grande + especialidad. Si banner_bytes, muestra el banner."""
    ancho = page_w - 2 * margin

    # Banner sustituye el membrete completo cuando está activo
    if banner_bytes:
        try:
            from PIL import Image as PILImg
            pil = PILImg.open(io.BytesIO(banner_bytes))
            w_px, h_px = pil.size
            ratio = h_px / w_px if w_px else 0.25
            banner_h = min(ancho * ratio, 3.0 * cm)
            return [Image(io.BytesIO(banner_bytes), width=ancho, height=banner_h)]
        except Exception:
            pass
    info = [Paragraph(nombre_medico, S_DR_NOM)]
    if especialidad:
        info.append(Paragraph(especialidad, S_DR_ESP))
    if direccion:
        info.append(Paragraph(direccion, S_DR_DIR))

    if logo_bytes:
        logo = Image(io.BytesIO(logo_bytes), width=2.0 * cm, height=2.0 * cm)
        t = Table([[logo, info]], colWidths=[2.5 * cm, ancho - 2.5 * cm])
        t.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (0, 0), 10),
            ('RIGHTPADDING',  (1, 0), (1, 0), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return [t]
    return list(info)


# ── Función pública ───────────────────────────────────────────────────────────

def generar_pdf_curvas(paciente, medico, config, grafica_b64: str, indicador: str) -> bytes:
    """
    Genera PDF con curvas OMS.

    Parameters
    ----------
    paciente     : Paciente
    medico       : Usuario (doctora)
    config       : ConfigConsultorio | None — para logo, teléfono, nombre consultorio
    grafica_b64  : imagen PNG en base64 (con o sin prefijo data:...)
    indicador    : 'peso' | 'talla' | 'pc'
    """
    PAGE_W, PAGE_H = letter
    ancho_util = PAGE_W - 2 * MARGIN

    # ── Datos del médico ──────────────────────────────────────────────────────
    titulo        = getattr(medico, 'titulo', '') or ''
    nombre_medico = f'{titulo} {medico.get_full_name() or medico.username}'.strip()
    especialidad  = getattr(medico, 'especialidad', '') or ''
    numero_mpps   = getattr(medico, 'numero_mpps',  '') or ''
    telefono_med  = getattr(medico, 'telefono',     '') or ''

    # ── Config del consultorio ────────────────────────────────────────────────
    logo_url     = None
    telefono_cf  = ''
    consultorio  = ''
    direccion    = ''

    if config:
        try:
            logo_url    = config.get_logo_url()
            telefono_cf = config.telefono or ''
            consultorio = getattr(config, 'nombre', '') or ''
            direccion   = getattr(config, 'direccion', '') or ''
        except Exception:
            pass

    telefono = telefono_med or telefono_cf

    # ── Logo ──────────────────────────────────────────────────────────────────
    logo_bytes = _fetch_bytes(logo_url) if logo_url else None
    wm_bytes   = _transparent_png(logo_bytes, alpha=0.08) if logo_bytes else None

    # ── Firma y sello del médico ──────────────────────────────────────────────
    firma_url = medico.get_firma_url() if hasattr(medico, 'get_firma_url') else None
    firma_bytes = _fetch_bytes(firma_url) if firma_url else None

    sello_url = medico.get_sello_url() if hasattr(medico, 'get_sello_url') else None
    sello_bytes = _fetch_bytes(sello_url) if sello_url else None

    # ── Banner del médico ─────────────────────────────────────────────────────
    banner_url = medico.get_banner_url() if hasattr(medico, 'get_banner_url') else None
    _banner_bytes = _fetch_bytes(banner_url) if banner_url else None
    banner_bytes_ctx = _banner_bytes if (getattr(medico, 'usar_banner', False) and bool(_banner_bytes)) else None

    # ── Imagen del gráfico ────────────────────────────────────────────────────
    if ',' in grafica_b64:
        grafica_b64 = grafica_b64.split(',', 1)[1]

    try:
        grafica_img_data = base64.b64decode(grafica_b64)
        grafica_stream   = io.BytesIO(grafica_img_data)
        # Ajustamos al ancho útil con proporción 16:9
        graf_w = ancho_util
        graf_h = graf_w * (9 / 16)
        grafica_img = Image(grafica_stream, width=graf_w, height=graf_h)
    except Exception:
        grafica_img = None

    # ── Título del indicador ──────────────────────────────────────────────────
    titulo_ind = {
        'peso':  'Peso para la Edad',
        'talla': 'Talla para la Edad',
        'pc':    'Perímetro Cefálico para la Edad',
    }.get(indicador, indicador.capitalize())

    # ── Edad del paciente ─────────────────────────────────────────────────────
    try:
        edad_str = str(paciente.get_edad_detallada())
    except Exception:
        edad_str = '—'

    # ── Flowables ─────────────────────────────────────────────────────────────
    items = []

    # 1. Membrete
    items += _membrete(PAGE_W, MARGIN, nombre_medico, especialidad or consultorio, direccion, logo_bytes, banner_bytes=banner_bytes_ctx)
    items.append(Spacer(1, 3 * mm))
    items.append(HRFlowable(width=ancho_util, thickness=0.8, color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 4 * mm))

    # 2. Título del reporte
    items.append(Paragraph(f'Curva de Crecimiento OMS — {titulo_ind}', S_TITULO))
    items.append(Spacer(1, 3 * mm))

    # 3. Datos del paciente (tabla 2 columnas)
    sexo_str = paciente.get_sexo_display() if (hasattr(paciente, 'get_sexo_display') and paciente.sexo) else '—'
    fnac_str = paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—'
    cedula_str = getattr(paciente, 'cedula', '—') or '—'
    grupo_str  = getattr(paciente, 'grupo_sanguineo', '—') or '—'

    pac_data = [
        [Paragraph('Paciente:', S_LABEL), Paragraph(paciente.nombre_completo, S_VALOR),
         Paragraph('Sexo:', S_LABEL),     Paragraph(sexo_str, S_VALOR)],
        [Paragraph('Cédula:', S_LABEL),   Paragraph(cedula_str, S_VALOR),
         Paragraph('Edad:', S_LABEL),     Paragraph(edad_str, S_VALOR)],
        [Paragraph('Fecha nac.:', S_LABEL), Paragraph(fnac_str, S_VALOR),
         Paragraph('Grupo sg.:', S_LABEL),  Paragraph(grupo_str, S_VALOR)],
    ]
    pac_t = Table(pac_data, colWidths=[2.8*cm, 6.2*cm, 2.8*cm, 6.2*cm])
    pac_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), FONDO),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [FONDO, colors.white]),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
    ]))
    items.append(pac_t)
    items.append(Spacer(1, 4 * mm))

    # 4. Gráfica
    if grafica_img:
        items.append(grafica_img)
    else:
        items.append(Paragraph('[Imagen del gráfico no disponible]', S_NOTA))
    items.append(Spacer(1, 3 * mm))

    # 5. Nota OMS
    items.append(HRFlowable(width=ancho_util, thickness=0.4, color=LINEA))
    items.append(Spacer(1, 2 * mm))
    items.append(Paragraph(
        'Referencias: Estándares de Crecimiento Infantil OMS (2006). '
        'Líneas de percentiles: P3, P15, P50 (mediana, teal), P85 y P97. '
        'La zona sombreada indica el rango normal P15–P85.',
        S_NOTA
    ))

    # ── Canvas callback: watermark + firma al pie ─────────────────────────────
    def _on_page(canvas, doc):
        canvas.saveState()

        # Watermark centrado en la página
        if wm_bytes:
            wm_sz = 7 * cm
            cx = PAGE_W / 2
            cy = MARGIN + FIRMA_H + (PAGE_H - MARGIN * 2 - FIRMA_H) * 0.40
            reader = ImageReader(io.BytesIO(wm_bytes))
            canvas.drawImage(
                reader,
                cx - wm_sz / 2, cy - wm_sz / 2,
                width=wm_sz, height=wm_sz,
                mask='auto', preserveAspectRatio=True,
            )

        # Firma centrada al pie
        cx = PAGE_W / 2
        LINE_W = 6 * cm
        lines = []   # (texto, font, size, color)
        if telefono:
            lines.append((telefono, 'Helvetica', 8, GRIS))
        if numero_mpps:
            lines.append((f'MPPS/CMP: {numero_mpps}', 'Helvetica', 8, GRIS))
        if especialidad:
            lines.append((especialidad, 'Helvetica', 8, GRIS))
        lines.append((nombre_medico, 'Helvetica-Bold', 9, NEGRO))

        LINE_LEAD = 11
        GAP = 3
        y = MARGIN

        for text, font, size, clr in lines:
            canvas.setFont(font, size)
            canvas.setFillColor(clr)
            canvas.drawCentredString(cx, y, text)
            y += LINE_LEAD

        y += GAP
        canvas.setStrokeColor(GRIS_CLARO)
        canvas.setLineWidth(0.6)
        canvas.line(cx - LINE_W / 2, y, cx + LINE_W / 2, y)
        y_linea = y

        # Firma: imagen centrada encima de la línea
        if firma_bytes:
            FIRMA_IMG_W = 7.5 * cm
            FIRMA_IMG_H = 2.2 * cm
            try:
                reader = ImageReader(io.BytesIO(firma_bytes))
                canvas.drawImage(
                    reader,
                    cx - FIRMA_IMG_W / 2, y_linea + 2,
                    width=FIRMA_IMG_W, height=FIRMA_IMG_H,
                    mask='auto', preserveAspectRatio=True,
                )
            except Exception:
                pass

        # Sello: a la derecha de la línea
        if sello_bytes:
            SELLO_SZ = 3.0 * cm
            sy = MARGIN + (len(lines) * LINE_LEAD) / 2 - SELLO_SZ / 2
            try:
                reader = ImageReader(io.BytesIO(sello_bytes))
                canvas.drawImage(
                    reader,
                    cx + LINE_W / 2 + 5, sy,
                    width=SELLO_SZ, height=SELLO_SZ,
                    mask='auto', preserveAspectRatio=True,
                )
            except Exception:
                pass

        # Fecha generación (esquina inferior derecha)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(GRIS_CLARO)
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 4, f'Generado: {date.today().strftime("%d/%m/%Y")}')

        canvas.restoreState()

    # ── Construir PDF ─────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    frame = Frame(
        MARGIN,
        MARGIN + FIRMA_H,
        ancho_util,
        PAGE_H - 2 * MARGIN - FIRMA_H,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='content',
    )
    page_tpl = PageTemplate(id='curvas', frames=[frame], onPage=_on_page)
    doc = BaseDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + FIRMA_H,
        pageTemplates=[page_tpl],
    )
    doc.build(items)
    buffer.seek(0)
    return buffer.getvalue()
