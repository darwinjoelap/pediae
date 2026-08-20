from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from pediae.decorators import tenant_login_required as login_required
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
        return 'Pediae', '', '', '', None
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

    # Cédula: puede ser del paciente o del representante si no está cedulado
    cedula_display = paciente.cedula if not paciente.no_cedulado else f'S/C (Rep: {paciente.cedula_representante})'
    datos = [
        ['Paciente:', paciente.nombre_completo,
         'Cédula:', cedula_display],
        ['F. Nacimiento:',
         paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '—',
         'Edad:', paciente.get_edad_detallada()],
        ['Teléfono:', paciente.telefono,
         'Sexo:', paciente.get_sexo_display() if paciente.sexo else '—'],
        ['Seguro:', paciente.seguro_medico or '—',
         'Grupo sang.:', paciente.grupo_sanguineo or '—'],
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

    # Representante
    if paciente.no_cedulado or paciente.nombre_representante:
        rep_lineas = []
        if paciente.nombre_representante:
            fil = paciente.get_filiacion_representante_display() if paciente.filiacion_representante else 'Representante'
            rep_lineas.append([f'{fil}:', paciente.nombre_representante])
        if paciente.cedula_representante:
            rep_lineas.append(['C.I. Rep.:', paciente.cedula_representante])
        if paciente.telefono_representante:
            rep_lineas.append(['Tel. Rep.:', paciente.telefono_representante])
        if rep_lineas:
            elementos.append(Paragraph('REPRESENTANTE', e_seccion))
            tabla_rep = Table(rep_lineas, colWidths=[3.5*cm, 13.5*cm])
            tabla_rep.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), gris),
                ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elementos.append(tabla_rep)

    # Antecedentes personales y familiares
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
    if paciente.antec_diabetes: antec_fam.append('Diabetes')
    if paciente.antec_hipertension: antec_fam.append('HTA')
    if paciente.antec_cardiopatias: antec_fam.append('Cardiopatías')
    if paciente.antec_epilepsia: antec_fam.append('Epilepsia')
    if paciente.antec_asma_atopia: antec_fam.append('Asma/Atopía')
    if antec_fam:
        antec.append(['Antec. fam.:', ', '.join(antec_fam)])

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

    # Antecedentes perinatales
    perinatal = []
    if paciente.antec_embarazo:
        perinatal.append(['Embarazo:', paciente.antec_embarazo])
    if paciente.antec_parto:
        perinatal.append(['Parto:', paciente.antec_parto])
    if paciente.antec_neonatal:
        perinatal.append(['Neonatal:', paciente.antec_neonatal])
    if perinatal:
        elementos.append(Paragraph('ANTECEDENTES PERINATALES', e_seccion))
        tabla_perinatal = Table(perinatal, colWidths=[3.5*cm, 13.5*cm])
        tabla_perinatal.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), gris),
            ('TEXTCOLOR', (1, 0), (1, -1), oscuro),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabla_perinatal)

    # Vacunas aplicadas
    from pacientes.models import VacunaAplicada
    vacunas_aplicadas = VacunaAplicada.objects.filter(
        paciente=paciente, tenant=request.tenant
    ).select_related('vacuna').order_by('fecha')
    if vacunas_aplicadas.exists():
        elementos.append(Paragraph('VACUNAS APLICADAS', e_seccion))
        vac_filas = [['Vacuna', 'Dosis', 'Fecha', 'Lote']]
        for va in vacunas_aplicadas:
            vac_filas.append([
                va.vacuna.nombre,
                f'd{va.vacuna.dosis_numero}',
                va.fecha.strftime('%d/%m/%Y'),
                va.lote or '—',
            ])
        tabla_vac = Table(vac_filas, colWidths=[6*cm, 2*cm, 3.5*cm, 5.5*cm])
        tabla_vac.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), oscuro),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#E5E7EB')),
        ]))
        elementos.append(tabla_vac)

    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E5E7EB')))
    elementos.append(Paragraph('HISTORIAL DE CONSULTAS', e_seccion))

    if consultas:
        for consulta in consultas:
            tipo = consulta.get_tipo_consulta_display() if hasattr(consulta, 'get_tipo_consulta_display') else 'CONSULTA'
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

            # Antropometría pediátrica
            antrop = []
            if consulta.peso:
                txt = f'{consulta.peso} kg'
                if consulta.percentil_peso: txt += f'  (P{consulta.percentil_peso})'
                antrop.append(txt)
            if consulta.talla:
                txt = f'{consulta.talla} cm'
                if consulta.percentil_talla: txt += f'  (P{consulta.percentil_talla})'
                antrop.append(txt)
            if consulta.perimetro_cefalico:
                txt = f'PC {consulta.perimetro_cefalico} cm'
                if consulta.percentil_pc: txt += f'  (P{consulta.percentil_pc})'
                antrop.append(txt)
            if antrop:
                filas_consulta.append(['Antropometría:', ' · '.join(antrop)])
            if consulta.clasificacion_nutricional:
                filas_consulta.append(['Estado nutr.:', consulta.get_clasificacion_nutricional_display()])

            # Signos vitales
            sv = []
            if consulta.frecuencia_cardiaca: sv.append(f'FC: {consulta.frecuencia_cardiaca} lpm')
            if consulta.frecuencia_respiratoria: sv.append(f'FR: {consulta.frecuencia_respiratoria} rpm')
            if consulta.temperatura: sv.append(f'T°: {consulta.temperatura} °C')
            if consulta.saturacion_oxigeno: sv.append(f'SatO₂: {consulta.saturacion_oxigeno}%')
            if consulta.tension_arterial: sv.append(f'TA: {consulta.tension_arterial}')
            if sv:
                filas_consulta.append(['Signos vitales:', ' · '.join(sv)])

            if consulta.desarrollo_psicomotor:
                filas_consulta.append(['Desarrollo:', consulta.desarrollo_psicomotor])
            if consulta.laboratorio:
                filas_consulta.append(['Laboratorio:', consulta.laboratorio])
            if consulta.observaciones:
                filas_consulta.append(['Observaciones:', consulta.observaciones])
            if consulta.proxima_cita:
                filas_consulta.append(['Próxima cita:', consulta.proxima_cita.strftime('%d/%m/%Y')])

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


@login_required
def estadisticas(request):
    if not request.user.es_medico:
        return _r(request, '/agenda/')

    _tenant = request.tenant
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

    medicos = Usuario.objects.filter(tenant=_tenant, rol='medico')
    medico_seleccionado = None
    if medico_id:
        try:
            medico_seleccionado = Usuario.objects.get(pk=medico_id, tenant=_tenant)
        except Usuario.DoesNotExist:
            medico_id = ''

    pacientes = Paciente.objects.filter(tenant=_tenant)
    citas = Cita.objects.filter(tenant=_tenant, fecha__range=[fecha_desde, fecha_hasta])
    consultas = Consulta.objects.filter(tenant=_tenant, fecha__range=[fecha_desde, fecha_hasta])

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

    # Consultas por tipo (pediátrico)
    tipos_consulta = consultas.values('tipo_consulta').annotate(
        total=Count('id')
    ).order_by('-total')
    tipos_dict = {t['tipo_consulta']: t['total'] for t in tipos_consulta}

    # Usar get_tipo_consulta_display equivalente — mapear los choices manualmente
    TIPO_LABELS = {
        'control': 'Control',
        'enfermedad': 'Enfermedad',
        'urgencia': 'Urgencia',
        'procedimiento': 'Procedimiento',
        'otro': 'Otro',
    }
    stats_consultas = {
        'total': consultas.count(),
        'por_tipo': [
            {'tipo': TIPO_LABELS.get(k, k), 'total': v}
            for k, v in tipos_dict.items()
        ],
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

    from consultas.models import Procedimiento
    procedimientos_qs = Procedimiento.objects.filter(
        tenant=_tenant,
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

    # Pacientes nuevos por mes
    pacientes_nuevos = pacientes.filter(
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

    # Distribución por edad (pediátrica: 0-1, 1-3, 3-6, 6-10, 10-15, 15+)
    edades = {'0-1': 0, '1-3': 0, '3-6': 0, '6-10': 0, '10-15': 0, '15+': 0}
    sexos = {'M': 0, 'F': 0, 'otro': 0}
    for p in pacientes:
        # Edad en años
        if p.fecha_nacimiento:
            from dateutil.relativedelta import relativedelta
            delta = relativedelta(date.today(), p.fecha_nacimiento)
            edad_anios = delta.years
            if edad_anios < 1: edades['0-1'] += 1
            elif edad_anios < 3: edades['1-3'] += 1
            elif edad_anios < 6: edades['3-6'] += 1
            elif edad_anios < 10: edades['6-10'] += 1
            elif edad_anios < 15: edades['10-15'] += 1
            else: edades['15+'] += 1
        # Sexo
        if hasattr(p, 'sexo'):
            if p.sexo == 'M': sexos['M'] += 1
            elif p.sexo == 'F': sexos['F'] += 1
            else: sexos['otro'] += 1

    # Estado nutricional
    nutricion = consultas.exclude(
        clasificacion_nutricional=''
    ).exclude(
        clasificacion_nutricional__isnull=True
    ).values('clasificacion_nutricional').annotate(
        total=Count('id')
    ).order_by('-total')

    NUTRICION_LABELS = {
        'normal': 'Normal',
        'desnutricion_leve': 'Desnutrición leve',
        'desnutricion_moderada': 'Desnutrición moderada',
        'desnutricion_severa': 'Desnutrición severa',
        'sobrepeso': 'Sobrepeso',
        'obesidad': 'Obesidad',
        'talla_baja': 'Talla baja',
        'macrosomia': 'Macrosomía',
    }

    # Antecedentes familiares pediátricos
    antecedentes = {
        'Diabetes': pacientes.filter(antec_diabetes=True).count(),
        'Hipertensión': pacientes.filter(antec_hipertension=True).count(),
        'Cardiopatías': pacientes.filter(antec_cardiopatias=True).count(),
        'Epilepsia': pacientes.filter(antec_epilepsia=True).count(),
        'Asma/Atopía': pacientes.filter(antec_asma_atopia=True).count(),
    }

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    citas_por_dia = [0] * 7
    for cita in citas:
        citas_por_dia[cita.fecha.weekday()] += 1

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
        'pacientes_nuevos': {
            'labels': meses_labels(pacientes_nuevos),
            'data': [item['total'] for item in pacientes_nuevos],
        },
        'edades': {
            'labels': list(edades.keys()),
            'data': list(edades.values()),
        },
        'sexos': {
            'labels': ['Masculino', 'Femenino', 'Otro'],
            'data': [sexos['M'], sexos['F'], sexos['otro']],
        },
        'tipos_consulta': {
            'labels': [TIPO_LABELS.get(t['tipo_consulta'], t['tipo_consulta']) for t in tipos_consulta],
            'data': [t['total'] for t in tipos_consulta],
        },
        'nutricion': {
            'labels': [NUTRICION_LABELS.get(n['clasificacion_nutricional'], n['clasificacion_nutricional']) for n in nutricion],
            'data': [n['total'] for n in nutricion],
        },
        'antecedentes': {
            'labels': list(antecedentes.keys()),
            'data': list(antecedentes.values()),
        },
        'dias_semana': {
            'labels': dias_semana,
            'data': citas_por_dia,
        },
        'ingresos_mes': {
            'labels': [item['mes'].strftime('%b %Y') for item in ingresos_mes],
            'data': [float(item['total']) for item in ingresos_mes],
        },
        'servicios_top': {
            'labels': [item['servicio__nombre'] for item in servicios_top],
            'data': [item['total'] for item in servicios_top],
            'ingresos': [float(item['ingresos'] or 0) for item in servicios_top],
        },
    }

    return render(request, 'reportes/estadisticas.html', {
        'stats_citas': stats_citas,
        'stats_consultas': stats_consultas,
        'total_pacientes': pacientes.count(),
        'charts': json.dumps(charts, default=str),
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
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

    _tenant = request.tenant
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

    pacientes = Paciente.objects.filter(tenant=_tenant)
    citas = Cita.objects.filter(tenant=_tenant, fecha__range=[fecha_desde, fecha_hasta])
    consultas = Consulta.objects.filter(tenant=_tenant, fecha__range=[fecha_desde, fecha_hasta])

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

    total_ingresos = ConsultaServicio.objects.filter(
        consulta__tenant=_tenant,
        consulta__fecha__range=[fecha_desde, fecha_hasta],
        consulta__pagado=True,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    ingresos_pendientes = ConsultaServicio.objects.filter(
        consulta__tenant=_tenant,
        consulta__fecha__range=[fecha_desde, fecha_hasta],
        consulta__pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    # Consultas por tipo
    TIPO_LABELS = {
        'control': 'Control',
        'enfermedad': 'Enfermedad',
        'urgencia': 'Urgencia',
        'procedimiento': 'Procedimiento',
        'otro': 'Otro',
    }
    tipos_consulta = consultas.values('tipo_consulta').annotate(
        total=Count('id')
    ).order_by('-total')

    elementos.append(Paragraph('RESUMEN GENERAL', e_seccion))
    resumen = [
        ['Total pacientes registrados', str(pacientes.count())],
        ['Total citas en el período', str(total_citas)],
        ['Citas atendidas', f'{atendidas} ({tasa}%)'],
        ['Citas canceladas', str(citas.filter(estado='cancelada').count())],
        ['Citas no asistidas', str(citas.filter(estado='no_asistio').count())],
        ['Consultas registradas', str(consultas.count())],
    ]
    for t in tipos_consulta:
        lbl = TIPO_LABELS.get(t['tipo_consulta'], t['tipo_consulta'])
        resumen.append([f'  · {lbl}', str(t['total'])])

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

    elementos.append(Paragraph('ANTECEDENTES FAMILIARES', e_seccion))
    antec_data = [
        ['Diabetes', str(pacientes.filter(antec_diabetes=True).count())],
        ['Hipertensión', str(pacientes.filter(antec_hipertension=True).count())],
        ['Cardiopatías', str(pacientes.filter(antec_cardiopatias=True).count())],
        ['Epilepsia', str(pacientes.filter(antec_epilepsia=True).count())],
        ['Asma/Atopía', str(pacientes.filter(antec_asma_atopia=True).count())],
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
    edades = {'0-1': 0, '1-3': 0, '3-6': 0, '6-10': 0, '10-15': 0, '15+': 0}
    for p in pacientes:
        if not p.fecha_nacimiento:
            continue
        from dateutil.relativedelta import relativedelta
        edad_anios = relativedelta(date.today(), p.fecha_nacimiento).years
        if edad_anios < 1: edades['0-1'] += 1
        elif edad_anios < 3: edades['1-3'] += 1
        elif edad_anios < 6: edades['3-6'] += 1
        elif edad_anios < 10: edades['6-10'] += 1
        elif edad_anios < 15: edades['10-15'] += 1
        else: edades['15+'] += 1
    edad_data = [[f'{rango} años', str(cnt)] for rango, cnt in edades.items()]
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

    _tenant = request.tenant
    from consultas.models import Consulta, ConsultaServicio, Procedimiento
    from django.db.models import Sum

    consultas = Consulta.objects.filter(
        tenant=_tenant, pagado=False, servicios_usados__isnull=False,
    ).select_related('paciente', 'medico').prefetch_related(
        'servicios_usados__servicio'
    ).distinct().order_by('-fecha')

    procedimientos = Procedimiento.objects.filter(
        tenant=_tenant, pagado=False,
    ).select_related('paciente', 'servicio').order_by('-fecha')

    total_consultas = ConsultaServicio.objects.filter(
        consulta__tenant=_tenant, consulta__pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    total_procedimientos = Procedimiento.objects.filter(
        tenant=_tenant, pagado=False,
    ).aggregate(total=Sum('precio_usd'))['total'] or 0

    total_pendiente = total_consultas + total_procedimientos

    return render(request, 'reportes/pagos_pendientes.html', {
        'consultas': consultas,
        'procedimientos': procedimientos,
        'total_pendiente': total_pendiente,
    })
