from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from ginea.decorators import tenant_login_required as login_required
from pacientes.models import Paciente
from agenda.models import Cita
from .models import Consulta, AdjuntoConsulta, ConsultaServicio
from .forms import ConsultaForm


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


@login_required
def nueva_consulta(request, paciente_id):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para registrar consultas.')
        return _r(request, '/agenda/')

    paciente = get_object_or_404(Paciente, pk=paciente_id, tenant=request.tenant)
    cita_id = request.GET.get('cita')
    cita = None
    if cita_id:
        cita = get_object_or_404(Cita, pk=cita_id, tenant=request.tenant)
    else:
        # Buscar cita del día para este paciente sin consulta registrada
        from datetime import date as _date
        cita = Cita.objects.filter(
            paciente=paciente,
            tenant=request.tenant,
            fecha=_date.today(),
            consulta__isnull=True,
        ).order_by('-hora_inicio').first()

    from servicios.models import Servicio
    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )

    # Preseleccionar servicios desde la cita si existen
    servicios_preseleccionados = []
    if cita and cita.servicios.exists():
        servicios_preseleccionados = list(cita.servicios.values_list('pk', flat=True))

    if request.method == 'POST':
        form = ConsultaForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.paciente = paciente
            consulta.tenant = request.tenant
            consulta.medico = request.user
            consulta.pagado = 'pagado' in request.POST
            consulta.notas_pago = request.POST.get('notas_pago', '')
            if cita:
                consulta.cita = cita
                cita.estado = 'atendida'
                cita.save(update_fields=['estado'])
            consulta.save()

            # Guardar servicios seleccionados
            servicios_ids = request.POST.getlist('servicios')
            if servicios_ids:
                try:
                    tasa_obj = request.tenant.tasa_cambio
                    tasa = tasa_obj.tasa
                except Exception:
                    tasa = None
                for sid in servicios_ids:
                    try:
                        srv = Servicio.objects.get(
                            pk=sid, tenant=request.tenant, activo=True
                        )
                        ConsultaServicio.objects.create(
                            consulta=consulta,
                            servicio=srv,
                            precio_usd=srv.precio_usd,
                            tasa_cambio=tasa,
                        )
                    except Servicio.DoesNotExist:
                        pass

            if consulta.proxima_cita:
                import datetime
                Cita.objects.create(
                    tenant=request.tenant,
                    paciente=paciente,
                    fecha=consulta.proxima_cita,
                    hora_inicio=datetime.time(8, 0),
                    hora_fin=datetime.time(8, 30),
                    motivo='Control - ' + (consulta.diagnostico[:50] if consulta.diagnostico else 'Seguimiento'),
                    estado='programada',
                    lugar=cita.lugar if cita else None,
                    creado_por=request.user,
                )
                messages.success(request, 'Consulta registrada. Cita programada para el ' + consulta.proxima_cita.strftime('%d/%m/%Y') + '.')
            else:
                messages.success(request, 'Consulta registrada correctamente.')
            return _r(request, f'/pacientes/{paciente.pk}/')
    else:
        from datetime import date
        initial = {'fecha': date.today()}
        if cita and cita.lugar:
            initial['lugar'] = cita.lugar
        form = ConsultaForm(initial=initial, tenant=request.tenant)

    return render(request, 'consultas/form.html', {
        'form': form,
        'paciente': paciente,
        'cita': cita,
        'titulo': 'Nueva consulta',
        'servicios_disponibles': servicios_disponibles,
        'servicios_seleccionados': servicios_preseleccionados,
    })

@login_required
def detalle_consulta(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para ver consultas.')
        return _r(request, '/agenda/')
    consulta = get_object_or_404(
        Consulta.objects.select_related(
            'paciente', 'lugar'
        ).prefetch_related('adjuntos', 'servicios_usados__servicio'),
        pk=pk, tenant=request.tenant
    )
    from servicios.models import Servicio
    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )
    return render(request, 'consultas/detalle.html', {
        'consulta': consulta,
        'servicios_disponibles': servicios_disponibles,
    })


@login_required
def adjuntar_archivo(request, pk):
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para adjuntar archivos.')
        return _r(request, '/agenda/')

    consulta = get_object_or_404(Consulta, pk=pk, tenant=request.tenant)
    from .forms import AdjuntoForm
    if request.method == 'POST':
        form = AdjuntoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES.get('archivo')
            if archivo:
                from consultas.drive import subir_archivo_drive
                try:
                    resultado = subir_archivo_drive(archivo, consulta)
                    AdjuntoConsulta.objects.create(
                        consulta=consulta,
                        drive_file_id=resultado['file_id'],
                        nombre_original=archivo.name,
                        tipo='imagen' if archivo.content_type.startswith('image') else 'pdf',
                        drive_folder_id=resultado.get('folder_id', ''),
                    )
                    messages.success(request, f'Archivo "{archivo.name}" subido correctamente.')
                except Exception as e:
                    messages.error(request, f'Error al subir archivo: {e}')
            return _r(request, f'/pacientes/{consulta.paciente.pk}/')
    else:
        form = AdjuntoForm()

    return render(request, 'consultas/adjuntar.html', {'form': form, 'consulta': consulta})


@login_required
def imprimir_consulta(request, pk):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    consulta = get_object_or_404(
        Consulta.objects.select_related(
            'paciente', 'lugar'
        ).prefetch_related('servicios_usados__servicio'),
        pk=pk, tenant=request.tenant
    )
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER
    from datetime import date
    import io

    tenant = request.tenant
    try:
        config = tenant.config
        nombre_medico = config.nombre_medico or tenant.nombre
        especialidad = config.especialidad or ''
        telefono = config.telefono or tenant.telefono or ''
        email = config.email or ''
        logo_url = config.get_logo_url()
    except Exception:
        nombre_medico = tenant.nombre
        especialidad = telefono = email = ''
        logo_url = None

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

    e_nombre = ParagraphStyle('n', parent=styles['Normal'],
        fontSize=14, fontName='Helvetica-Bold', textColor=oscuro, spaceAfter=2)
    e_sub = ParagraphStyle('s', parent=styles['Normal'],
        fontSize=9, textColor=gris, spaceAfter=2)
    e_seccion = ParagraphStyle('sec', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', textColor=teal,
        spaceBefore=10, spaceAfter=4)
    e_normal = ParagraphStyle('nor', parent=styles['Normal'],
        fontSize=9.5, textColor=oscuro, spaceAfter=4, leading=14)
    e_label = ParagraphStyle('lbl', parent=styles['Normal'],
        fontSize=8, textColor=gris, spaceAfter=1)
    e_pie = ParagraphStyle('pie', parent=styles['Normal'],
        fontSize=7.5, textColor=gris, alignment=TA_CENTER, spaceBefore=4)
    e_firma = ParagraphStyle('firma', parent=styles['Normal'],
        fontSize=9, textColor=oscuro, alignment=TA_CENTER)

    elementos = []

    # Membrete
    logo_img = None
    if logo_url:
        try:
            import urllib.request as ur
            data = ur.urlopen(logo_url).read()
            from reportlab.platypus import Image
            logo_img = Image(io.BytesIO(data), width=2.5*cm, height=2.5*cm)
        except Exception:
            logo_img = None

    info = [Paragraph(nombre_medico, e_nombre)]
    if especialidad:
        info.append(Paragraph(especialidad, e_sub))
    contacto = ' · '.join(filter(None, [telefono, email]))
    if contacto:
        info.append(Paragraph(contacto, e_sub))

    if logo_img:
        from reportlab.platypus import Table as T
        t = T([[logo_img, info]], colWidths=[3*cm, 13*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (0,0), (0,0), 8),
        ]))
        elementos.append(t)
    else:
        for l in info:
            elementos.append(l)

    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(HRFlowable(width='100%', thickness=2, color=teal))
    elementos.append(Spacer(1, 0.3*cm))

    # Datos del paciente
    elementos.append(Paragraph('DATOS DEL PACIENTE', e_seccion))
    p = consulta.paciente
    datos = [
        ['Paciente:', p.nombre_completo, 'Cédula:', p.cedula],
        ['Edad:', f'{p.get_edad()} años' if p.fecha_nacimiento else '—',
         'Teléfono:', p.telefono],
        ['Fecha de consulta:', consulta.fecha.strftime('%d/%m/%Y'),
         'Lugar:', consulta.lugar.nombre if consulta.lugar else '—'],
    ]
    tabla_p = Table(datos, colWidths=[3.5*cm, 6.5*cm, 3*cm, 4*cm])
    tabla_p.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), gris),
        ('TEXTCOLOR', (2,0), (2,-1), gris),
        ('TEXTCOLOR', (1,0), (1,-1), oscuro),
        ('TEXTCOLOR', (3,0), (3,-1), oscuro),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    elementos.append(tabla_p)
    elementos.append(Spacer(1, 0.3*cm))

    # Servicios prestados
    servicios = consulta.servicios_usados.all()
    if servicios:
        elementos.append(Paragraph('SERVICIOS PRESTADOS', e_seccion))
        srv_data = [['Servicio', 'Precio USD', 'Precio Bs']]
        for cs in servicios:
            srv_data.append([
                cs.servicio.nombre,
                f'${cs.precio_usd}',
                f'Bs {cs.precio_bs}' if cs.precio_bs else '—',
            ])
        srv_data.append(['TOTAL', f'${consulta.total_usd}',
            f'Bs {consulta.total_bs}' if consulta.total_bs else '—'])
        tabla_srv = Table(srv_data, colWidths=[10*cm, 3.5*cm, 3.5*cm])
        tabla_srv.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#E5E7EB')),
            ('LINEABOVE', (0,-1), (-1,-1), 0.5, teal),
            ('TEXTCOLOR', (0,-1), (-1,-1), teal),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elementos.append(tabla_srv)
        # Estado de pago
        estado_pago = '✓ PAGADO' if consulta.pagado else '⏳ PAGO PENDIENTE'
        color_pago = colors.HexColor('#16A34A') if consulta.pagado else colors.HexColor('#D97706')
        elementos.append(Paragraph(
            f'<b>{estado_pago}</b>' + (f' — {consulta.notas_pago}' if consulta.notas_pago else ''),
            ParagraphStyle('pago', parent=styles['Normal'],
                fontSize=9, textColor=color_pago, spaceBefore=4, spaceAfter=6)
        ))

    # Diagnóstico
    elementos.append(Paragraph('DIAGNÓSTICO', e_seccion))
    elementos.append(Paragraph(consulta.diagnostico, e_normal))

    if consulta.motivo_consulta:
        elementos.append(Paragraph('MOTIVO / NOTAS', e_seccion))
        elementos.append(Paragraph(consulta.motivo_consulta, e_normal))

    if consulta.peso or consulta.tension_arterial:
        elementos.append(Paragraph('SIGNOS VITALES', e_seccion))
        sv = []
        if consulta.peso:
            sv.append(['Peso:', f'{consulta.peso} kg'])
        if consulta.tension_arterial:
            sv.append(['Tensión arterial:', f'{consulta.tension_arterial} mmHg'])
        tabla_sv = Table(sv, colWidths=[5*cm, 12*cm])
        tabla_sv.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), gris),
            ('TEXTCOLOR', (1,0), (1,-1), oscuro),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elementos.append(tabla_sv)

    elementos.append(Paragraph('TRATAMIENTO E INDICACIONES', e_seccion))
    elementos.append(Paragraph(consulta.tratamiento, e_normal))

    if consulta.observaciones:
        elementos.append(Paragraph('OBSERVACIONES', e_seccion))
        elementos.append(Paragraph(consulta.observaciones, e_normal))

    if consulta.proxima_cita:
        elementos.append(Spacer(1, 0.2*cm))
        elementos.append(HRFlowable(width='100%', thickness=0.5,
            color=colors.HexColor('#E5E7EB')))
        elementos.append(Paragraph(
            f'<b>Próxima cita:</b> {consulta.proxima_cita.strftime("%d/%m/%Y")}',
            e_normal
        ))

    if consulta.es_prenatal:
        elementos.append(Paragraph('CONTROL PRENATAL', e_seccion))
        pre = []
        if consulta.semanas_gestacion:
            pre.append(['Semanas:', str(consulta.semanas_gestacion)])
        if consulta.fpp:
            pre.append(['FPP:', consulta.fpp.strftime('%d/%m/%Y')])
        if consulta.altura_uterina:
            pre.append(['Altura uterina:', f'{consulta.altura_uterina} cm'])
        if consulta.fcf:
            pre.append(['FCF:', f'{consulta.fcf} lpm'])
        if consulta.presentacion_fetal:
            pre.append(['Presentación:', consulta.presentacion_fetal])
        if consulta.edemas is not None:
            pre.append(['Edemas:', 'Sí' if consulta.edemas else 'No'])
        if pre:
            tabla_pre = Table(pre, colWidths=[5*cm, 12*cm])
            tabla_pre.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 8.5),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0,0), (0,-1), gris),
                ('TEXTCOLOR', (1,0), (1,-1), oscuro),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            elementos.append(tabla_pre)
        if consulta.laboratorio:
            elementos.append(Paragraph('Laboratorio:', e_label))
            elementos.append(Paragraph(consulta.laboratorio, e_normal))

    # Firma
    elementos.append(Spacer(1, 1.5*cm))
    elementos.append(HRFlowable(width=8*cm, thickness=0.5,
        color=oscuro, hAlign='CENTER'))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph(nombre_medico, e_firma))
    if especialidad:
        elementos.append(Paragraph(especialidad,
            ParagraphStyle('esp', parent=styles['Normal'],
                fontSize=8, textColor=gris, alignment=TA_CENTER)))

    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width='100%', thickness=0.5,
        color=colors.HexColor('#E5E7EB')))
    pie_parts = [f'Fecha de emisión: {date.today().strftime("%d/%m/%Y")}']
    if telefono:
        pie_parts.append(f'Tel: {telefono}')
    elementos.append(Paragraph(' · '.join(pie_parts), e_pie))

    doc.build(elementos)
    buffer.seek(0)

    from django.http import HttpResponse
    nombre_archivo = f'consulta_{p.cedula}_{consulta.fecha.isoformat()}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response
@login_required
def toggle_pago(request, pk):
    from django.http import JsonResponse
    if request.method == 'POST':
        consulta = get_object_or_404(Consulta, pk=pk, tenant=request.tenant)
        # Si viene con forzar=True siempre marca como pagado
        forzar = request.POST.get('forzar') == 'true'
        if forzar:
            consulta.pagado = True
        else:
            consulta.pagado = not consulta.pagado
        consulta.save(update_fields=['pagado'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'pagado': consulta.pagado})
        referer = request.META.get('HTTP_REFERER', '')
        if 'pagos-pendientes' in referer:
            return _r(request, '/reportes/pagos-pendientes/')
        return _r(request, '/agenda/')
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def agregar_servicio(request, pk):
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    consulta = get_object_or_404(Consulta, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        from servicios.models import Servicio
        servicio_id = request.POST.get('servicio')
        try:
            srv = Servicio.objects.get(pk=servicio_id, tenant=request.tenant, activo=True)
            try:
                tasa = request.tenant.tasa_cambio.tasa
            except Exception:
                tasa = None
            ConsultaServicio.objects.create(
                consulta=consulta,
                servicio=srv,
                precio_usd=srv.precio_usd,
                tasa_cambio=tasa,
            )
            messages.success(request, f'Servicio "{srv.nombre}" agregado.')
        except Servicio.DoesNotExist:
            messages.error(request, 'Servicio no encontrado.')
    return _r(request, f'/consultas/{pk}/')

@login_required
def eliminar_servicio(request, pk):
    """Elimina un ConsultaServicio por su pk."""
    if not request.user.es_medico:
        return _r(request, '/agenda/')
    cs = get_object_or_404(ConsultaServicio, pk=pk, consulta__tenant=request.tenant)
    consulta_pk = cs.consulta.pk
    if request.method == 'POST':
        cs.delete()
        messages.success(request, 'Servicio eliminado.')
    return _r(request, f'/consultas/{consulta_pk}/')

@login_required
def nuevo_procedimiento(request, paciente_id):
    if not request.user.es_medico:
        return _r(request, '/agenda/')

    paciente = get_object_or_404(Paciente, pk=paciente_id, tenant=request.tenant)
    from servicios.models import Servicio
    from .models import Procedimiento
    from datetime import date

    if request.method == 'POST':
        servicio_id = request.POST.get('servicio')
        notas = request.POST.get('notas', '')
        pagado = 'pagado' in request.POST
        cita_id = request.POST.get('cita_id')

        try:
            srv = Servicio.objects.get(pk=servicio_id, tenant=request.tenant, activo=True)
        except Servicio.DoesNotExist:
            messages.error(request, 'Servicio no válido.')
            return _r(request, f'/pacientes/{paciente_id}/')

        try:
            tasa = request.tenant.tasa_cambio.tasa
        except Exception:
            tasa = None

        from agenda.models import Cita
        cita = None
        if cita_id:
            try:
                cita = Cita.objects.get(pk=cita_id, tenant=request.tenant)
                cita.estado = 'atendida'
                cita.save(update_fields=['estado'])
            except Cita.DoesNotExist:
                pass

        Procedimiento.objects.create(
            tenant=request.tenant,
            paciente=paciente,
            medico=request.user,
            fecha=date.today(),
            servicio=srv,
            precio_usd=srv.precio_usd,
            tasa_cambio=tasa,
            notas=notas,
            pagado=pagado,
            cita=cita,
        )
        messages.success(request, f'Procedimiento "{srv.nombre}" registrado.')
        return _r(request, f'/pacientes/{paciente_id}/')

    return _r(request, f'/pacientes/{paciente_id}/')


@login_required
def toggle_pago_procedimiento(request, pk):
    from .models import Procedimiento
    from django.http import JsonResponse
    if request.method == 'POST':
        proc = get_object_or_404(Procedimiento, pk=pk, tenant=request.tenant)
        proc.pagado = not proc.pagado
        proc.save(update_fields=['pagado'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({'pagado': proc.pagado})
        referer = request.META.get('HTTP_REFERER', '')
        if 'pagos-pendientes' in referer:
            return _r(request, '/reportes/pagos-pendientes/')
        return _r(request, '/agenda/')
    return JsonResponse({'error': 'Método no permitido'}, status=405)