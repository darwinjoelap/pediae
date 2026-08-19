from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from ginea.decorators import tenant_login_required as login_required
from datetime import date, timedelta
from pacientes.models import Paciente
from consultas.models import ConsultaServicio
from django.db.models import Sum
import io
import json

import tenant


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


def _get_config(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return 'Ginea', '', '', '', None
    try:
        config = tenant.config
        return (
            config.nombre_medico or tenant.nombre,
            config.especialidad or '',
            config.telefono or tenant.telefono or '',
            config.email or '',
            config.get_logo_url(),
        )
    except Exception:
        return tenant.nombre, '', tenant.telefono or '', '', None


@login_required
def generar_pdf_historial(request, paciente_id):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para generar reportes.')
        return _r(request, '/agenda/')

    paciente = get_object_or_404(Paciente, pk=paciente_id, tenant=request.tenant)
    consultas = paciente.consultas.filter(
        tenant=request.tenant
    ).prefetch_related('adjuntos').order_by('fecha')

    nombre, especialidad, telefono, email, logo_url = _get_config(request)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    import urllib.request

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    teal = colors.HexColor('#2AACA8')
    gris = colors.HexColor('#6B7280')
    oscuro = colors.HexColor('#1F2937')

    e_nombre = ParagraphStyle('nombre', parent=styles['Normal'],
        fontSize=14, fontName='Helvetica-Bold', textColor=oscuro, spaceAfter=2)
    e_sub = ParagraphStyle('sub', parent=styles['Normal'],
        fontSize=9, textColor=gris, spaceAfter=2)
    e_seccion = ParagraphStyle('seccion', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', textColor=teal,
        spaceBefore=10, spaceAfter=3, borderPad=0)
    e_normal = ParagraphStyle('normal', parent=styles['Normal'],
        fontSize=8.5, textColor=oscuro, spaceAfter=2)
    e_pie = ParagraphStyle('pie', parent=styles['Normal'],
        fontSize=7, textColor=gris, alignment=TA_CENTER, spaceBefore=4)

    elementos = []

    logo_img = None
    if logo_url:
        try:
            logo_data = urllib.request.urlopen(logo_url).read()
            logo_buffer = io.BytesIO(logo_data)
            logo_img = Image(logo_buffer, width=3*cm, height=3*cm)
            logo_img.hAlign = 'LEFT'
        except Exception:
            logo_img = None

    info_lines = [Paragraph(nombre, e_nombre)]
    if especialidad:
        info_lines.append(Paragraph(especialidad, e_sub))
    contacto_parts = []
    if telefono:
        contacto_parts.append(f'Tel: {telefono}')
    if email:
        contacto_parts.append(f'Email: {email}')
    if contacto_parts:
        info_lines.append(Paragraph(' · '.join(contacto_parts), e_sub))

    if logo_img:
        membrete_tabla = Table(
            [[logo_img, info_lines]],
            colWidths=[3.5*cm, 13.5*cm]
        )
        membrete_tabla.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 8),
        ]))
        elementos.append(membrete_tabla)
    else:
        for line in info_lines:
            elementos.append(line)

    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width='100%', thickness=2, color=teal))
    elementos.append(Spacer(1, 0.3*cm))

    elementos.append(Paragraph('HISTORIA CLÍNICA', e_seccion))

    datos = [
        ['Paciente:', paciente.nombre_completo, 'Cédula:', paciente.cedula],
        ['F. Nacimiento:',
         paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—',
         'Edad:', f'{paciente.get_edad()} años' if paciente.fecha_nacimiento else '—'],
        ['Teléfono:', paciente.telefono,
         'Estado civil:', paciente.get_estado_civil_display() if paciente.estado_civil else '—'],
        ['Seguro:', paciente.seguro_medico or '—',
         'Ocupación:', paciente.ocupacion or '—'],
    ]
    tabla_datos = Table(datos, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
    tabla_datos.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (2, 0), (2, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('TEXTCOLOR', (3, 0), (3, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elementos.append(tabla_datos)

    antec = []
    if paciente.alergias:
        antec.append(['Alergias:', paciente.alergias])
    if paciente.enfermedades_cronicas:
        antec.append(['Enf. crónicas:', paciente.enfermedades_cronicas])
    if paciente.medicacion_actual:
        antec.append(['Medicación:', paciente.medicacion_actual])
    if paciente.cirugias_previas:
        antec.append(['Cirugías:', paciente.cirugias_previas])
    antec_fam = []
    if paciente.antec_cancer_mama: antec_fam.append('Ca. mama')
    if paciente.antec_cancer_cuello: antec_fam.append('Ca. cuello')
    if paciente.antec_diabetes: antec_fam.append('Diabetes')
    if paciente.antec_hipertension: antec_fam.append('HTA')
    if antec_fam:
        antec.append(['Fam.:', ', '.join(antec_fam)])

    if antec:
        elementos.append(Paragraph('ANTECEDENTES', e_seccion))
        tabla_antec = Table(antec, colWidths=[3.5*cm, 13.5*cm])
        tabla_antec.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), gris),
            ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabla_antec)

    elementos.append(Paragraph('GINECO-OBSTÉTRICO', e_seccion))
    go_data = [
        ['Fórmula obs.:', paciente.get_formula_obstetrica(),
         'FUR:', paciente.fur.strftime('%d/%m/%Y') if paciente.fur else '—'],
        ['Citología:', paciente.ultima_citologia_fecha.strftime('%d/%m/%Y') if paciente.ultima_citologia_fecha else '—',
         'Result.:', paciente.ultima_citologia_resultado or '—'],
        ['VIH:', paciente.get_vih_resultado_display(),
         'VPH vacuna:', 'Sí' if paciente.vph_vacuna else 'No'],
        ['Método AC:', paciente.metodo_anticonceptivo or '—',
         'Menopausia:', 'Sí' if paciente.menopausia else 'No'],
    ]
    tabla_go = Table(go_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
    tabla_go.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (2, 0), (2, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('TEXTCOLOR', (3, 0), (3, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_go)

    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E5E7EB')))
    elementos.append(Paragraph('HISTORIAL DE CONSULTAS', e_seccion))

    if consultas:
        for consulta in consultas:
            tipo = 'CONTROL PRENATAL' if consulta.es_prenatal else 'CONSULTA'
            bloque = []

            header_data = [[
                Paragraph(f'<b>{consulta.fecha.strftime("%d/%m/%Y")}</b>', e_normal),
                Paragraph(f'<b>{tipo}</b>', e_normal),
                Paragraph(f'<b>Lugar:</b> {consulta.lugar.nombre if consulta.lugar else "—"}', e_normal),
            ]]
            header_tabla = Table(header_data, colWidths=[4*cm, 5*cm, 8*cm])
            header_tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ]))
            bloque.append(header_tabla)

            filas_consulta = []
            if consulta.motivo_consulta:
                filas_consulta.append(['Motivo:', consulta.motivo_consulta])
            if consulta.diagnostico:
                filas_consulta.append(['Diagnóstico:', consulta.diagnostico])
            if consulta.tratamiento:
                filas_consulta.append(['Tratamiento:', consulta.tratamiento])
            if consulta.peso or consulta.tension_arterial:
                sv = []
                if consulta.peso: sv.append(f'Peso: {consulta.peso} kg')
                if consulta.tension_arterial: sv.append(f'TA: {consulta.tension_arterial}')
                filas_consulta.append(['Signos vitales:', ' · '.join(sv)])
            if consulta.observaciones:
                filas_consulta.append(['Observaciones:', consulta.observaciones])
            if consulta.proxima_cita:
                filas_consulta.append(['Próxima cita:', consulta.proxima_cita.strftime('%d/%m/%Y')])

            if consulta.es_prenatal:
                if consulta.semanas_gestacion:
                    filas_consulta.append(['Semanas gest.:', str(consulta.semanas_gestacion)])
                if consulta.fpp:
                    filas_consulta.append(['FPP:', consulta.fpp.strftime('%d/%m/%Y')])
                if consulta.altura_uterina:
                    filas_consulta.append(['Altura uterina:', f'{consulta.altura_uterina} cm'])
                if consulta.fcf:
                    filas_consulta.append(['FCF:', f'{consulta.fcf} lpm'])
                if consulta.presentacion_fetal:
                    filas_consulta.append(['Presentación:', consulta.presentacion_fetal])
                if consulta.laboratorio:
                    filas_consulta.append(['Laboratorio:', consulta.laboratorio])

            if filas_consulta:
                tabla_c = Table(filas_consulta, colWidths=[3.5*cm, 13.5*cm])
                tabla_c.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 0), (0, -1), gris),
                    ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                bloque.append(tabla_c)

            adjuntos = consulta.adjuntos.all()
            if adjuntos:
                adj_text = ' · '.join([adj.nombre_original for adj in adjuntos])
                bloque.append(Paragraph(f'Adjuntos: {adj_text}', e_normal))

            bloque.append(Spacer(1, 0.2*cm))
            elementos.append(KeepTogether(bloque))
    else:
        elementos.append(Paragraph('Sin consultas registradas.', e_normal))

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E5E7EB')))
    pie_parts = [f'Generado el {date.today().strftime("%d/%m/%Y")}', nombre]
    if especialidad:
        pie_parts.append(especialidad)
    elementos.append(Paragraph(' · '.join(pie_parts), e_pie))

    doc.build(elementos)
    buffer.seek(0)

    nombre_archivo = f'historial_{paciente.cedula}_{date.today().isoformat()}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response


# REEMPLAZA la función estadisticas en reportes/views.py
# Busca "@login_required\ndef estadisticas(request):" y reemplaza toda la función

@login_required
def estadisticas(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')

    tenant = request.tenant
    from agenda.models import Cita
    from consultas.models import Consulta
    from accounts.models import Usuario

    hoy = date.today()
    fecha_desde_str = request.GET.get('desde', (hoy - timedelta(days=365)).isoformat())
    fecha_hasta_str = request.GET.get('hasta', hoy.isoformat())
    medico_id = request.GET.get('medico', '')

    try:
        fecha_desde = date.fromisoformat(fecha_desde_str)
        fecha_hasta = date.fromisoformat(fecha_hasta_str)
    except ValueError:
        fecha_desde = hoy - timedelta(days=365)
        fecha_hasta = hoy

    # Lista de médicos del tenant para el selector
    medicos = Usuario.objects.filter(tenant=tenant, rol='medico')
    medico_seleccionado = None
    if medico_id:
        try:
            medico_seleccionado = Usuario.objects.get(pk=medico_id, tenant=tenant)
        except Usuario.DoesNotExist:
            medico_id = ''

    pacientes = Paciente.objects.filter(tenant=tenant)
    citas = Cita.objects.filter(tenant=tenant, fecha__range=[fecha_desde, fecha_hasta])
    consultas = Consulta.objects.filter(tenant=tenant, fecha__range=[fecha_desde, fecha_hasta])

    # Filtrar por médico si se seleccionó
    if medico_seleccionado:
        consultas = consultas.filter(medico=medico_seleccionado)
        citas = citas.filter(creado_por=medico_seleccionado)

    # Actividad clínica
    stats_citas = {
        'total': citas.count(),
        'atendidas': citas.filter(estado='atendida').count(),
        'canceladas': citas.filter(estado='cancelada').count(),
        'no_asistio': citas.filter(estado='no_asistio').count(),
        'programadas': citas.filter(estado__in=['programada', 'confirmada']).count(),
    }
    stats_citas['tasa_asistencia'] = round(
        stats_citas['atendidas'] / stats_citas['total'] * 100, 1
    ) if stats_citas['total'] > 0 else 0

    stats_consultas = {
        'total': consultas.count(),
        'prenatales': consultas.filter(es_prenatal=True).count(),
        'regulares': consultas.filter(es_prenatal=False).count(),
    }

    # Ingresos
    consultas_ids = consultas.values_list('id', flat=True)
    total_ingresos_usd = ConsultaServicio.objects.filter(
        consulta_id__in=consultas_ids,
        consulta__pagado=True,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    ingresos_pendientes = ConsultaServicio.objects.filter(
        consulta_id__in=consultas_ids,
        consulta__pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0
    # Ingresos por procedimientos
    from consultas.models import Procedimiento
    procedimientos_qs = Procedimiento.objects.filter(
    tenant=tenant,
        fecha__range=[fecha_desde, fecha_hasta],
    )
    if medico_seleccionado:
        procedimientos_qs = procedimientos_qs.filter(medico=medico_seleccionado)

    total_ingresos_proc = procedimientos_qs.filter(
        pagado=True
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    ingresos_pendientes_proc = procedimientos_qs.filter(
        pagado=False
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    total_ingresos_usd = total_ingresos_usd + total_ingresos_proc
    ingresos_pendientes = ingresos_pendientes + ingresos_pendientes_proc
    servicios_top = ConsultaServicio.objects.filter(
        consulta_id__in=consultas_ids,
    ).values('servicio__nombre').annotate(
        total=Count('id'),
        ingresos=Sum('precio_usd'),
    ).order_by('-total')[:8]

    ingresos_mes = ConsultaServicio.objects.filter(
        consulta_id__in=consultas_ids,
        consulta__pagado=True,
    ).annotate(
        mes=TruncMonth('consulta__fecha')
    ).values('mes').annotate(
        total=Sum('precio_usd')
    ).order_by('mes')

    # Pacientes nuevas por mes
    pacientes_nuevas = pacientes.filter(
        creado_en__date__range=[fecha_desde, fecha_hasta]
    ).annotate(mes=TruncMonth('creado_en')).values('mes').annotate(
        total=Count('id')
    ).order_by('mes')

    # Citas por mes
    citas_por_mes = citas.annotate(
        mes=TruncMonth('fecha')
    ).values('mes').annotate(
        total=Count('id'),
        atendidas=Count('id', filter=Q(estado='atendida')),
    ).order_by('mes')

    # Consultas por mes
    consultas_por_mes = consultas.annotate(
        mes=TruncMonth('fecha')
    ).values('mes').annotate(total=Count('id')).order_by('mes')

    # Perfil de pacientes
    edades = {'0-20': 0, '21-30': 0, '31-40': 0, '41-50': 0, '51-60': 0, '60+': 0}
    for p in pacientes:
        if not p.fecha_nacimiento:
            continue
        edad = p.get_edad()
        if not isinstance(edad, int):
            continue
        if edad <= 20: edades['0-20'] += 1
        elif edad <= 30: edades['21-30'] += 1
        elif edad <= 40: edades['31-40'] += 1
        elif edad <= 50: edades['41-50'] += 1
        elif edad <= 60: edades['51-60'] += 1
        else: edades['60+'] += 1

    metodos = pacientes.exclude(
        metodo_anticonceptivo=''
    ).values('metodo_anticonceptivo').annotate(
        total=Count('id')
    ).order_by('-total')[:8]

    vih = pacientes.values('vih_resultado').annotate(total=Count('id'))
    vih_data = {v['vih_resultado']: v['total'] for v in vih}

    vph_vacuna = pacientes.filter(vph_vacuna=True).count()
    vph_diagnostico = pacientes.filter(vph_diagnostico=True).count()
    vph_sin_vacuna = pacientes.count() - vph_vacuna

    con_citologia = pacientes.exclude(ultima_citologia_fecha__isnull=True).count()
    sin_citologia = pacientes.filter(ultima_citologia_fecha__isnull=True).count()

    antecedentes = {
        'Cáncer de mama': pacientes.filter(antec_cancer_mama=True).count(),
        'Cáncer cervical': pacientes.filter(antec_cancer_cuello=True).count(),
        'Diabetes': pacientes.filter(antec_diabetes=True).count(),
        'Hipertensión': pacientes.filter(antec_hipertension=True).count(),
    }

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    citas_por_dia = [0] * 7
    for cita in citas:
        citas_por_dia[cita.fecha.weekday()] += 1

    prenatales = consultas.filter(es_prenatal=True)
    semanas_prom = 0
    if prenatales.exists():
        semanas_vals = [c.semanas_gestacion for c in prenatales if c.semanas_gestacion]
        semanas_prom = round(sum(semanas_vals) / len(semanas_vals), 1) if semanas_vals else 0

    prenatales_por_mes = prenatales.annotate(
        mes=TruncMonth('fecha')
    ).values('mes').annotate(total=Count('id')).order_by('mes')

    def meses_labels(qs):
        return [item['mes'].strftime('%b %Y') for item in qs]

    charts = {
        'citas_meses': {
            'labels': meses_labels(citas_por_mes),
            'total': [item['total'] for item in citas_por_mes],
            'atendidas': [item['atendidas'] for item in citas_por_mes],
        },
        'consultas_meses': {
            'labels': meses_labels(consultas_por_mes),
            'data': [item['total'] for item in consultas_por_mes],
        },
        'pacientes_nuevas': {
            'labels': meses_labels(pacientes_nuevas),
            'data': [item['total'] for item in pacientes_nuevas],
        },
        'edades': {
            'labels': list(edades.keys()),
            'data': list(edades.values()),
        },
        'metodos': {
            'labels': [m['metodo_anticonceptivo'] for m in metodos],
            'data': [m['total'] for m in metodos],
        },
        'vih': {
            'labels': ['Negativo', 'Positivo', 'No realizado'],
            'data': [
                vih_data.get('negativo', 0),
                vih_data.get('positivo', 0),
                vih_data.get('no_realizado', 0),
            ],
        },
        'vph': {
            'labels': ['Vacunadas', 'Sin vacuna', 'Con diagnóstico VPH'],
            'data': [vph_vacuna, vph_sin_vacuna, vph_diagnostico],
        },
        'citologia': {
            'labels': ['Con citología', 'Sin citología'],
            'data': [con_citologia, sin_citologia],
        },
        'antecedentes': {
            'labels': list(antecedentes.keys()),
            'data': list(antecedentes.values()),
        },
        'dias_semana': {
            'labels': dias_semana,
            'data': citas_por_dia,
        },
        'prenatales_meses': {
            'labels': meses_labels(prenatales_por_mes),
            'data': [item['total'] for item in prenatales_por_mes],
        },
        'ingresos_mes': {
            'labels': [item['mes'].strftime('%b %Y') for item in ingresos_mes],
            'data': [float(item['total']) for item in ingresos_mes],
        },
        'servicios_top': {
            'labels': [item['servicio__nombre'] for item in servicios_top],
            'data': [item['total'] for item in servicios_top],
            'ingresos': [float(item['ingresos']) for item in servicios_top],
        },
    }

    return render(request, 'reportes/estadisticas.html', {
        'stats_citas': stats_citas,
        'stats_consultas': stats_consultas,
        'total_pacientes': pacientes.count(),
        'semanas_prom': semanas_prom,
        'charts': json.dumps(charts, default=str),
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'vph_vacuna': vph_vacuna,
        'vph_sin_vacuna': vph_sin_vacuna,
        'vph_diagnostico': vph_diagnostico,
        'con_citologia': con_citologia,
        'sin_citologia': sin_citologia,
        'total_ingresos_usd': total_ingresos_usd,
        'ingresos_pendientes': ingresos_pendientes,
        'medicos': medicos,
        'medico_id': medico_id,
        'medico_seleccionado': medico_seleccionado,
    })


@login_required
def estadisticas_pdf(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')

    tenant = request.tenant
    from agenda.models import Cita
    from consultas.models import Consulta
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER

    hoy = date.today()
    fecha_desde_str = request.GET.get('desde', (hoy - timedelta(days=365)).isoformat())
    fecha_hasta_str = request.GET.get('hasta', hoy.isoformat())
    try:
        fecha_desde = date.fromisoformat(fecha_desde_str)
        fecha_hasta = date.fromisoformat(fecha_hasta_str)
    except ValueError:
        fecha_desde = hoy - timedelta(days=365)
        fecha_hasta = hoy

    pacientes = Paciente.objects.filter(tenant=tenant)
    citas = Cita.objects.filter(tenant=tenant, fecha__range=[fecha_desde, fecha_hasta])
    consultas = Consulta.objects.filter(tenant=tenant, fecha__range=[fecha_desde, fecha_hasta])

    nombre, especialidad, telefono, email, logo_url = _get_config(request)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    teal = colors.HexColor('#2AACA8')
    gris = colors.HexColor('#6B7280')
    oscuro = colors.HexColor('#1F2937')

    e_titulo = ParagraphStyle('t', parent=styles['Normal'],
        fontSize=14, fontName='Helvetica-Bold', textColor=oscuro, spaceAfter=2)
    e_sub = ParagraphStyle('s', parent=styles['Normal'],
        fontSize=9, textColor=gris, spaceAfter=2)
    e_seccion = ParagraphStyle('sec', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=teal,
        spaceBefore=12, spaceAfter=4)
    e_normal = ParagraphStyle('n', parent=styles['Normal'],
        fontSize=9, textColor=oscuro, spaceAfter=2)
    e_pie = ParagraphStyle('p', parent=styles['Normal'],
        fontSize=7, textColor=gris, alignment=TA_CENTER, spaceBefore=4)

    elementos = []

    elementos.append(Paragraph(nombre, e_titulo))
    if especialidad:
        elementos.append(Paragraph(especialidad, e_sub))
    contacto = ' · '.join(filter(None, [telefono, email]))
    if contacto:
        elementos.append(Paragraph(contacto, e_sub))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(HRFlowable(width='100%', thickness=2, color=teal))
    elementos.append(Spacer(1, 0.2*cm))

    elementos.append(Paragraph('REPORTE ESTADÍSTICO', e_seccion))
    elementos.append(Paragraph(
        f'Período: {fecha_desde.strftime("%d/%m/%Y")} — {fecha_hasta.strftime("%d/%m/%Y")}',
        e_normal
    ))
    elementos.append(Spacer(1, 0.3*cm))

    total_citas = citas.count()
    atendidas = citas.filter(estado='atendida').count()
    tasa = round(atendidas / total_citas * 100, 1) if total_citas > 0 else 0
    vph_vacuna = pacientes.filter(vph_vacuna=True).count()
    vph_dx = pacientes.filter(vph_diagnostico=True).count()
    con_cito = pacientes.exclude(ultima_citologia_fecha__isnull=True).count()

    total_ingresos = ConsultaServicio.objects.filter(
        consulta__tenant=tenant,
        consulta__fecha__range=[fecha_desde, fecha_hasta],
        consulta__pagado=True,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    ingresos_pendientes = ConsultaServicio.objects.filter(
        consulta__tenant=tenant,
        consulta__fecha__range=[fecha_desde, fecha_hasta],
        consulta__pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    elementos.append(Paragraph('RESUMEN GENERAL', e_seccion))
    resumen = [
        ['Total pacientes registradas', str(pacientes.count())],
        ['Total citas en el período', str(total_citas)],
        ['Citas atendidas', f'{atendidas} ({tasa}%)'],
        ['Citas canceladas', str(citas.filter(estado='cancelada').count())],
        ['Citas no asistidas', str(citas.filter(estado='no_asistio').count())],
        ['Consultas registradas', str(consultas.count())],
        ['Controles prenatales', str(consultas.filter(es_prenatal=True).count())],
    ]
    tabla_r = Table(resumen, colWidths=[10*cm, 7*cm])
    tabla_r.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    elementos.append(tabla_r)

    elementos.append(Paragraph('INGRESOS', e_seccion))
    ing_data = [
        ['Ingresos cobrados', f'${total_ingresos} USD'],
        ['Ingresos pendientes', f'${ingresos_pendientes} USD'],
    ]
    tabla_ing = Table(ing_data, colWidths=[10*cm, 7*cm])
    tabla_ing.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_ing)

    elementos.append(Paragraph('VPH Y CITOLOGÍA', e_seccion))
    vph_data = [
        ['Pacientes vacunadas VPH', str(vph_vacuna)],
        ['Pacientes sin vacuna VPH', str(pacientes.count() - vph_vacuna)],
        ['Pacientes con diagnóstico VPH', str(vph_dx)],
        ['Pacientes con citología registrada', str(con_cito)],
        ['Pacientes sin citología', str(pacientes.filter(ultima_citologia_fecha__isnull=True).count())],
    ]
    tabla_vph = Table(vph_data, colWidths=[10*cm, 7*cm])
    tabla_vph.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_vph)

    elementos.append(Paragraph('ANTECEDENTES FAMILIARES', e_seccion))
    antec_data = [
        ['Cáncer de mama', str(pacientes.filter(antec_cancer_mama=True).count())],
        ['Cáncer cervical', str(pacientes.filter(antec_cancer_cuello=True).count())],
        ['Diabetes', str(pacientes.filter(antec_diabetes=True).count())],
        ['Hipertensión', str(pacientes.filter(antec_hipertension=True).count())],
    ]
    tabla_antec = Table(antec_data, colWidths=[10*cm, 7*cm])
    tabla_antec.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_antec)

    elementos.append(Paragraph('DISTRIBUCIÓN POR EDAD', e_seccion))
    edades = {'0-20': 0, '21-30': 0, '31-40': 0, '41-50': 0, '51-60': 0, '60+': 0}
    rangos = [(0,20,'0-20'),(21,30,'21-30'),(31,40,'31-40'),(41,50,'41-50'),(51,60,'51-60'),(61,999,'60+')]
    for p in pacientes:
        if not p.fecha_nacimiento:
            continue
        edad = p.get_edad()
        if not isinstance(edad, int):
            continue
        for mn, mx, lbl in rangos:
            if mn <= edad <= mx:
                edades[lbl] += 1
                break
    edad_data = [[rango, str(cnt)] for rango, cnt in edades.items()]
    tabla_edad = Table(edad_data, colWidths=[10*cm, 7*cm])
    tabla_edad.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), gris),
        ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_edad)

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E5E7EB')))
    elementos.append(Paragraph(
        f'Generado el {date.today().strftime("%d/%m/%Y")} · {nombre}',
        e_pie
    ))

    doc.build(elementos)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="estadisticas_{fecha_desde}_{fecha_hasta}.pdf"'
    return response

@login_required
def pagos_pendientes(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')

    tenant = request.tenant
    from consultas.models import Consulta, ConsultaServicio, Procedimiento
    from django.db.models import Sum

    consultas = Consulta.objects.filter(
        tenant=tenant, pagado=False, servicios_usados__isnull=False,
    ).select_related('paciente', 'medico').prefetch_related(
        'servicios_usados__servicio'
    ).distinct().order_by('-fecha')

    procedimientos = Procedimiento.objects.filter(
        tenant=tenant, pagado=False,
    ).select_related('paciente', 'servicio').order_by('-fecha')

    total_consultas = ConsultaServicio.objects.filter(
        consulta__tenant=tenant, consulta__pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    total_procedimientos = Procedimiento.objects.filter(
        tenant=tenant, pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    total_pendiente = total_consultas + total_procedimientos

    return render(request, 'reportes/pagos_pendientes.html', {
        'consultas': consultas,
        'procedimientos': procedimientos,
        'total_pendiente': total_pendiente,
    })