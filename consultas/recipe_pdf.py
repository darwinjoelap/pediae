"""
consultas/recipe_pdf.py
Récipe médico — landscape letter, dos columnas simétricas.
Firma fija al pie de página dibujada vía canvas callback.
"""
import io
import urllib.request as ur

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ── Paleta ────────────────────────────────────────────────────────────────────
NEGRO      = colors.HexColor('#111827')
GRIS       = colors.HexColor('#6B7280')
GRIS_CLARO = colors.HexColor('#9CA3AF')
LINEA      = colors.HexColor('#D1D5DB')

# ── Dimensiones ───────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(letter)
MARGIN = 1.3 * cm
SEP    = 0.8 * cm
COL_W  = (PAGE_W - 2 * MARGIN - SEP) / 2

# Altura reservada para la firma al pie (espacio que el contenido no debe pisar)
FIRMA_H = 2.4 * cm   # HR + nombre + especialidad + mpps + telefono

# ── Estilos ───────────────────────────────────────────────────────────────────
_ctr = [0]


def _style(**kw):
    _ctr[0] += 1
    base = dict(fontName='Helvetica', fontSize=9, textColor=NEGRO,
                spaceAfter=0, spaceBefore=0, leading=12)
    base.update(kw)
    return ParagraphStyle(f'rcp_{_ctr[0]}', **base)


S_DR_NOM  = _style(fontName='Helvetica-Bold', fontSize=16, textColor=NEGRO, leading=20, spaceAfter=1)
S_DR_ESP  = _style(fontSize=10, textColor=GRIS, leading=13)
S_DR_DIR  = _style(fontSize=9,  textColor=GRIS, leading=12)
S_FECHA   = _style(fontSize=9,  textColor=GRIS, alignment=TA_RIGHT, leading=12)
S_PAC_NOM = _style(fontName='Helvetica-Bold', fontSize=10, textColor=NEGRO, leading=14, spaceAfter=1)
S_PAC_DET = _style(fontSize=9, textColor=GRIS, leading=12)
S_SECCION = _style(fontName='Helvetica-Bold', fontSize=11, textColor=NEGRO, leading=15)
S_BODY    = _style(fontSize=9.5, textColor=NEGRO, leading=14, spaceAfter=2)
S_BODY_IT = _style(fontSize=9.5, textColor=NEGRO, leading=14, spaceAfter=2, leftIndent=8)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_bytes(url):
    try:
        return ur.urlopen(url, timeout=5).read()
    except Exception:
        return None


def _transparent_png(raw_bytes, alpha=0.10, max_px=300):
    """Devuelve bytes PNG redimensionado y con opacidad reducida para watermark."""
    try:
        from PIL import Image as PILImg
        img = PILImg.open(io.BytesIO(raw_bytes)).convert('RGBA')
        # Limita a max_px para que el watermark no pese más de lo necesario
        img.thumbnail((max_px, max_px), PILImg.LANCZOS)
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * alpha))
        out = io.BytesIO()
        PILImg.merge('RGBA', (r, g, b, a)).save(out, 'PNG')
        out.seek(0)
        return out.read()
    except Exception:
        return None


def _membrete(col_w, nombre_medico, especialidad, direccion, logo_bytes):
    """Header: logo + nombre grande + especialidad + dirección."""
    info = [Paragraph(nombre_medico, S_DR_NOM)]
    if especialidad:
        info.append(Paragraph(especialidad, S_DR_ESP))
    if direccion:
        info.append(Paragraph(direccion, S_DR_DIR))

    if logo_bytes:
        logo = Image(io.BytesIO(logo_bytes), width=1.8 * cm, height=1.8 * cm)
        t = Table([[logo, info]], colWidths=[2.2 * cm, col_w - 2.2 * cm])
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


def _bloque_lado(etiqueta, contenido_texto, *, col_w, nombre_medico,
                 especialidad, direccion, logo_bytes,
                 paciente, consulta, edad_str, fecha_str, estudios=''):
    """Flowables de una columna (SIN firma — la firma va en el canvas callback)."""
    items = []

    # 1. Membrete
    items += _membrete(col_w, nombre_medico, especialidad, direccion, logo_bytes)
    items.append(Spacer(1, 3 * mm))

    # 2. Línea separadora
    items.append(HRFlowable(width=col_w, thickness=0.5, color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 3 * mm))

    # 3. Fecha (derecha)
    items.append(Paragraph(fecha_str, S_FECHA))
    items.append(Spacer(1, 3 * mm))

    # 4. Datos del paciente
    items.append(Paragraph(paciente.nombre_completo, S_PAC_NOM))
    det = []
    if edad_str and edad_str != '—':
        det.append(f'Edad: {edad_str}')
    if consulta.peso:
        det.append(f'Peso: {consulta.peso} kg')
    if getattr(consulta, 'talla', None):
        det.append(f'Talla: {consulta.talla} cm')
    if det:
        items.append(Paragraph(' , '.join(det), S_PAC_DET))
    items.append(Spacer(1, 4 * mm))

    # 5. Etiqueta sección
    items.append(Paragraph(etiqueta, S_SECCION))
    items.append(Spacer(1, 3 * mm))

    # 6. Contenido
    texto = (contenido_texto or '').strip()
    if texto:
        for linea in texto.split('\n'):
            linea = linea.strip()
            if not linea:
                items.append(Spacer(1, 2 * mm))
                continue
            if linea[0] in '-·•' or (
                    len(linea) > 2 and linea[1] in '.):' and linea[0].isdigit()):
                items.append(Paragraph(linea, S_BODY_IT))
            else:
                items.append(Paragraph(linea, S_BODY))

    # 7. Estudios solicitados (solo si hay contenido)
    estudios_txt = (estudios or '').strip()
    if estudios_txt:
        items.append(Spacer(1, 4 * mm))
        items.append(Paragraph('Estudios solicitados:', S_SECCION))
        items.append(Spacer(1, 3 * mm))
        for linea in estudios_txt.split('\n'):
            linea = linea.strip()
            if not linea:
                items.append(Spacer(1, 2 * mm))
                continue
            if linea[0] in '-·•' or (
                    len(linea) > 2 and linea[1] in '.):' and linea[0].isdigit()):
                items.append(Paragraph(linea, S_BODY_IT))
            else:
                items.append(Paragraph(linea, S_BODY))

    return items


# ── Función pública ───────────────────────────────────────────────────────────

def generar_recipe_pdf(consulta, medico, config):
    """
    Genera el récipe médico en PDF y devuelve un io.BytesIO listo para leer.

    Parámetros
    ----------
    consulta : Consulta  — con paciente, tratamiento, indicaciones, lugar
    medico   : Usuario   — quien está atendiendo (título Dr./Dra. según sexo)
    config   : ConfigConsultorio | None — logo, teléfono, etc.
    """
    paciente = consulta.paciente

    # ── Médico ────────────────────────────────────────────────────────────────
    titulo        = getattr(medico, 'titulo', '')          # Dr. / Dra.
    nombre_medico = f'{titulo} {medico.get_full_name() or medico.username}'.strip()
    especialidad  = getattr(medico, 'especialidad', '') or ''
    numero_mpps   = getattr(medico, 'numero_mpps',   '') or ''
    telefono_med  = getattr(medico, 'telefono',      '') or ''

    # ── Configuración ─────────────────────────────────────────────────────────
    if config:
        logo_url    = config.get_logo_url()
        telefono_cf = config.telefono or ''
    else:
        logo_url    = None
        telefono_cf = ''

    telefono = telefono_med or telefono_cf

    # ── Dirección del lugar de la consulta ────────────────────────────────────
    lugar = getattr(consulta, 'lugar', None)
    direccion = ''
    if lugar:
        direccion = (getattr(lugar, 'direccion', '') or
                     getattr(lugar, 'nombre',    '') or '')

    # ── Logo ──────────────────────────────────────────────────────────────────
    logo_bytes = _fetch_bytes(logo_url) if logo_url else None
    wm_bytes   = _transparent_png(logo_bytes, alpha=0.10) if logo_bytes else None

    # ── Edad / fecha ──────────────────────────────────────────────────────────
    try:
        edad_str = paciente.get_edad_detallada()
    except Exception:
        try:
            edad_str = paciente.get_edad()
        except Exception:
            edad_str = '—'
    if callable(edad_str):
        edad_str = edad_str()
    edad_str  = str(edad_str) if edad_str else '—'
    fecha_str = consulta.fecha.strftime('%d/%m/%Y')

    # ── Columnas de contenido ─────────────────────────────────────────────────
    kw = dict(
        col_w=COL_W,
        nombre_medico=nombre_medico,
        especialidad=especialidad,
        direccion=direccion,
        logo_bytes=logo_bytes,
        paciente=paciente,
        consulta=consulta,
        edad_str=edad_str,
        fecha_str=fecha_str,
    )

    lado_izq = _bloque_lado('RP:',          consulta.tratamiento  or '', estudios='', **kw)
    lado_der = _bloque_lado('Indicaciones', consulta.indicaciones or '',
                            estudios=consulta.laboratorio or '', **kw)

    # ── Canvas callback: watermark + firma fija al pie ────────────────────────
    def _on_page(canvas, doc):
        canvas.saveState()

        # — Watermark: logo transparente centrado en cada columna —
        if wm_bytes:
            wm_size = 5.5 * cm
            col1_cx = MARGIN + COL_W / 2
            col2_cx = MARGIN + COL_W + SEP + COL_W / 2
            wm_y    = MARGIN + FIRMA_H + (PAGE_H - MARGIN * 2 - FIRMA_H) * 0.30
            for cx in (col1_cx, col2_cx):
                reader = ImageReader(io.BytesIO(wm_bytes))
                canvas.drawImage(
                    reader,
                    cx - wm_size / 2, wm_y,
                    width=wm_size, height=wm_size,
                    mask='auto', preserveAspectRatio=True,
                )

        # — Firma fija al pie: centrada en cada columna —
        col1_cx = MARGIN + COL_W / 2
        col2_cx = MARGIN + COL_W + SEP + COL_W / 2
        LINE_W  = 5 * cm

        # Líneas de texto desde abajo hacia arriba
        lines = []                         # (texto, fontName, fontSize, color)
        if telefono:
            lines.append((telefono,              'Helvetica', 8, GRIS))
        if numero_mpps:
            lines.append((f'MPPS/CMP: {numero_mpps}', 'Helvetica', 8, GRIS))
        if especialidad:
            lines.append((especialidad,          'Helvetica', 8, GRIS))
        lines.append((nombre_medico,             'Helvetica-Bold', 9, NEGRO))

        LINE_LEADING = 11  # puntos entre líneas de la firma
        GAP_BELOW_HR = 3   # espacio entre HR y primera línea de texto

        # Y base (borde inferior del área de la firma)
        y = MARGIN

        # Dibuja líneas de abajo hacia arriba
        for text, font, size, clr in lines:
            canvas.setFont(font, size)
            canvas.setFillColor(clr)
            canvas.drawCentredString(col1_cx, y, text)
            canvas.drawCentredString(col2_cx, y, text)
            y += LINE_LEADING

        y += GAP_BELOW_HR  # espacio antes de la raya

        # Raya de firma
        canvas.setStrokeColor(GRIS_CLARO)
        canvas.setLineWidth(0.6)
        for cx in (col1_cx, col2_cx):
            canvas.line(cx - LINE_W / 2, y, cx + LINE_W / 2, y)

        # Línea divisoria vertical entre columnas (misma que la tabla)
        div_x = MARGIN + COL_W + SEP / 2
        canvas.setStrokeColor(LINEA)
        canvas.setLineWidth(0.5)
        canvas.line(div_x, MARGIN, div_x, y + 4)

        canvas.restoreState()

    # ── Tabla principal (contenido, sin firma) ────────────────────────────────
    tabla = Table(
        [[lado_izq, '', lado_der]],
        colWidths=[COL_W, SEP, COL_W],
    )
    tabla.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (0, 0),   8),
        ('LEFTPADDING',   (2, 0), (2, 0),   8),
    ]))

    # Frame de contenido: deja FIRMA_H libre en la parte inferior
    buffer = io.BytesIO()
    frame = Frame(
        MARGIN,
        MARGIN + FIRMA_H,                          # empieza sobre la firma
        PAGE_W - 2 * MARGIN,
        PAGE_H - 2 * MARGIN - FIRMA_H,            # altura disponible para contenido
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='content',
    )
    page_tpl = PageTemplate(id='recipe', frames=[frame], onPage=_on_page)
    doc = BaseDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + FIRMA_H,
        pageTemplates=[page_tpl],
    )
    doc.build([tabla])
    buffer.seek(0)
    return buffer
