"""
consultas/recipe_pdf.py
Generación del récipe médico en PDF landscape con dos columnas simétricas.
Uso:
    from consultas.recipe_pdf import generar_recipe_pdf
    buffer = generar_recipe_pdf(consulta, medico, config)
"""
import io
import urllib.request as ur

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)


# ── Paleta ───────────────────────────────────────────────────────────────────
TEAL       = colors.HexColor('#2AACA8')
TEAL_DARK  = colors.HexColor('#1E7D7A')
GRIS       = colors.HexColor('#6B7280')
GRIS_CLARO = colors.HexColor('#9CA3AF')
OSCURO     = colors.HexColor('#111827')
LINEA      = colors.HexColor('#E5E7EB')
FONDO_PAC  = colors.HexColor('#F0FDFC')
BLANCO     = colors.white

# ── Dimensiones ──────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(letter)
MARGIN = 1.3 * cm
SEP    = 0.8 * cm
COL_W  = (PAGE_W - 2 * MARGIN - SEP) / 2


# ── Estilos ──────────────────────────────────────────────────────────────────
_ctr = [0]

def _style(**kw):
    _ctr[0] += 1
    base = dict(fontName='Helvetica', fontSize=9, textColor=OSCURO,
                spaceAfter=0, spaceBefore=0, leading=12)
    base.update(kw)
    return ParagraphStyle(f'rcp_{_ctr[0]}', **base)


S_MEDICO_NOMBRE = _style(fontName='Helvetica-Bold', fontSize=12, textColor=OSCURO,
                         leading=15, spaceAfter=1)
S_MEDICO_ESP    = _style(fontSize=8.5, textColor=TEAL_DARK, leading=11, spaceAfter=1)
S_MEDICO_CRED   = _style(fontSize=8, textColor=GRIS, leading=10, spaceAfter=0)
S_MEDICO_MPPS   = _style(fontSize=7.5, textColor=GRIS_CLARO, leading=10)
S_PAC_NOMBRE    = _style(fontName='Helvetica-Bold', fontSize=9.5, textColor=OSCURO,
                         leading=12, spaceAfter=1)
S_PAC_DET       = _style(fontSize=8.5, textColor=GRIS, leading=11)
S_BODY          = _style(fontSize=9.5, textColor=OSCURO, leading=14, spaceAfter=3)
S_BODY_ITEM     = _style(fontSize=9.5, textColor=OSCURO, leading=14, spaceAfter=2,
                         leftIndent=8)
S_FIRMA_NOMBRE  = _style(fontName='Helvetica-Bold', fontSize=9, textColor=OSCURO,
                         alignment=TA_CENTER, leading=12)
S_FIRMA_SUB     = _style(fontSize=7.5, textColor=GRIS, alignment=TA_CENTER,
                         leading=10, spaceAfter=1)
S_FECHA         = _style(fontSize=7.5, textColor=GRIS_CLARO, alignment=TA_RIGHT,
                         leading=10)
S_CONTACTO      = _style(fontSize=7.5, textColor=GRIS, alignment=TA_CENTER, leading=10)
S_ETIQUETA      = _style(fontName='Helvetica-Bold', fontSize=8.5,
                         textColor=BLANCO, leading=11)


# ── Helpers internos ─────────────────────────────────────────────────────────

def _fetch_image(url, width, height):
    """Descarga una imagen desde una URL y devuelve un flowable Image, o None."""
    try:
        data = ur.urlopen(url, timeout=5).read()
        return Image(io.BytesIO(data), width=width, height=height)
    except Exception:
        return None


def _membrete(col_w, nombre_medico, especialidad, credenciales, numero_mpps,
              logo_url, membrete_url):
    """Devuelve la lista de flowables del membrete (imagen o texto generado)."""
    items = []
    if membrete_url:
        img = _fetch_image(membrete_url, col_w, 2.0 * cm)
        if img:
            img.hAlign = 'CENTER'
            items.append(img)
            return items

    logo_img = _fetch_image(logo_url, 1.6 * cm, 1.6 * cm) if logo_url else None
    info = [Paragraph(nombre_medico, S_MEDICO_NOMBRE)]
    if especialidad:
        info.append(Paragraph(especialidad, S_MEDICO_ESP))
    if credenciales:
        info.append(Paragraph(credenciales, S_MEDICO_CRED))
    if numero_mpps:
        info.append(Paragraph(f'MPPS/CMP: {numero_mpps}', S_MEDICO_MPPS))

    if logo_img:
        t = Table([[logo_img, info]], colWidths=[2.0 * cm, col_w - 2.0 * cm])
        t.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',   (0, 0), (0, 0), 0),
            ('RIGHTPADDING',  (0, 0), (0, 0), 8),
            ('LEFTPADDING',   (1, 0), (1, 0), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ]))
        items.append(t)
    else:
        items += info
    return items


def _bloque_paciente(col_w, paciente, consulta, edad_str, medidas):
    """Devuelve el bloque con fondo teal suave con datos del paciente."""
    det_parts = [edad_str]
    if medidas:
        det_parts.append(medidas)
    det_str = ' · '.join(det_parts)

    data = [[Paragraph('Paciente', S_PAC_DET),
             Paragraph(paciente.nombre_completo, S_PAC_NOMBRE)]]
    if det_str:
        data.append([Paragraph('', S_PAC_DET), Paragraph(det_str, S_PAC_DET)])
    dx = getattr(consulta, 'diagnostico', '') or ''
    if dx:
        data.append([Paragraph('Dx', S_PAC_DET), Paragraph(dx[:120], S_PAC_DET)])

    t = Table(data, colWidths=[1.6 * cm, col_w - 1.6 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), FONDO_PAC),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR',     (0, 0), (0, -1), GRIS),
    ]))
    return t


def _firma(nombre_medico, especialidad, numero_mpps, telefono_medico,
           telefono_config, email):
    """Devuelve la firma médica al pie de cada columna."""
    items = []
    items.append(HRFlowable(width=4.5 * cm, thickness=0.8, color=GRIS_CLARO,
                            hAlign='CENTER'))
    items.append(Spacer(1, 1.5 * mm))
    items.append(Paragraph(nombre_medico, S_FIRMA_NOMBRE))
    if especialidad:
        items.append(Paragraph(especialidad, S_FIRMA_SUB))
    if numero_mpps:
        items.append(Paragraph(f'MPPS/CMP: {numero_mpps}', S_FIRMA_SUB))
    # Teléfono: prioriza el del médico, si no el del consultorio
    tel = telefono_medico or telefono_config
    contacto = ' · '.join(filter(None, [tel, email]))
    if contacto:
        items.append(Paragraph(contacto, S_CONTACTO))
    return items


def _bloque_lado(etiqueta, contenido_texto, col_w,
                 nombre_medico, especialidad, credenciales, numero_mpps,
                 logo_url, membrete_url,
                 paciente, consulta, edad_str, medidas, fecha_str,
                 telefono_medico, telefono_config, email):
    """Construye la lista de flowables de una mitad del récipe."""
    items = []

    # 1. Membrete
    items += _membrete(col_w, nombre_medico, especialidad, credenciales,
                       numero_mpps, logo_url, membrete_url)
    items.append(Spacer(1, 1.5 * mm))

    # 2. Línea decorativa teal
    items.append(HRFlowable(width=col_w, thickness=2, color=TEAL, spaceAfter=0))
    items.append(Spacer(1, 2 * mm))

    # 3. Fecha
    items.append(Paragraph(f'Fecha: {fecha_str}', S_FECHA))
    items.append(Spacer(1, 2 * mm))

    # 4. Datos del paciente
    items.append(_bloque_paciente(col_w, paciente, consulta, edad_str, medidas))
    items.append(Spacer(1, 3 * mm))

    # 5. Etiqueta de sección (banda teal)
    lbl_t = Table([[Paragraph(etiqueta, S_ETIQUETA)]], colWidths=[col_w])
    lbl_t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), TEAL),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    items.append(lbl_t)
    items.append(Spacer(1, 3 * mm))

    # 6. Contenido
    texto = contenido_texto.strip() if contenido_texto else ''
    if texto:
        for linea in texto.split('\n'):
            linea = linea.strip()
            if not linea:
                items.append(Spacer(1, 2 * mm))
                continue
            if linea[0] in '-·•' or (
                    len(linea) > 2 and linea[1] in '.):' and linea[0].isdigit()):
                items.append(Paragraph(linea, S_BODY_ITEM))
            else:
                items.append(Paragraph(linea, S_BODY))
    else:
        items.append(Paragraph('—', S_BODY))

    items.append(Spacer(1, 4 * mm))

    # 7. Firma
    items += _firma(nombre_medico, especialidad, numero_mpps,
                    telefono_medico, telefono_config, email)
    return items


# ── Función pública ───────────────────────────────────────────────────────────

def generar_recipe_pdf(consulta, medico, config):
    """
    Genera el récipe médico en PDF y devuelve un io.BytesIO listo para leer.

    Parámetros
    ----------
    consulta : Consulta  — instancia con paciente, tratamiento, indicaciones
    medico   : Usuario   — instancia del médico (título, especialidad, etc.)
    config   : ConfigConsultorio | None — configuración del consultorio
    """
    paciente = consulta.paciente

    # Datos del médico
    titulo        = getattr(medico, 'titulo', '')
    nombre_medico = f'{titulo} {medico.get_full_name() or medico.username}'.strip()
    especialidad  = getattr(medico, 'especialidad', '') or ''
    credenciales  = getattr(medico, 'credenciales', '') or ''
    numero_mpps   = getattr(medico, 'numero_mpps', '') or ''
    telefono_med  = getattr(medico, 'telefono', '') or ''

    # Datos del consultorio
    if config:
        logo_url      = config.get_logo_url()
        membrete_url  = config.get_membrete_url()
        telefono_conf = config.telefono or ''
        email         = config.email or ''
    else:
        logo_url = membrete_url = None
        telefono_conf = email = ''

    # Datos del paciente
    try:
        edad_str = paciente.get_edad_detallada()
    except Exception:
        try:
            edad_str = paciente.get_edad()
        except Exception:
            edad_str = '—'
    if callable(edad_str):
        edad_str = edad_str()
    edad_str = str(edad_str) if edad_str else '—'

    peso_str = f'{consulta.peso} kg' if consulta.peso else ''
    talla_str = f'{consulta.talla} cm' if getattr(consulta, 'talla', None) else ''
    medidas = ' · '.join(filter(None, [peso_str, talla_str]))
    fecha_str = consulta.fecha.strftime('%d/%m/%Y')

    # Argumentos comunes para los bloques
    kwargs = dict(
        col_w=COL_W,
        nombre_medico=nombre_medico,
        especialidad=especialidad,
        credenciales=credenciales,
        numero_mpps=numero_mpps,
        logo_url=logo_url,
        membrete_url=membrete_url,
        paciente=paciente,
        consulta=consulta,
        edad_str=edad_str,
        medidas=medidas,
        fecha_str=fecha_str,
        telefono_medico=telefono_med,
        telefono_config=telefono_conf,
        email=email,
    )

    lado_izq = _bloque_lado('TRATAMIENTO', consulta.tratamiento or '', **kwargs)
    lado_der = _bloque_lado('INDICACIONES', consulta.indicaciones or '', **kwargs)

    # Ensamblado
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    tabla = Table(
        [[lado_izq, '', lado_der]],
        colWidths=[COL_W, SEP, COL_W],
        rowHeights=None,
    )
    tabla.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LINEAFTER',     (0, 0), (0, 0), 1.2, LINEA),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    doc.build([tabla])
    buffer.seek(0)
    return buffer
