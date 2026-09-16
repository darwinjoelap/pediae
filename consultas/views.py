from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from pediae.decorators import tenant_login_required as login_required
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
            estado__in=['programada', 'confirmada'],
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
                            costo_adquisicion_usd=srv.costo_adquisicion_usd,
                            tasa_cambio=tasa,
                        )
                    except Servicio.DoesNotExist:
                        pass

            if consulta.proxima_cita:
                Cita.objects.create(
                    tenant=request.tenant,
                    paciente=paciente,
                    fecha=consulta.proxima_cita,
                    hora_inicio=None,
                    hora_fin=None,
                    motivo='Control - ' + (consulta.diagnostico[:50] if consulta.diagnostico else 'Seguimiento'),
                    estado='tentativa',
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

    import json as _json
    from .models import Medicamento
    from decimal import Decimal

    def _meds_context(tenant):
        qs = list(Medicamento.objects.filter(
            tenant=tenant, activo=True
        ).order_by('orden', 'nombre').values(
            'pk', 'nombre', 'indicaciones',
            'dosis_mg_kg_min', 'dosis_mg_kg_max',
            'frecuencia_horas', 'duracion_dias',
            'presentacion', 'concentracion_mg', 'volumen_ml',
            'unidad_resultado', 'dosis_max_absoluta',
        ))
        for m in qs:
            for k in ('dosis_mg_kg_min','dosis_mg_kg_max','concentracion_mg',
                      'volumen_ml','dosis_max_absoluta'):
                m[k] = float(m[k]) if m[k] is not None else None
            m['tiene_calculo'] = bool(m['dosis_mg_kg_min'] and m['concentracion_mg'] and m['unidad_resultado'])
            m['tiene_rango'] = bool(m['dosis_mg_kg_min'] and m['dosis_mg_kg_max'])
        return qs

    meds_qs = _meds_context(request.tenant)

    # Edad actual del paciente en meses (para AJAX)
    from dateutil.relativedelta import relativedelta
    from datetime import date as _date
    edad_meses_actual = None
    if paciente.fecha_nacimiento:
        d = relativedelta(_date.today(), paciente.fecha_nacimiento)
        edad_meses_actual = d.years * 12 + d.months

    # Peso de la última consulta (sugerencia)
    ultimo_peso = None
    ultima = Consulta.objects.filter(
        paciente=paciente, tenant=request.tenant, peso__isnull=False
    ).order_by('-fecha').first()
    if ultima:
        ultimo_peso = float(ultima.peso)

    return render(request, 'consultas/form.html', {
        'form': form,
        'paciente': paciente,
        'cita': cita,
        'titulo': 'Nueva consulta',
        'servicios_disponibles': servicios_disponibles,
        'servicios_seleccionados': servicios_preseleccionados,
        'medicamentos_disponibles': meds_qs,
        'medicamentos_json': _json.dumps(meds_qs, ensure_ascii=False),
        'paciente_edad_meses': edad_meses_actual,
        'paciente_ultimo_peso': ultimo_peso,
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
    from datetime import date, timedelta
    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )
    puede_eliminar = (
        not consulta.pagado
        and consulta.creado_en.date() >= date.today() - timedelta(days=7)
    )
    return render(request, 'consultas/detalle.html', {
        'consulta': consulta,
        'servicios_disponibles': servicios_disponibles,
        'puede_eliminar': puede_eliminar,
    })


@login_required
def editar_consulta(request, pk):
    """Edita una consulta existente. Nunca crea duplicados."""
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para editar consultas.')
        return _r(request, '/agenda/')

    consulta = get_object_or_404(
        Consulta.objects.select_related('paciente', 'cita', 'lugar'),
        pk=pk, tenant=request.tenant
    )
    paciente = consulta.paciente

    from servicios.models import Servicio
    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )
    servicios_preseleccionados = list(
        consulta.servicios_usados.values_list('servicio_id', flat=True)
    )

    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta, tenant=request.tenant)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.pagado = 'pagado' in request.POST
            consulta.notas_pago = request.POST.get('notas_pago', '')
            consulta.save()

            # Reemplaza los servicios: borra los anteriores y guarda los nuevos
            consulta.servicios_usados.all().delete()
            servicios_ids = request.POST.getlist('servicios')
            if servicios_ids:
                try:
                    tasa = request.tenant.tasa_cambio.tasa
                except Exception:
                    tasa = None
                for sid in servicios_ids:
                    try:
                        srv = Servicio.objects.get(pk=sid, tenant=request.tenant, activo=True)
                        ConsultaServicio.objects.create(
                            consulta=consulta,
                            servicio=srv,
                            precio_usd=srv.precio_usd,
                            costo_adquisicion_usd=srv.costo_adquisicion_usd,
                            tasa_cambio=tasa,
                        )
                    except Servicio.DoesNotExist:
                        pass

            messages.success(request, 'Consulta actualizada correctamente.')
            return _r(request, f'/consultas/{consulta.pk}/')
    else:
        form = ConsultaForm(instance=consulta, tenant=request.tenant)

    import json as _json
    from .models import Medicamento
    from decimal import Decimal

    def _meds_ctx(tenant):
        qs = list(Medicamento.objects.filter(
            tenant=tenant, activo=True
        ).order_by('orden', 'nombre').values(
            'pk', 'nombre', 'indicaciones',
            'dosis_mg_kg_min', 'dosis_mg_kg_max',
            'frecuencia_horas', 'duracion_dias',
            'presentacion', 'concentracion_mg', 'volumen_ml',
            'unidad_resultado', 'dosis_max_absoluta',
        ))
        for m in qs:
            for k in ('dosis_mg_kg_min','dosis_mg_kg_max','concentracion_mg',
                      'volumen_ml','dosis_max_absoluta'):
                m[k] = float(m[k]) if m[k] is not None else None
            m['tiene_calculo'] = bool(m['dosis_mg_kg_min'] and m['concentracion_mg'] and m['unidad_resultado'])
            m['tiene_rango'] = bool(m['dosis_mg_kg_min'] and m['dosis_mg_kg_max'])
        return qs

    meds_qs = _meds_ctx(request.tenant)

    from dateutil.relativedelta import relativedelta
    from datetime import date as _date
    edad_meses_actual = None
    if paciente.fecha_nacimiento:
        d = relativedelta(_date.today(), paciente.fecha_nacimiento)
        edad_meses_actual = d.years * 12 + d.months

    peso_actual = float(consulta.peso) if consulta.peso else None

    return render(request, 'consultas/form.html', {
        'form': form,
        'paciente': paciente,
        'cita': consulta.cita,
        'titulo': 'Editar consulta',
        'consulta': consulta,
        'servicios_disponibles': servicios_disponibles,
        'servicios_seleccionados': servicios_preseleccionados,
        'medicamentos_disponibles': meds_qs,
        'medicamentos_json': _json.dumps(meds_qs, ensure_ascii=False),
        'paciente_edad_meses': edad_meses_actual,
        'paciente_ultimo_peso': peso_actual,
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
        Consulta.objects.select_related('paciente', 'lugar'),
        pk=pk, tenant=request.tenant
    )
    from weasyprint import HTML, CSS
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from datetime import date
    import io

    tenant = request.tenant
    try:
        config = tenant.config
        nombre_medico = config.nombre_medico or tenant.nombre
        especialidad  = config.especialidad or ''
        telefono      = config.telefono or tenant.telefono or ''
        email         = config.email or ''
        logo_url      = config.get_logo_url()
    except Exception:
        nombre_medico = tenant.nombre
        especialidad = telefono = email = logo_url = ''

    contacto = ' · '.join(filter(None, [telefono, email]))

    ctx = {
        'consulta':      consulta,
        'nombre_medico': nombre_medico,
        'especialidad':  especialidad,
        'telefono':      telefono,
        'contacto':      contacto,
        'logo_url':      logo_url,
        'hoy':           date.today().strftime('%d/%m/%Y'),
    }

    html_str = render_to_string('consultas/imprimir_consulta.html', ctx, request=request)
    pdf_buffer = io.BytesIO()
    HTML(string=html_str, base_url=request.build_absolute_uri('/')).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    p = consulta.paciente
    nombre_archivo = f'consulta_{p.cedula}_{consulta.fecha.isoformat()}.pdf'
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
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
def eliminar_procedimiento(request, pk):
    from .models import Procedimiento
    from datetime import date, timedelta
    from django.http import HttpResponseForbidden, HttpResponseNotAllowed
    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    proc = get_object_or_404(Procedimiento, pk=pk, tenant=request.tenant)
    limite = date.today() - timedelta(days=7)
    if proc.creado_en.date() < limite:
        messages.error(request, 'Solo puedes eliminar procedimientos creados en los últimos 7 días.')
        return _r(request, f'/pacientes/{proc.paciente.pk}/')
    paciente_pk = proc.paciente.pk
    proc.delete()
    messages.success(request, 'Procedimiento eliminado correctamente.')
    return _r(request, f'/pacientes/{paciente_pk}/')


# ── Glosario de medicamentos ─────────────────────────────────────────────────

@login_required
def lista_medicamentos(request):
    from .models import Medicamento
    from django.http import HttpResponseForbidden
    if not request.user.es_medico:
        return HttpResponseForbidden()
    meds = Medicamento.objects.filter(tenant=request.tenant).order_by('orden', 'nombre')
    return render(request, 'consultas/glosario_medicamentos.html', {'medicamentos': meds})


@login_required
def medicamentos_json(request):
    from .models import Medicamento
    meds = list(Medicamento.objects.filter(
        tenant=request.tenant, activo=True
    ).order_by('orden', 'nombre').values(
        'pk', 'nombre', 'indicaciones',
        'modo_calculo', 'unidad_dosis_kg', 'dosis_fija',
        'dosis_mg_kg_min', 'dosis_mg_kg_max',
        'frecuencia_horas', 'duracion_dias',
        'presentacion', 'concentracion_mg', 'volumen_ml',
        'unidad_resultado', 'dosis_max_absoluta',
    ))
    # Serialize Decimal → str for JSON
    UNIDADES_DIRECTAS_KG = frozenset({'mL', 'gotas', 'tableta', 'sobre', 'puff', 'aplicacion'})
    for m in meds:
        for k in ('dosis_mg_kg_min','dosis_mg_kg_max','concentracion_mg',
                  'volumen_ml','dosis_max_absoluta'):
            m[k] = str(m[k]) if m[k] is not None else None
        modo = m.get('modo_calculo', 'peso')
        if modo == 'fija':
            m['tiene_calculo'] = bool(m.get('dosis_fija'))
        elif modo == 'edad':
            m['tiene_calculo'] = True  # simplificado; el servidor calcula
        else:  # modo peso
            udkg = m.get('unidad_dosis_kg', 'mg')
            if udkg in UNIDADES_DIRECTAS_KG:
                m['tiene_calculo'] = bool(m['dosis_mg_kg_min'])
            else:
                m['tiene_calculo'] = bool(m['dosis_mg_kg_min'] and m['concentracion_mg'] and m['unidad_resultado'])
        m['tiene_rango'] = bool(m['dosis_mg_kg_min'] and m['dosis_mg_kg_max'])
    return JsonResponse({'medicamentos': meds})


@login_required
def nuevo_medicamento(request):
    from .models import Medicamento
    from django.http import HttpResponseForbidden
    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method == 'POST':
        nombre       = request.POST.get('nombre', '').strip()
        indicaciones = request.POST.get('indicaciones', '').strip()
        orden        = int(request.POST.get('orden', 0) or 0)

        def _dec(key):
            v = request.POST.get(key, '').strip()
            return v if v else None

        def _int(key):
            v = request.POST.get(key, '').strip()
            return int(v) if v else None

        if nombre:
            Medicamento.objects.create(
                tenant=request.tenant,
                nombre=nombre,
                indicaciones=indicaciones,
                orden=orden,
                modo_calculo=request.POST.get('modo_calculo', 'peso') or 'peso',
                unidad_dosis_kg=request.POST.get('unidad_dosis_kg', 'mg') or 'mg',
                dosis_fija=request.POST.get('dosis_fija', '').strip(),
                dosis_mg_kg_min=_dec('dosis_mg_kg_min'),
                dosis_mg_kg_max=_dec('dosis_mg_kg_max'),
                frecuencia_horas=_int({
                    'fija': 'frecuencia_horas_fija',
                    'edad': 'frecuencia_horas_edad',
                }.get(request.POST.get('modo_calculo', 'peso') or 'peso', 'frecuencia_horas')),
                duracion_dias=_int({
                    'fija': 'duracion_dias_fija',
                    'edad': 'duracion_dias_edad',
                }.get(request.POST.get('modo_calculo', 'peso') or 'peso', 'duracion_dias')),
                presentacion=request.POST.get('presentacion', '').strip(),
                concentracion_mg=_dec('concentracion_mg'),
                volumen_ml=_dec('volumen_ml'),
                unidad_resultado=request.POST.get('unidad_resultado', '').strip(),
                dosis_max_absoluta=_dec('dosis_max_absoluta'),
                peso_min_kg=_dec('peso_min_kg'),
                edad_min_meses=_int('edad_min_meses'),
                edad_max_meses=_int('edad_max_meses'),
                rango1_edad_min=_int('rango1_edad_min'),
                rango1_edad_max=_int('rango1_edad_max'),
                rango1_dosis=request.POST.get('rango1_dosis', '').strip(),
                rango2_edad_min=_int('rango2_edad_min'),
                rango2_edad_max=_int('rango2_edad_max'),
                rango2_dosis=request.POST.get('rango2_dosis', '').strip(),
                rango3_edad_min=_int('rango3_edad_min'),
                rango3_edad_max=_int('rango3_edad_max'),
                rango3_dosis=request.POST.get('rango3_dosis', '').strip(),
            )
            messages.success(request, f'Medicamento "{nombre}" agregado.')
    return _r(request, '/consultas/medicamentos/')


@login_required
def editar_medicamento(request, pk):
    from .models import Medicamento
    from django.http import HttpResponseForbidden
    if not request.user.es_medico:
        return HttpResponseForbidden()
    med = get_object_or_404(Medicamento, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        def _dec(key):
            v = request.POST.get(key, '').strip()
            return v if v else None

        def _int(key):
            v = request.POST.get(key, '').strip()
            return int(v) if v else None

        med.nombre              = request.POST.get('nombre', med.nombre).strip()
        med.indicaciones        = request.POST.get('indicaciones', med.indicaciones).strip()
        med.orden               = int(request.POST.get('orden', med.orden) or 0)
        _modo = request.POST.get('modo_calculo', 'peso') or 'peso'
        _freq_key = {'fija': 'frecuencia_horas_fija', 'edad': 'frecuencia_horas_edad'}.get(_modo, 'frecuencia_horas')
        _dur_key  = {'fija': 'duracion_dias_fija',    'edad': 'duracion_dias_edad'   }.get(_modo, 'duracion_dias')
        med.modo_calculo        = _modo
        med.unidad_dosis_kg     = request.POST.get('unidad_dosis_kg', 'mg') or 'mg'
        med.dosis_fija          = request.POST.get('dosis_fija', '').strip()
        med.dosis_mg_kg_min     = _dec('dosis_mg_kg_min')
        med.dosis_mg_kg_max     = _dec('dosis_mg_kg_max')
        med.frecuencia_horas    = _int(_freq_key)
        med.duracion_dias       = _int(_dur_key)
        med.presentacion        = request.POST.get('presentacion', '').strip()
        med.concentracion_mg    = _dec('concentracion_mg')
        med.volumen_ml          = _dec('volumen_ml')
        med.unidad_resultado    = request.POST.get('unidad_resultado', '').strip()
        med.dosis_max_absoluta  = _dec('dosis_max_absoluta')
        med.peso_min_kg         = _dec('peso_min_kg')
        med.edad_min_meses      = _int('edad_min_meses')
        med.edad_max_meses      = _int('edad_max_meses')
        med.rango1_edad_min     = _int('rango1_edad_min')
        med.rango1_edad_max     = _int('rango1_edad_max')
        med.rango1_dosis        = request.POST.get('rango1_dosis', '').strip()
        med.rango2_edad_min     = _int('rango2_edad_min')
        med.rango2_edad_max     = _int('rango2_edad_max')
        med.rango2_dosis        = request.POST.get('rango2_dosis', '').strip()
        med.rango3_edad_min     = _int('rango3_edad_min')
        med.rango3_edad_max     = _int('rango3_edad_max')
        med.rango3_dosis        = request.POST.get('rango3_dosis', '').strip()
        # DEBUG TEMPORAL — ver en la terminal del runserver qué llega en el POST
        import sys
        print('=== DEBUG editar_medicamento POST ===', file=sys.stderr)
        for k in ['modo_calculo','dosis_mg_kg_min','dosis_mg_kg_max',
                  'frecuencia_horas','duracion_dias','concentracion_mg','volumen_ml']:
            print(f'  {k} = {request.POST.get(k, "<AUSENTE>")!r}', file=sys.stderr)
        print('=====================================', file=sys.stderr)
        # FIN DEBUG
        try:
            med.save()
            messages.success(request, 'Medicamento actualizado.')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')
            import traceback; traceback.print_exc()
    return _r(request, '/consultas/medicamentos/')


@login_required
def toggle_medicamento(request, pk):
    from .models import Medicamento
    from django.http import HttpResponseForbidden
    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method == 'POST':
        med = get_object_or_404(Medicamento, pk=pk, tenant=request.tenant)
        med.activo = not med.activo
        med.save(update_fields=['activo'])
    return _r(request, '/consultas/medicamentos/')


@login_required
def eliminar_medicamento(request, pk):
    from .models import Medicamento
    from django.http import HttpResponseForbidden
    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method == 'POST':
        med = get_object_or_404(Medicamento, pk=pk, tenant=request.tenant)
        nombre = med.nombre
        med.delete()
        messages.success(request, f'Medicamento "{nombre}" eliminado.')
    return _r(request, '/consultas/medicamentos/')


@login_required
def calcular_dosis_medicamento(request, pk):
    """GET /consultas/medicamentos/<pk>/calcular/?peso=17&edad_meses=36&nivel=estandar"""
    from .models import Medicamento
    med = get_object_or_404(Medicamento, pk=pk, tenant=request.tenant, activo=True)
    try:
        peso = float(request.GET.get('peso', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'peso inválido'}, status=400)
    if peso <= 0:
        return JsonResponse({'error': 'peso requerido'}, status=400)
    edad_meses = None
    em = request.GET.get('edad_meses', '')
    if em:
        try:
            edad_meses = int(em)
        except (ValueError, TypeError):
            pass
    nivel = request.GET.get('nivel', 'estandar')
    try:
        resultado = med.calcular_dosis(peso_kg=peso, edad_meses=edad_meses, nivel=nivel)
    except Exception as exc:
        import traceback
        return JsonResponse({'error': str(exc), 'traceback': traceback.format_exc()}, status=500)
    return JsonResponse(resultado)


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
                costo_adquisicion_usd=srv.costo_adquisicion_usd,
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
def eliminar_consulta(request, pk):
    """
    Elimina una consulta con restricciones estrictas:
    - Solo médicos
    - POST con confirmación 'ELIMINAR'
    - Creada hace ≤7 días
    - No pagada
    """
    from django.http import HttpResponseForbidden, HttpResponseBadRequest
    from datetime import date, timedelta

    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    consulta = get_object_or_404(
        Consulta.objects.select_related('paciente'),
        pk=pk, tenant=request.tenant
    )

    # Validar confirmación
    if request.POST.get('confirmacion', '').strip().upper() != 'ELIMINAR':
        messages.error(request, 'Confirmación incorrecta. Escribe ELIMINAR para confirmar.')
        return _r(request, f'/consultas/{pk}/')

    # Validar ≤7 días
    limite = date.today() - timedelta(days=7)
    if consulta.creado_en.date() < limite:
        messages.error(request, 'Solo puedes eliminar consultas creadas en los últimos 7 días.')
        return _r(request, f'/consultas/{pk}/')

    # Validar no pagada
    if consulta.pagado:
        messages.error(request, 'No se puede eliminar una consulta que ya fue marcada como pagada.')
        return _r(request, f'/consultas/{pk}/')

    paciente_pk = consulta.paciente.pk
    consulta.delete()
    messages.success(request, 'Consulta eliminada correctamente.')
    return _r(request, f'/pacientes/{paciente_pk}/')


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
def recipe_consulta(request, pk):
    """Genera el récipe médico en PDF y lo devuelve como respuesta inline."""
    if not request.user.es_medico:
        return _r(request, '/agenda/')

    consulta = get_object_or_404(
        Consulta.objects.select_related('paciente', 'lugar', 'medico'),
        pk=pk, tenant=request.tenant
    )

    from django.http import HttpResponse
    from .recipe_pdf import generar_recipe_pdf

    medico = consulta.medico or request.user
    try:
        config = request.tenant.config
    except Exception:
        config = None

    buffer = generar_recipe_pdf(consulta, medico, config)

    paciente = consulta.paciente
    cedula = paciente.cedula.replace('/', '-')
    nombre_archivo = f'recipe_{cedula}_{consulta.fecha.isoformat()}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response


@login_required
def toggle_pago_procedimiento(request, pk):
    from .models import Procedimiento
    from django.http import JsonResponse
    if request.method == 'POST':
        proc = get_object_or_404(Procedimiento, pk=pk, tenant=request.tenant)
        forzar = request.POST.get('forzar') == 'true'
        if forzar:
            proc.pagado = True
        else:
            proc.pagado = not proc.pagado
        proc.save(update_fields=['pagado'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({'pagado': proc.pagado})
        referer = request.META.get('HTTP_REFERER', '')
        if 'pagos-pendientes' in referer:
            return _r(request, '/reportes/pagos-pendientes/')
        return _r(request, '/agenda/')
    return JsonResponse({'error': 'Método no permitido'}, status=405)