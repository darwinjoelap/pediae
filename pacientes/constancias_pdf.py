"""
pacientes/constancias_pdf.py
Constancias médicas en PDF: Niño Sano, Reposo, Lactancia Materna.
Mismo membrete que recipe_pdf / curvas_pdf: logo + nombre médico + watermark + firma al pie.
"""
import io
import urllib.request as ur
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
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
TEAL       = colors.HexColor('#2AACA8')
LINEA      = colors.HexColor('#D1D5DB')

MARGIN  = 1.5 * cm
FIRMA_H = 4.5 * cm   # ampliado para acomodar imagen de firma sobre la línea

# ── Estilos ───────────────────────────────────────────────────────────────────
_ctr = [0]
def _sty(**kw):
    _ctr[0] += 1
    base = dict(fontName='Helvetica', fontSize=9, textColor=NEGRO,
                spaceAfter=0, spaceBefore=0, leading=13)
    base.update(kw)
    return ParagraphStyle(f'cs_{_ctr[0]}', **base)

S_DR_NOM  = _sty(fontName='Helvetica-Bold', fontSize=15, textColor=NEGRO, leading=18, spaceAfter=1)
S_DR_ESP  = _sty(fontSize=9, textColor=GRIS, leading=12)
S_DR_DIR  = _sty(fontSize=8, textColor=GRIS, leading=11)
S_TITULO  = _sty(fontName='Helvetica-Bold', fontSize=13, textColor=NEGRO, leading=16,
                 spaceAfter=4, spaceBefore=4, alignment=TA_CENTER)
S_BODY    = _sty(fontSize=9.5, leading=15, spaceAfter=3, alignment=TA_JUSTIFY)
S_BODY_B  = _sty(fontName='Helvetica-Bold', fontSize=9.5, leading=15, spaceAfter=3)
S_ITEM    = _sty(fontSize=9.5, leading=15, spaceAfter=3, leftIndent=12, alignment=TA_JUSTIFY)
S_NOTA    = _sty(fontSize=8, textColor=GRIS, leading=11)


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


def _membrete(page_w, margin, nombre_medico, especialidad, direccion, logo_bytes):
    ancho = page_w - 2 * margin
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


_DIAS = [
    '', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez',
    'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho',
    'diecinueve', 'veinte', 'veintiuno', 'veintidós', 'veintitrés', 'veinticuatro',
    'veinticinco', 'veintiséis', 'veintisiete', 'veintiocho', 'veintinueve', 'treinta',
    'treinta y uno',
]
_MESES = [
    '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]
_MILES = {
    2024: 'dos mil veinticuatro', 2025: 'dos mil veinticinco',
    2026: 'dos mil veintiséis',   2027: 'dos mil veintisiete',
    2028: 'dos mil veintiocho',   2029: 'dos mil veintinueve',
    2030: 'dos mil treinta',
}


def _fecha_letras(d: date) -> str:
    """'a los dieciséis (16) días del mes de mayo de 2026'"""
    dia_n  = _DIAS[d.day]   if d.day  < len(_DIAS)  else str(d.day)
    mes_n  = _MESES[d.month] if d.month < len(_MESES) else ''
    anio_n = _MILES.get(d.year, str(d.year))
    return f'a los {dia_n} ({d.day}) días del mes de {mes_n} de {anio_n}'


def _canvas_cb(nombre_medico, especialidad, numero_mpps, telefono, wm_bytes,
               firma_bytes=None, sello_bytes=None):
    """Devuelve la función onPage para el canvas callback (watermark + firma + sello)."""
    PAGE_W, PAGE_H = letter

    def _on_page(canvas, doc):
        canvas.saveState()

        # Watermark (logo semitransparente centrado en el cuerpo)
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

        # Texto del pie de página (nombre, especialidad, MPPS, teléfono)
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

        # Firma: imagen PNG centrada, base apoyada sobre la línea
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

        # Sello: imagen circular / cuadrada a la derecha de la línea de firma
        if sello_bytes:
            SELLO_SZ = 3.0 * cm
            try:
                reader = ImageReader(io.BytesIO(sello_bytes))
                sx = cx + LINE_W / 2 + 5
                sy = MARGIN + (len(lines) * LINE_LEAD) / 2 - SELLO_SZ / 2
                canvas.drawImage(
                    reader,
                    sx, sy,
                    width=SELLO_SZ, height=SELLO_SZ,
                    mask='auto', preserveAspectRatio=True,
                )
            except Exception:
                pass

        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(GRIS_CLARO)
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 4,
                               f'Generado: {date.today().strftime("%d/%m/%Y")}')
        canvas.restoreState()

    return _on_page


def _build_pdf(items, on_page_fn) -> bytes:
    PAGE_W, PAGE_H = letter
    ancho_util = PAGE_W - 2 * MARGIN
    buffer = io.BytesIO()
    frame = Frame(
        MARGIN, MARGIN + FIRMA_H,
        ancho_util, PAGE_H - 2 * MARGIN - FIRMA_H,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='content',
    )
    page_tpl = PageTemplate(id='constancia', frames=[frame], onPage=on_page_fn)
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


# ── Función base de contexto médico ──────────────────────────────────────────

def _contexto_medico(medico, config):
    titulo        = getattr(medico, 'titulo', '') or ''
    nombre_medico = f'{titulo} {medico.get_full_name() or medico.username}'.strip()
    especialidad  = getattr(medico, 'especialidad', '') or ''
    numero_mpps   = getattr(medico, 'numero_mpps',  '') or ''
    telefono_med  = getattr(medico, 'telefono',     '') or ''

    logo_url    = None
    telefono_cf = ''
    direccion   = ''
    consultorio = ''

    if config:
        try:
            logo_url    = config.get_logo_url()
            telefono_cf = config.telefono or ''
            consultorio = getattr(config, 'nombre', '') or ''
            direccion   = getattr(config, 'direccion', '') or ''
        except Exception:
            pass

    telefono   = telefono_med or telefono_cf
    logo_bytes = _fetch_bytes(logo_url) if logo_url else None
    wm_bytes   = _transparent_png(logo_bytes, alpha=0.08) if logo_bytes else None

    # Firma y sello digitalizados del médico
    firma_bytes = None
    firma_field = getattr(medico, 'firma', None)
    if firma_field and getattr(firma_field, 'name', None):
        try:
            firma_bytes = firma_field.read()
        except Exception:
            try:
                with open(firma_field.path, 'rb') as fh:
                    firma_bytes = fh.read()
            except Exception:
                firma_bytes = None

    sello_bytes = None
    sello_field = getattr(medico, 'sello', None)
    if sello_field and getattr(sello_field, 'name', None):
        try:
            sello_bytes = sello_field.read()
        except Exception:
            try:
                with open(sello_field.path, 'rb') as fh:
                    sello_bytes = fh.read()
            except Exception:
                sello_bytes = None

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
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. CONSTANCIA DE NIÑO SANO
# ══════════════════════════════════════════════════════════════════════════════

def generar_constancia_nino_sano(paciente, medico, config, datos: dict) -> bytes:
    """
    datos keys:
      ciudad          str   — ciudad donde se emite
      vacunas_ok      bool  — el esquema está completo
      incluir_vacunas bool  — incluir párrafo de inmunizaciones
    """
    PAGE_W, _ = letter
    ctx = _contexto_medico(medico, config)
    if not datos.get('incluir_firma', True):
        ctx['firma_bytes'] = None
        ctx['sello_bytes'] = None

    ciudad          = datos.get('ciudad', '')
    vacunas_ok      = datos.get('vacunas_ok', True)
    incluir_vacunas = datos.get('incluir_vacunas', True)

    # Datos del paciente
    try:
        edad_str = str(paciente.get_edad_detallada())
    except Exception:
        edad_str = ''

    fnac = paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—'

    # Última consulta con peso/talla
    ultima = paciente.consultas.filter(
        peso__isnull=False
    ).order_by('-fecha').first()
    peso_str  = f'{ultima.peso} kg' if ultima and ultima.peso else '—'
    talla_str = f'{ultima.talla} cm' if ultima and getattr(ultima, 'talla', None) else '—'

    hoy = date.today()
    fecha_letras = _fecha_letras(hoy)

    items = []
    items += _membrete(PAGE_W, MARGIN,
                       ctx['nombre_medico'], ctx['especialidad'],
                       ctx['direccion'], ctx['logo_bytes'])
    items.append(Spacer(1, 3 * mm))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.8,
                             color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 6 * mm))

    items.append(Paragraph('CONSTANCIA DE NIÑO SANO', S_TITULO))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.4,
                             color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 5 * mm))

    items.append(Paragraph(
        f'Por medio de la presente se hace constar que el paciente '
        f'<b>{paciente.nombre_completo}</b>, {edad_str} '
        f'(Fecha de nacimiento: {fnac}), fue evaluado clínicamente en la '
        f'presente fecha en el marco de la consulta de control de niño sano, '
        f'obteniéndose los siguientes datos antropométricos:',
        S_BODY,
    ))
    items.append(Spacer(1, 2 * mm))
    items.append(Paragraph(f'Peso: <b>{peso_str}</b>', S_ITEM))
    items.append(Paragraph(f'Talla: <b>{talla_str}</b>', S_ITEM))
    items.append(Spacer(1, 3 * mm))

    items.append(Paragraph('<b>Evaluación y Diagnóstico:</b>', S_BODY_B))
    items.append(Paragraph(
        '<b>1. Examen Físico:</b> Paciente en excelentes condiciones generales, '
        'activo, reactivo, con un desarrollo psicomotor adecuado para su edad '
        'cronológica. Sistema cardiopulmonar, abdominal y neurológico completamente normales.',
        S_ITEM,
    ))
    items.append(Paragraph(
        '<b>2. Diagnóstico Nutricional:</b> Normopeso (Eutrófico). Tanto el peso como '
        'la talla se encuentran dentro de los percentiles normales y adecuados para su '
        'edad y sexo, evidenciando un crecimiento armónico.',
        S_ITEM,
    ))

    if incluir_vacunas:
        if vacunas_ok:
            vac_txt = (
                '<b>3. Inmunizaciones:</b> Posterior a la revisión de la tarjeta de '
                'vacunación, se constata que el esquema de inmunizaciones se encuentra '
                '<b>completo y al día</b> para su edad.'
            )
        else:
            vac_txt = (
                '<b>3. Inmunizaciones:</b> Posterior a la revisión de la tarjeta de '
                'vacunación, se constata que el esquema de inmunizaciones presenta '
                '<b>dosis pendientes</b> para su edad.'
            )
        items.append(Paragraph(vac_txt, S_ITEM))

    items.append(Spacer(1, 3 * mm))
    items.append(Paragraph('<b>Conclusión:</b>', S_BODY_B))
    items.append(Paragraph(
        'Se concluye que el menor se encuentra clínicamente <b>SANO</b>, sin evidencia '
        'de patologías agudas o crónicas al momento de la evaluación.',
        S_ITEM,
    ))
    items.append(Spacer(1, 5 * mm))

    ciudad_txt = f'en la ciudad de {ciudad}, ' if ciudad else ''
    items.append(Paragraph(
        f'Se expide la presente constancia a petición de la parte interesada, '
        f'{ciudad_txt}{fecha_letras}.',
        S_BODY,
    ))

    on_page = _canvas_cb(ctx['nombre_medico'], ctx['especialidad'],
                         ctx['numero_mpps'], ctx['telefono'], ctx['wm_bytes'],
                         firma_bytes=ctx.get('firma_bytes'),
                         sello_bytes=ctx.get('sello_bytes'))
    return _build_pdf(items, on_page)


# ══════════════════════════════════════════════════════════════════════════════
# 2. CONSTANCIA DE REPOSO
# ══════════════════════════════════════════════════════════════════════════════

_NUMS = [
    '', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez',
    'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho',
    'diecinueve', 'veinte', 'veintiuno', 'veintidós', 'veintitrés', 'veinticuatro',
    'veinticinco', 'veintiséis', 'veintisiete', 'veintiocho', 'veintinueve', 'treinta',
]


def _num_letras(n: int) -> str:
    if 0 < n < len(_NUMS):
        return _NUMS[n]
    return str(n)


def generar_constancia_reposo(paciente, medico, config, datos: dict) -> bytes:
    """
    datos keys:
      ciudad      str
      dias        int   — días de reposo
      motivo      str   — diagnóstico / motivo
      fecha_inicio date  — inicio del reposo (default hoy)
    """
    PAGE_W, _ = letter
    ctx = _contexto_medico(medico, config)
    if not datos.get('incluir_firma', True):
        ctx['firma_bytes'] = None
        ctx['sello_bytes'] = None

    ciudad      = datos.get('ciudad', '')
    dias        = int(datos.get('dias', 1))
    motivo      = datos.get('motivo', '')
    fecha_ini   = datos.get('fecha_inicio') or date.today()
    hoy         = date.today()
    fecha_letras = _fecha_letras(hoy)
    dias_letras  = _num_letras(dias)

    cedula_txt = f', portador de la cédula de identidad N° {paciente.cedula},' \
        if paciente.cedula else ''

    items = []
    items += _membrete(PAGE_W, MARGIN,
                       ctx['nombre_medico'], ctx['especialidad'],
                       ctx['direccion'], ctx['logo_bytes'])
    items.append(Spacer(1, 3 * mm))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.8,
                             color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 6 * mm))

    items.append(Paragraph('CONSTANCIA DE REPOSO MÉDICO', S_TITULO))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.4,
                             color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 14 * mm))   # +3 espacios bajo el título

    motivo_txt = f', por presentar: <b>{motivo}</b>' if motivo else ''
    fecha_ini_str = fecha_ini.strftime('%d/%m/%Y') if hasattr(fecha_ini, 'strftime') else str(fecha_ini)

    items.append(Spacer(1, 9 * mm))    # +3 espacios antes del desarrollo
    items.append(Paragraph(
        f'Por medio de la presente se hace constar que el/la paciente '
        f'<b>{paciente.nombre_completo}</b>{cedula_txt}, fue evaluado/a '
        f'clínicamente en esta fecha, prescribiéndosele reposo médico por un período de '
        f'<b>{dias_letras} ({dias}) día{"s" if dias != 1 else ""}</b>, '
        f'contados a partir del {fecha_ini_str}{motivo_txt}.',
        S_BODY,
    ))
    items.append(Spacer(1, 5 * mm))

    ciudad_txt = f'en la ciudad de {ciudad}, ' if ciudad else ''
    items.append(Paragraph(
        f'Se expide la presente constancia a petición de la parte interesada, '
        f'{ciudad_txt}{fecha_letras}.',
        S_BODY,
    ))

    on_page = _canvas_cb(ctx['nombre_medico'], ctx['especialidad'],
                         ctx['numero_mpps'], ctx['telefono'], ctx['wm_bytes'],
                         firma_bytes=ctx.get('firma_bytes'),
                         sello_bytes=ctx.get('sello_bytes'))
    return _build_pdf(items, on_page)


# ══════════════════════════════════════════════════════════════════════════════
# 3. CERTIFICADO DE LACTANCIA MATERNA
# ══════════════════════════════════════════════════════════════════════════════

def generar_certificado_lactancia(paciente, medico, config, datos: dict) -> bytes:
    """
    datos keys:
      ciudad         str
      duracion_meses int  — meses de lactancia exclusiva
    """
    PAGE_W, _ = letter
    ctx = _contexto_medico(medico, config)
    if not datos.get('incluir_firma', True):
        ctx['firma_bytes'] = None
        ctx['sello_bytes'] = None

    ciudad         = datos.get('ciudad', '')
    duracion_meses = int(datos.get('duracion_meses', 6))
    hoy            = date.today()
    fecha_letras   = _fecha_letras(hoy)
    dur_letras     = _num_letras(duracion_meses)

    fnac = paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—'
    sexo = getattr(paciente, 'sexo', '') or ''
    art_nino  = 'la niña' if sexo == 'F' else 'el niño'
    art_nino2 = 'la niña' if sexo == 'F' else 'el niño'
    art_del   = 'de la niña' if sexo == 'F' else 'del niño'
    art_lo    = 'la' if sexo == 'F' else 'lo'

    items = []
    items += _membrete(PAGE_W, MARGIN,
                       ctx['nombre_medico'], ctx['especialidad'],
                       ctx['direccion'], ctx['logo_bytes'])
    items.append(Spacer(1, 3 * mm))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.8,
                             color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 6 * mm))

    items.append(Paragraph('CERTIFICADO DE LACTANCIA MATERNA EXCLUSIVA', S_TITULO))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.4,
                             color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 5 * mm))

    items.append(Paragraph(
        f'Por medio de la presente se certifica con orgullo que {art_nino} '
        f'<b>{paciente.nombre_completo}</b>, quien nació el {fnac}, ha recibido '
        f'<b>LACTANCIA MATERNA EXCLUSIVA</b> durante sus primeros '
        f'<b>{dur_letras} ({duracion_meses}) meses</b> de vida, de acuerdo con las '
        f'recomendaciones de la Organización Mundial de la Salud (OMS) y la UNICEF.',
        S_BODY,
    ))
    items.append(Spacer(1, 3 * mm))
    items.append(Paragraph(
        f'La lactancia materna exclusiva es uno de los actos más significativos en el '
        f'desarrollo y protección de la salud de un niño/a, proporcionando todos los '
        f'nutrientes necesarios, anticuerpos y el vínculo afectivo esencial para su '
        f'crecimiento integral.',
        S_BODY,
    ))
    items.append(Spacer(1, 3 * mm))
    items.append(Paragraph(
        f'En reconocimiento a este logro compartido entre madre e hijo/a, se otorga el '
        f'presente certificado como testimonio del compromiso y dedicación hacia la salud '
        f'y bienestar {art_del} <b>{paciente.nombre_completo}</b>.',
        S_BODY,
    ))
    items.append(Spacer(1, 5 * mm))

    ciudad_txt = f'en la ciudad de {ciudad}, ' if ciudad else ''
    items.append(Paragraph(
        f'Se expide el presente certificado {ciudad_txt}{fecha_letras}.',
        S_BODY,
    ))

    on_page = _canvas_cb(ctx['nombre_medico'], ctx['especialidad'],
                         ctx['numero_mpps'], ctx['telefono'], ctx['wm_bytes'],
                         firma_bytes=ctx.get('firma_bytes'),
                         sello_bytes=ctx.get('sello_bytes'))
    return _build_pdf(items, on_page)


# ══════════════════════════════════════════════════════════════════════════════
# 4. CONSTANCIA DE LACTANCIA MATERNA (para lugar de trabajo)
# ══════════════════════════════════════════════════════════════════════════════

def generar_constancia_lactancia_trabajo(paciente, medico, config, datos: dict) -> bytes:
    """
    datos keys:
      ciudad        str
      nombre_madre  str   — nombre completo de la madre
      cedula_madre  str   — cédula de la madre
    """
    PAGE_W, _ = letter
    ctx = _contexto_medico(medico, config)
    if not datos.get('incluir_firma', True):
        ctx['firma_bytes'] = None
        ctx['sello_bytes'] = None

    ciudad       = datos.get('ciudad', '')
    nombre_madre = datos.get('nombre_madre', '').strip()
    cedula_madre = datos.get('cedula_madre', '').strip()
    hoy          = date.today()
    fecha_letras = _fecha_letras(hoy)

    # Datos antropométricos del paciente
    try:
        edad_str = str(paciente.get_edad_detallada())
    except Exception:
        edad_str = ''

    ultima    = paciente.consultas.filter(peso__isnull=False).order_by('-fecha').first()
    peso_str  = f'{ultima.peso} kg'  if ultima and ultima.peso                    else '—'
    talla_str = f'{ultima.talla} cm' if ultima and getattr(ultima, 'talla', None) else '—'

    # Texto de cierre con datos de la madre
    if nombre_madre and cedula_madre:
        ciudad_txt = f', {ciudad}' if ciudad else ''
        peticion_txt = (
            f'Constancia que se expide a petición de su madre '
            f'<b>{nombre_madre}</b>, C.I. <b>{cedula_madre}</b>'
            f'{ciudad_txt}, {fecha_letras}.'
        )
    elif nombre_madre:
        ciudad_txt = f', {ciudad}' if ciudad else ''
        peticion_txt = (
            f'Constancia que se expide a petición de su madre '
            f'<b>{nombre_madre}</b>{ciudad_txt}, {fecha_letras}.'
        )
    else:
        ciudad_txt2 = f'en la ciudad de {ciudad}, ' if ciudad else ''
        peticion_txt = (
            f'Se expide la presente constancia a petición de la parte interesada, '
            f'{ciudad_txt2}{fecha_letras}.'
        )

    items = []
    items += _membrete(PAGE_W, MARGIN,
                       ctx['nombre_medico'], ctx['especialidad'],
                       ctx['direccion'], ctx['logo_bytes'])
    items.append(Spacer(1, 3 * mm))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.8,
                             color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 6 * mm))

    items.append(Paragraph('CONSTANCIA DE LACTANCIA MATERNA', S_TITULO))
    items.append(HRFlowable(width=PAGE_W - 2 * MARGIN, thickness=0.4,
                             color=LINEA, spaceAfter=0))
    items.append(Spacer(1, 14 * mm))   # igual que reposo

    # Datos del paciente
    items.append(Paragraph(
        f'<b>Paciente:</b> {paciente.nombre_completo}'
        f'{", " + edad_str if edad_str else ""}',
        S_BODY,
    ))
    items.append(Paragraph(
        f'<b>Peso:</b> {peso_str} &nbsp;&nbsp;&nbsp; <b>Talla:</b> {talla_str}',
        S_BODY,
    ))
    items.append(Spacer(1, 9 * mm))   # igual que reposo

    items.append(Paragraph(
        'Paciente quien actualmente recibe <b>lactancia materna</b> + '
        '<b>alimentación complementaria</b>, por lo que se indica dar '
        'continuidad a la misma, agradeciendo de antemano la colaboración '
        'para el cumplimiento de la misma.',
        S_BODY,
    ))
    items.append(Spacer(1, 5 * mm))

    items.append(Paragraph(peticion_txt, S_BODY))

    on_page = _canvas_cb(ctx['nombre_medico'], ctx['especialidad'],
                         ctx['numero_mpps'], ctx['telefono'], ctx['wm_bytes'],
                         firma_bytes=ctx.get('firma_bytes'),
                         sello_bytes=ctx.get('sello_bytes'))
    return _build_pdf(items, on_page)
