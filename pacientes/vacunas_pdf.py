"""
pacientes/vacunas_pdf.py
PDF del Esquema de Vacunación del paciente.
Mismo membrete que constancias_pdf: logo + nombre médico + watermark + firma al pie.
"""
import io
from collections import OrderedDict
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ── Paleta (misma que constancias_pdf) ────────────────────────────────────────
NEGRO      = colors.HexColor('#111827')
GRIS       = colors.HexColor('#6B7280')
GRIS_CLARO = colors.HexColor('#9CA3AF')
TEAL       = colors.HexColor('#2AACA8')
TEAL_CLARO = colors.HexColor('#E0F7F6')
LINEA      = colors.HexColor('#D1D5DB')
VERDE      = colors.HexColor('#16A34A')
ROJO       = colors.HexColor('#DC2626')
AMARILLO   = colors.HexColor('#D97706')
GRIS_FILA  = colors.HexColor('#F3F4F6')

MARGIN  = 1.5 * cm
FIRMA_H = 4.5 * cm

# ── Estilos ───────────────────────────────────────────────────────────────────
_ctr = [0]


def _sty(**kw):
    _ctr[0] += 1
    base = dict(fontName='Helvetica', fontSize=9, textColor=NEGRO,
                spaceAfter=0, spaceBefore=0, leading=13)
    base.update(kw)
    return ParagraphStyle(f'vp_{_ctr[0]}', **base)


S_DR_NOM  = _sty(fontName='Helvetica-Bold', fontSize=15, textColor=NEGRO, leading=18, spaceAfter=1)
S_DR_ESP  = _sty(fontSize=9, textColor=GRIS, leading=12)
S_DR_DIR  = _sty(fontSize=8, textColor=GRIS, leading=11)
S_TITULO  = _sty(fontName='Helvetica-Bold', fontSize=13, textColor=NEGRO, leading=16,
                 spaceAfter=4, spaceBefore=4, alignment=TA_CENTER)
S_PACIENTE = _sty(fontSize=9.5, leading=14, spaceAfter=2)
S_PACIENTE_B = _sty(fontName='Helvetica-Bold', fontSize=9.5, leading=14, spaceAfter=2)
S_GRUPO   = _sty(fontName='Helvetica-Bold', fontSize=9, textColor=colors.white,
                 alignment=TA_LEFT, leading=13)
S_VAC     = _sty(fontSize=8.5, leading=12)
S_VAC_B   = _sty(fontName='Helvetica-Bold', fontSize=8.5, leading=12)
S_NOTA    = _sty(fontSize=7.5, textColor=GRIS, leading=11)
S_RESUMEN = _sty(fontSize=8.5, textColor=NEGRO, leading=12, alignment=TA_CENTER)


# ── Helpers reutilizados de constancias_pdf ───────────────────────────────────

def _fetch_bytes(url):
    import urllib.request as ur
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
    from reportlab.lib.utils import ImageReader
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


def _canvas_cb(nombre_medico, especialidad, numero_mpps, telefono, wm_bytes,
               firma_bytes=None, sello_bytes=None):
    from reportlab.lib.utils import ImageReader
    PAGE_W, PAGE_H = letter

    def _on_page(canvas, doc):
        canvas.saveState()

        if wm_bytes:
            wm_sz = 7 * cm
            cx = PAGE_W / 2
            cy = MARGIN + FIRMA_H + (PAGE_H - MARGIN * 2 - FIRMA_H) * 0.40
            reader = ImageReader(io.BytesIO(wm_bytes))
            canvas.drawImage(reader, cx - wm_sz / 2, cy - wm_sz / 2,
                             width=wm_sz, height=wm_sz,
                             mask='auto', preserveAspectRatio=True)

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
                canvas.drawImage(reader, cx - FIRMA_IMG_W / 2, y_linea + 2,
                                 width=FIRMA_IMG_W, height=FIRMA_IMG_H,
                                 mask='auto', preserveAspectRatio=True)
            except Exception:
                pass

        if sello_bytes:
            SELLO_SZ = 3.0 * cm
            try:
                reader = ImageReader(io.BytesIO(sello_bytes))
                sx = cx + LINE_W / 2 + 5
                sy = MARGIN + (len(lines) * LINE_LEAD) / 2 - SELLO_SZ / 2
                canvas.drawImage(reader, sx, sy,
                                 width=SELLO_SZ, height=SELLO_SZ,
                                 mask='auto', preserveAspectRatio=True)
            except Exception:
                pass

        # Numeración de página
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(GRIS_CLARO)
        canvas.drawCentredString(cx, MARGIN - 8,
                                 f'Página {doc.page}')
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 4,
                               f'Generado: {date.today().strftime("%d/%m/%Y")}')
        canvas.restoreState()

    return _on_page


def _contexto_medico(medico, config):
    titulo        = getattr(medico, 'titulo', '') or ''
    nombre_medico = f'{titulo} {medico.get_full_name() or medico.username}'.strip()
    especialidad  = getattr(medico, 'especialidad', '') or ''
    numero_mpps   = getattr(medico, 'numero_mpps',  '') or ''
    telefono_med  = getattr(medico, 'telefono',     '') or ''

    logo_url = telefono_cf = direccion = consultorio = ''
    if config:
        try:
            logo_url    = config.get_logo_url()
            telefono_cf = config.telefono or ''
            consultorio = getattr(config, 'nombre', '') or ''
            direccion   = getattr(config, 'direccion', '') or ''
        except Exception:
            pass

    telefono = telefono_med or telefono_cf

    firma_url  = medico.get_firma_url()  if hasattr(medico, 'get_firma_url')  else None
    sello_url  = medico.get_sello_url()  if hasattr(medico, 'get_sello_url')  else None
    banner_url = medico.get_banner_url() if hasattr(medico, 'get_banner_url') else None

    from concurrent.futures import ThreadPoolExecutor
    urls = [logo_url, firma_url, sello_url, banner_url]
    with ThreadPoolExecutor(max_workers=4) as ex:
        logo_bytes, firma_bytes, sello_bytes, _banner_bytes = [
            r if url else None
            for url, r in zip(urls, ex.map(lambda u: _fetch_bytes(u) if u else None, urls))
        ]

    wm_bytes     = _transparent_png(logo_bytes, alpha=0.08) if logo_bytes else None
    _usar_banner = getattr(medico, 'usar_banner', False) and bool(_banner_bytes)

    return dict(
        nombre_medico=nombre_medico,
        especialidad=especialidad or consultorio,
        numero_mpps=numero_mpps,
        telefono=telefono,
        logo_bytes=logo_bytes,
        wm_bytes=wm_bytes,
        direccion=direccion,
        firma_bytes=firma_bytes,
        sello_bytes=sello_bytes,
        banner_bytes=_banner_bytes if _usar_banner else None,
        usar_banner=_usar_banner,
    )


# ── Función principal ─────────────────────────────────────────────────────────

def generar_vacunas_pdf(paciente, medico, config, esquema: list, datos: dict) -> bytes:
    """
    Genera el PDF del esquema de vacunación del paciente.

    esquema : lista de dicts {'vacuna': Vacuna, 'estado': str, 'aplicada': VacunaAplicada|None}
    datos   : {'ciudad': str, 'incluir_firma': bool}
    """
    PAGE_W, PAGE_H = letter
    ancho_util = PAGE_W - 2 * MARGIN

    ctx = _contexto_medico(medico, config)
    if not datos.get('incluir_firma', True):
        ctx['firma_bytes'] = None
        ctx['sello_bytes'] = None

    # ── Agrupar por grupo_etario ──────────────────────────────────────────────
    grupos = OrderedDict()
    for e in esquema:
        g = getattr(e['vacuna'], 'grupo_etario', '') or 'Otras vacunas'
        grupos.setdefault(g, []).append(e)

    # ── Datos del paciente ────────────────────────────────────────────────────
    try:
        edad_str = str(paciente.get_edad_detallada())
    except Exception:
        edad_str = '—'

    fnac = paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—'
    hoy  = date.today()

    total    = len(esquema)
    aplicadas_n = sum(1 for e in esquema if e['estado'] == 'aplicada')
    atrasadas_n = sum(1 for e in esquema if e['estado'] == 'atrasada')
    pendientes_n = total - aplicadas_n

    # ── Columnas de la tabla de vacunas ───────────────────────────────────────
    # Ancho útil ≈ 18.6 cm
    COL_W = [7.2 * cm, 3.0 * cm, 3.2 * cm, 5.2 * cm]  # Vacuna | Estado | Fecha | Lote/Obs

    HEADER_VAC = ['Vacuna', 'Estado', 'Fecha', 'Lote / Obs.']

    # ── Estilo base de la tabla ───────────────────────────────────────────────
    def _tabla_style(num_filas):
        return TableStyle([
            # Encabezado
            ('BACKGROUND',    (0, 0), (-1, 0), TEAL),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING',    (0, 0), (-1, 0), 5),
            # Filas de datos
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), 8),
            ('TOPPADDING',    (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 5),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID',          (0, 0), (-1, -1), 0.3, LINEA),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS_FILA]),
        ])

    # ── Construir flowables ───────────────────────────────────────────────────
    items = []

    # Membrete
    items += _membrete(PAGE_W, MARGIN,
                       ctx['nombre_medico'], ctx['especialidad'],
                       ctx['direccion'], ctx['logo_bytes'],
                       banner_bytes=ctx.get('banner_bytes'))
    items.append(Spacer(1, 3 * mm))
    items.append(HRFlowable(width=ancho_util, thickness=0.8, color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 5 * mm))

    # Título
    items.append(Paragraph('ESQUEMA DE VACUNACIÓN', S_TITULO))
    items.append(HRFlowable(width=ancho_util, thickness=0.4, color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 4 * mm))

    # Info del paciente en tabla compacta 2 columnas
    info_data = [
        [Paragraph('<b>Paciente:</b>', S_PACIENTE), Paragraph(paciente.nombre_completo, S_PACIENTE),
         Paragraph('<b>Fecha nac.:</b>', S_PACIENTE), Paragraph(fnac, S_PACIENTE)],
        [Paragraph('<b>Edad:</b>', S_PACIENTE), Paragraph(edad_str, S_PACIENTE),
         Paragraph('<b>Fecha emisión:</b>', S_PACIENTE), Paragraph(hoy.strftime('%d/%m/%Y'), S_PACIENTE)],
    ]
    t_info = Table(info_data, colWidths=[2.8 * cm, 5.5 * cm, 2.8 * cm, 5.5 * cm])
    t_info.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    items.append(t_info)
    items.append(Spacer(1, 3 * mm))

    # Barra resumen
    resumen_data = [[
        Paragraph(f'<b>{aplicadas_n}</b> aplicadas', S_RESUMEN),
        Paragraph(f'<b>{pendientes_n}</b> pendientes / futuras', S_RESUMEN),
        Paragraph(f'<b>{atrasadas_n}</b> atrasadas', S_RESUMEN),
    ]]
    t_res = Table(resumen_data, colWidths=[ancho_util / 3] * 3)
    t_res.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), colors.HexColor('#DCFCE7')),
        ('BACKGROUND',    (1, 0), (1, 0), colors.HexColor('#FEF9C3')),
        ('BACKGROUND',    (2, 0), (2, 0), colors.HexColor('#FEE2E2') if atrasadas_n else colors.HexColor('#FEF9C3')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.4, LINEA),
        ('ROUNDEDCORNERS', [3]),
    ]))
    items.append(t_res)
    items.append(Spacer(1, 5 * mm))

    # ── Tablas por grupo etario ───────────────────────────────────────────────
    for grupo_label, vacs in grupos.items():
        # Encabezado de grupo
        g_data = [[Paragraph(f'  {grupo_label}', S_GRUPO)]]
        t_g = Table(g_data, colWidths=[ancho_util])
        t_g.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), TEAL),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ]))
        items.append(t_g)

        # Filas de vacunas
        rows = [HEADER_VAC]
        for e in vacs:
            v = e['vacuna']
            ap = e['aplicada']
            estado = e['estado']

            nombre_txt = f'{v.nombre}  (d{v.dosis_numero})'
            if estado == 'aplicada':
                estado_txt = '✓ Aplicada'
                fecha_txt  = ap.fecha.strftime('%d/%m/%Y') if ap and ap.fecha else 'Registrada'
                lote_txt   = (ap.lote or '') + (f'\n{ap.observaciones}' if ap and ap.observaciones else '') if ap else ''
            elif estado == 'atrasada':
                estado_txt = '⚠ Atrasada'
                fecha_txt  = '—'
                lote_txt   = ''
            elif estado == 'pendiente':
                estado_txt = '○ Pendiente'
                fecha_txt  = '—'
                lote_txt   = ''
            else:
                estado_txt = '→ Futura'
                fecha_txt  = '—'
                lote_txt   = ''

            rows.append([nombre_txt, estado_txt, fecha_txt, lote_txt or '—'])

        t_vac = Table(rows, colWidths=COL_W, repeatRows=1)
        style = _tabla_style(len(rows))

        # Color por estado en columna 1
        for i, e in enumerate(vacs, start=1):
            if e['estado'] == 'aplicada':
                style.add('TEXTCOLOR', (1, i), (1, i), VERDE)
                style.add('FONTNAME',  (1, i), (1, i), 'Helvetica-Bold')
            elif e['estado'] == 'atrasada':
                style.add('TEXTCOLOR', (1, i), (1, i), ROJO)
                style.add('FONTNAME',  (1, i), (1, i), 'Helvetica-Bold')
            elif e['estado'] == 'pendiente':
                style.add('TEXTCOLOR', (1, i), (1, i), AMARILLO)

        t_vac.setStyle(style)
        items.append(t_vac)
        items.append(Spacer(1, 4 * mm))

    # Nota al pie
    items.append(HRFlowable(width=ancho_util, thickness=0.4, color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 2 * mm))
    items.append(Paragraph(
        '✓ Aplicada   ○ Pendiente/Futura   ⚠ Atrasada   '
        '→ Aún no corresponde por edad',
        S_NOTA,
    ))

    # ── PDF ───────────────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    frame = Frame(
        MARGIN, MARGIN + FIRMA_H,
        ancho_util, PAGE_H - 2 * MARGIN - FIRMA_H,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='content',
    )
    on_page = _canvas_cb(
        ctx['nombre_medico'], ctx['especialidad'],
        ctx['numero_mpps'], ctx['telefono'], ctx['wm_bytes'],
        firma_bytes=ctx.get('firma_bytes'),
        sello_bytes=ctx.get('sello_bytes'),
    )
    page_tpl = PageTemplate(id='vacunas', frames=[frame], onPage=on_page)
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
