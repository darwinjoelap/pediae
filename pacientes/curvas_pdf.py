"""
Generador de PDF para curvas de crecimiento OMS.
Recibe imagen PNG en base64 (del canvas Chart.js) y datos del paciente/médico.
"""
import base64
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

COLOR_TEAL = colors.HexColor('#2AACA8')
COLOR_GRAY = colors.HexColor('#6b7280')
COLOR_LIGHT = colors.HexColor('#f3f4f6')


def generar_pdf_curvas(
    paciente,
    medico,
    consultorio_nombre: str,
    consultorio_especialidad: str,
    grafica_b64: str,
    indicador: str,
    meses_grafica: int = 60,
) -> bytes:
    """
    Genera un PDF con la curva de crecimiento.

    Args:
        paciente: instancia de Paciente
        medico: instancia de Usuario (doctora)
        consultorio_nombre: str
        consultorio_especialidad: str
        grafica_b64: imagen PNG en base64 (sin prefijo data:...)
        indicador: 'peso', 'talla' o 'pc'
        meses_grafica: meses máximos graficados

    Returns:
        bytes del PDF generado
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Encabezado ──────────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        'header',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=COLOR_TEAL,
        spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        'sub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLOR_GRAY,
        spaceAfter=4,
    )
    story.append(Paragraph(consultorio_nombre, header_style))
    story.append(Paragraph(consultorio_especialidad, sub_style))

    titulo_indicador = {'peso': 'Peso para la Edad', 'talla': 'Talla para la Edad', 'pc': 'Perímetro Cefálico para la Edad'}.get(indicador, indicador)
    story.append(Paragraph(f'<b>Curva de Crecimiento OMS — {titulo_indicador}</b>', sub_style))

    # línea separadora
    story.append(Spacer(1, 0.3 * cm))
    story.append(Table([['']], colWidths=[17 * cm],
                        style=TableStyle([('LINEABOVE', (0, 0), (-1, 0), 1, COLOR_TEAL)])))
    story.append(Spacer(1, 0.3 * cm))

    # ── Datos del paciente ───────────────────────────────────────────────────
    label_style = ParagraphStyle('lbl', parent=styles['Normal'], fontSize=9,
                                  fontName='Helvetica-Bold', textColor=COLOR_GRAY)
    val_style = ParagraphStyle('val', parent=styles['Normal'], fontSize=9)

    edad_str = paciente.get_edad_detallada() if hasattr(paciente, 'get_edad_detallada') else ''
    sexo_str = paciente.get_sexo_display() if hasattr(paciente, 'get_sexo_display') and paciente.sexo else ''

    datos_paciente = [
        ['Paciente:', paciente.nombre_completo, 'Sexo:', sexo_str],
        ['Cédula:', getattr(paciente, 'cedula', '—'), 'Edad:', edad_str],
        ['Fecha nac.:', str(paciente.fecha_nacimiento) if paciente.fecha_nacimiento else '—',
         'Grupo:', getattr(paciente, 'grupo_sanguineo', '—') or '—'],
    ]

    pac_table = Table(datos_paciente, colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5.5 * cm])
    pac_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_GRAY),
        ('TEXTCOLOR', (2, 0), (2, -1), COLOR_GRAY),
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [COLOR_LIGHT, colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(pac_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Gráfica ──────────────────────────────────────────────────────────────
    try:
        img_data = base64.b64decode(grafica_b64)
        img_stream = io.BytesIO(img_data)
        img = Image(img_stream, width=17 * cm, height=10 * cm)
        story.append(img)
    except Exception:
        story.append(Paragraph('[Imagen no disponible]', sub_style))

    story.append(Spacer(1, 0.4 * cm))

    # ── Nota percentiles ────────────────────────────────────────────────────
    nota_style = ParagraphStyle('nota', parent=styles['Normal'], fontSize=8,
                                 textColor=COLOR_GRAY, spaceAfter=4)
    story.append(Paragraph(
        'Las líneas de referencia corresponden a los Estándares de Crecimiento Infantil de la OMS (2006): '
        'P3, P15, P50, P85 y P97. La línea teal (P50) representa la mediana poblacional.',
        nota_style
    ))

    # ── Pie médico ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Table([['']], colWidths=[17 * cm],
                        style=TableStyle([('LINEABOVE', (0, 0), (-1, 0), 0.5, COLOR_GRAY)])))
    story.append(Spacer(1, 0.3 * cm))

    medico_nombre = medico.get_full_name() if medico else ''
    titulo_med = getattr(medico, 'titulo', '') or ''

    pie_data = [
        [Paragraph(f'<b>{titulo_med} {medico_nombre}</b>', val_style),
         Paragraph(consultorio_especialidad, sub_style)],
    ]
    pie_table = Table(pie_data, colWidths=[9 * cm, 8 * cm])
    pie_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(pie_table)

    from datetime import date
    story.append(Paragraph(
        f'Generado el {date.today().strftime("%d/%m/%Y")}',
        ParagraphStyle('fecha', parent=styles['Normal'], fontSize=8,
                        textColor=COLOR_GRAY, alignment=TA_RIGHT)
    ))

    doc.build(story)
    return buffer.getvalue()
