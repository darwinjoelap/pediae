"""
pacientes/informe_referencia_pdf.py
Informe médico de referencia — layout compacto para caber en una página.
"""
import io
import urllib.request as ur
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ── Paleta ─────────────────────────────────────────────────────────────────────
NEGRO      = colors.HexColor('#111827')
GRIS       = colors.HexColor('#6B7280')
GRIS_CLARO = colors.HexColor('#9CA3AF')
TEAL       = colors.HexColor('#2AACA8')
LINEA      = colors.HexColor('#D1D5DB')
FONDO      = colors.HexColor('#F9FAFB')
TEAL_LIGHT = colors.HexColor('#E6F7F7')

MARGIN  = 1.5 * cm
FIRMA_H = 4.5 * cm

# ── Estilos ────────────────────────────────────────────────────────────────────
_ctr = [0]
def _sty(**kw):
    _ctr[0] += 1
    base = dict(fontName='Helvetica', fontSize=9, textColor=NEGRO,
                spaceAfter=0, spaceBefore=0, leading=13)
    base.update(kw)
    return ParagraphStyle(f'ir_{_ctr[0]}', **base)

S_DR_NOM   = _sty(fontName='Helvetica-Bold', fontSize=15, textColor=NEGRO, leading=18, spaceAfter=1)
S_DR_ESP   = _sty(fontSize=9, textColor=GRIS, leading=12)
S_DR_DIR   = _sty(fontSize=8, textColor=GRIS, leading=11)
S_TITULO   = _sty(fontName='Helvetica-Bold', fontSize=13, textColor=NEGRO, leading=16,
                  spaceAfter=2, spaceBefore=2, alignment=TA_CENTER)
S_SECCION  = _sty(fontName='Helvetica-Bold', fontSize=8.5, textColor=TEAL, leading=11)
S_LABEL    = _sty(fontName='Helvetica-Bold', fontSize=8, textColor=GRIS, leading=11)
S_VALOR    = _sty(fontSize=8, textColor=NEGRO, leading=11)
S_BODY     = _sty(fontSize=9, leading=14, spaceAfter=2, alignment=TA_JUSTIFY)
S_ANTEC    = _sty(fontSize=8.5, leading=14, spaceAfter=0, alignment=TA_JUSTIFY)
S_NOTA     = _sty(fontSize=7.5, textColor=GRIS, leading=10)
S_FECHA_R  = _sty(fontSize=8, textColor=GRIS, leading=11, alignment=TA_LEFT)


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


def _seccion(titulo, ancho_util):
    """Cabecera de sección con fondo teal claro — padding compacto."""
    t = Table([[Paragraph(titulo, S_SECCION)]], colWidths=[ancho_util])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), TEAL_LIGHT),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ]))
    return t


def _tabla_datos(filas, col_widths, zebra=True):
    """Tabla de label/valor con zebra optional."""
    t = Table(filas, colWidths=col_widths)
    style = [
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]
    if zebra:
        style += [('ROWBACKGROUNDS', (0, 0), (-1, -1), [FONDO, colors.white])]
    t.setStyle(TableStyle(style))
    return t


# ── Función pública ───────────────────────────────────────────────────────────

def generar_informe_referencia(paciente, medico, config, datos: dict) -> bytes:
    """
    Genera el PDF del informe médico de referencia (layout compacto).

    datos keys:
        especialidad_ref   : str
        motivo_ref         : str
        antecedentes       : list[str]
        ultima_consulta    : Consulta | None
        observaciones      : str
        ciudad             : str
        incluir_firma      : bool
    """
    PAGE_W, PAGE_H = letter
    ancho_util = PAGE_W - 2 * MARGIN

    # Anchos de columna para tablas de 6 cols (label+valor × 3)
    LW = 2.2 * cm   # label width
    VW = (ancho_util - 3 * LW) / 3  # valor width

    # ── Médico ────────────────────────────────────────────────────────────────
    titulo        = getattr(medico, 'titulo', '') or ''
    nombre_medico = f'{titulo} {medico.get_full_name() or medico.username}'.strip()
    especialidad  = getattr(medico, 'especialidad', '') or ''
    numero_mpps   = getattr(medico, 'numero_mpps',  '') or ''
    telefono_med  = getattr(medico, 'telefono',     '') or ''

    # ── Consultorio ───────────────────────────────────────────────────────────
    logo_url    = None
    telefono_cf = ''
    consultorio = ''
    direccion   = ''
    if config:
        try:
            logo_url    = config.get_logo_url()
            telefono_cf = config.telefono or ''
            consultorio = getattr(config, 'nombre_consultorio', '') or ''
            direccion   = getattr(config, 'direccion', '') or ''
        except Exception:
            pass

    telefono = telefono_med or telefono_cf

    # ── Fetch paralelo: logo, firma, sello, banner ────────────────────────────
    firma_url  = medico.get_firma_url()  if hasattr(medico, 'get_firma_url')  else None
    sello_url  = medico.get_sello_url()  if hasattr(medico, 'get_sello_url')  else None
    banner_url = medico.get_banner_url() if hasattr(medico, 'get_banner_url') else None

    from concurrent.futures import ThreadPoolExecutor
    urls = [logo_url, firma_url, sello_url, banner_url]
    with ThreadPoolExecutor(max_workers=4) as ex:
        logo_bytes, _firma_bytes, _sello_bytes, _banner_bytes = [
            r if url else None
            for url, r in zip(urls, ex.map(lambda u: _fetch_bytes(u) if u else None, urls))
        ]

    wm_bytes = _transparent_png(logo_bytes, alpha=0.08) if logo_bytes else None

    # Firma/sello sólo si el PDF las incluye
    firma_bytes = _firma_bytes if datos.get('incluir_firma', True) else None
    sello_bytes = _sello_bytes if datos.get('incluir_firma', True) else None

    banner_bytes_ctx = _banner_bytes if (getattr(medico, 'usar_banner', False) and bool(_banner_bytes)) else None

    # ── Datos del paciente ────────────────────────────────────────────────────
    ciudad           = datos.get('ciudad', '')
    especialidad_ref = datos.get('especialidad_ref', '')
    motivo_ref       = datos.get('motivo_ref', '')
    antecedentes     = datos.get('antecedentes', [])
    observaciones    = datos.get('observaciones', '')
    ultima_consulta  = datos.get('ultima_consulta')

    try:
        edad_str = str(paciente.get_edad_detallada())
    except Exception:
        edad_str = '—'

    sexo_str  = paciente.get_sexo_display() if (hasattr(paciente, 'get_sexo_display') and paciente.sexo) else '—'
    fnac_str  = paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—'
    ced_str   = getattr(paciente, 'cedula', '') or 'S/C'
    grupo_str = getattr(paciente, 'grupo_sanguineo', '') or '—'

    fecha_doc   = date.today().strftime('%d/%m/%Y')
    lugar_fecha = f'{ciudad}, {fecha_doc}' if ciudad else fecha_doc

    def L(txt): return Paragraph(txt, S_LABEL)
    def V(txt): return Paragraph(txt or '—', S_VALOR)

    # ── Flowables ─────────────────────────────────────────────────────────────
    items = []

    # Membrete
    items += _membrete(PAGE_W, MARGIN, nombre_medico, especialidad or consultorio, direccion, logo_bytes, banner_bytes=banner_bytes_ctx)
    items.append(Spacer(1, 2 * mm))
    if not banner_bytes_ctx:
        items.append(HRFlowable(width=ancho_util, thickness=0.8, color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 3 * mm))

    # Título + fecha
    items.append(Paragraph('INFORME MÉDICO DE REFERENCIA', S_TITULO))
    items.append(Paragraph(lugar_fecha, S_FECHA_R))
    items.append(Spacer(1, 3 * mm))

    # ── DATOS DEL PACIENTE (4 cols, 3 filas) ──────────────────────────────────
    items.append(_seccion('DATOS DEL PACIENTE', ancho_util))
    LW4 = 2.4 * cm
    VW4 = (ancho_util - 2 * LW4) / 2
    pac_data = [
        [L('Paciente:'),    V(paciente.nombre_completo),
         L('Cédula:'),      V(ced_str)],
        [L('Fecha nac.:'),  V(fnac_str),
         L('Edad:'),        V(edad_str)],
        [L('Sexo:'),        V(sexo_str),
         L('Grupo sg.:'),   V(grupo_str)],
    ]
    items.append(_tabla_datos(pac_data, [LW4, VW4, LW4, VW4]))
    items.append(Spacer(1, 2 * mm))

    # ── REFERENCIA (fusionada: especialidad + motivo en un solo bloque) ────────
    items.append(_seccion('REFERENCIA', ancho_util))
    ref_row = [
        [L('Especialidad:'), V(especialidad_ref),
         L('Fecha:'),        V(fecha_doc)],
    ]
    items.append(_tabla_datos(ref_row, [LW4, VW4, LW4, VW4], zebra=False))
    items.append(Spacer(1, 1 * mm))
    items.append(Paragraph('Motivo de la referencia:', S_LABEL))
    items.append(Spacer(1, 0.5 * mm))
    items.append(Paragraph(motivo_ref or '—', S_BODY))
    items.append(Spacer(1, 2 * mm))

    # ── DATOS ANTROPOMÉTRICOS (3 filas × 6 cols) ──────────────────────────────
    if ultima_consulta:
        items.append(_seccion(
            f'DATOS ANTROPOMÉTRICOS — consulta {ultima_consulta.fecha.strftime("%d/%m/%Y")}',
            ancho_util
        ))

        def _fmt(val, unit='', decs=1):
            if val is None:
                return '—'
            return f'{round(float(val), decs)} {unit}'.strip()

        def _perc(val):
            if val is None:
                return ''
            return f' (p{round(float(val))})'

        peso_txt  = _fmt(ultima_consulta.peso, 'kg') + _perc(ultima_consulta.percentil_peso)
        talla_txt = _fmt(ultima_consulta.talla, 'cm') + _perc(ultima_consulta.percentil_talla)
        pc_txt    = _fmt(ultima_consulta.perimetro_cefalico, 'cm') + _perc(ultima_consulta.percentil_pc)
        fc_txt    = f'{ultima_consulta.frecuencia_cardiaca} lpm' if ultima_consulta.frecuencia_cardiaca else '—'
        fr_txt    = f'{ultima_consulta.frecuencia_respiratoria} rpm' if ultima_consulta.frecuencia_respiratoria else '—'
        temp_txt  = _fmt(ultima_consulta.temperatura, '°C') if ultima_consulta.temperatura else '—'
        sat_txt   = f'{ultima_consulta.saturacion_oxigeno}%' if ultima_consulta.saturacion_oxigeno else '—'
        ta_txt    = ultima_consulta.tension_arterial or '—'
        clasif    = ultima_consulta.get_clasificacion_nutricional_display() if ultima_consulta.clasificacion_nutricional else '—'

        # 3 filas × 6 celdas: label | valor | label | valor | label | valor
        antro_data = [
            [L('Peso:'),   V(peso_txt),  L('Talla:'),  V(talla_txt), L('PC:'),     V(pc_txt)],
            [L('FC:'),     V(fc_txt),    L('FR:'),     V(fr_txt),    L('Temp.:'),  V(temp_txt)],
            [L('SatO₂:'), V(sat_txt),   L('T/A:'),    V(ta_txt),    L('Nutric.:'), V(clasif)],
        ]
        items.append(_tabla_datos(antro_data, [LW, VW, LW, VW, LW, VW]))

        if ultima_consulta.diagnostico:
            items.append(Spacer(1, 1 * mm))
            items.append(Paragraph(
                f'<b>Diagnóstico (última consulta):</b> {ultima_consulta.diagnostico}',
                S_BODY
            ))

        items.append(Spacer(1, 2 * mm))

    # ── ANTECEDENTES (flujo inline con ·) ─────────────────────────────────────
    if antecedentes:
        items.append(_seccion('ANTECEDENTES RELEVANTES', ancho_util))
        items.append(Spacer(1, 1 * mm))
        # Agrupar en texto fluido: cada antecedente separado por · en nueva línea
        # si supera cierta longitud se parte naturalmente al wrappear
        antec_txt = '&nbsp;&nbsp;·&nbsp;&nbsp;'.join(antecedentes)
        items.append(Paragraph(antec_txt, S_ANTEC))
        items.append(Spacer(1, 2 * mm))

    # ── OBSERVACIONES ─────────────────────────────────────────────────────────
    if observaciones:
        items.append(_seccion('OBSERVACIONES', ancho_util))
        items.append(Spacer(1, 1 * mm))
        items.append(Paragraph(observaciones, S_BODY))
        items.append(Spacer(1, 2 * mm))

    # Nota de confidencialidad
    items.append(HRFlowable(width=ancho_util, thickness=0.4, color=LINEA))
    items.append(Spacer(1, 1.5 * mm))
    items.append(Paragraph(
        'Este documento contiene información médica confidencial. '
        'Su uso está restringido al destinatario indicado.',
        S_NOTA
    ))

    # ── Canvas callback ───────────────────────────────────────────────────────
    def _on_page(canvas, doc):
        canvas.saveState()

        # Watermark
        if wm_bytes:
            wm_sz = 7 * cm
            cx = PAGE_W / 2
            cy = MARGIN + FIRMA_H + (PAGE_H - MARGIN * 2 - FIRMA_H) * 0.40
            reader = ImageReader(io.BytesIO(wm_bytes))
            canvas.drawImage(reader,
                cx - wm_sz / 2, cy - wm_sz / 2,
                width=wm_sz, height=wm_sz,
                mask='auto', preserveAspectRatio=True)

        # Firma al pie
        cx = PAGE_W / 2
        LINE_W = 6 * cm
        lines = []
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

        if firma_bytes:
            FIRMA_IMG_W = 7.5 * cm
            FIRMA_IMG_H = 2.2 * cm
            try:
                reader = ImageReader(io.BytesIO(firma_bytes))
                canvas.drawImage(reader,
                    cx - FIRMA_IMG_W / 2, y_linea + 2,
                    width=FIRMA_IMG_W, height=FIRMA_IMG_H,
                    mask='auto', preserveAspectRatio=True)
            except Exception:
                pass

        if sello_bytes:
            SELLO_SZ = 3.0 * cm
            sy = MARGIN + (len(lines) * LINE_LEAD) / 2 - SELLO_SZ / 2
            try:
                reader = ImageReader(io.BytesIO(sello_bytes))
                canvas.drawImage(reader,
                    cx + LINE_W / 2 + 5, sy,
                    width=SELLO_SZ, height=SELLO_SZ,
                    mask='auto', preserveAspectRatio=True)
            except Exception:
                pass

        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(GRIS_CLARO)
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 4,
            f'Generado: {date.today().strftime("%d/%m/%Y")}')

        canvas.restoreState()

    # ── Construir PDF ─────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    frame = Frame(
        MARGIN, MARGIN + FIRMA_H,
        ancho_util, PAGE_H - 2 * MARGIN - FIRMA_H,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='content',
    )
    page_tpl = PageTemplate(id='informe', frames=[frame], onPage=_on_page)
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
