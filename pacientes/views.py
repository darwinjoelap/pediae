from django.shortcuts import render, get_object_or_404, redirect
from pediae.decorators import tenant_login_required as login_required
from django.contrib import messages
from django.db.models import Q
from django.db import models as _m
from datetime import date

from .models import Paciente, Vacuna, VacunaAplicada
from .forms import PacienteAsistenteForm, PacientePersonalForm, PacienteCompletoForm, PacienteDoctoraNuevoForm


def _r(request, path):
    tenant = getattr(request, 'tenant', None)
    prefix = f'/t/{tenant.slug}' if tenant else ''
    return redirect(f'{prefix}{path}')


# ── Pacientes ──────────────────────────────────────────────────────────────────

@login_required
def lista_pacientes(request):
    from django.db.models import Count
    tenant = request.tenant
    q = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.filter(tenant=tenant).annotate(num_consultas=Count('consultas'))
    if q:
        pacientes = pacientes.filter(
            Q(nombre_completo__icontains=q) | Q(cedula__icontains=q) | Q(telefono__icontains=q)
        )
    return render(request, 'pacientes/lista.html', {'pacientes': pacientes, 'q': q})


@login_required
def nueva_paciente(request):
    if request.user.es_medico:
        FormClass = PacienteDoctoraNuevoForm
    else:
        FormClass = PacienteAsistenteForm

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            paciente.tenant = request.tenant
            paciente.save()
            messages.success(request, f'Paciente {paciente.nombre_completo} registrada.')
            if request.user.es_medico:
                accion = request.POST.get('accion', 'solo_guardar')
                if accion == 'historia':
                    return _r(request, f'/pacientes/{paciente.pk}/editar/')
                elif accion == 'cita':
                    return _r(request, f'/agenda/citas/nueva/?paciente={paciente.pk}')
            return _r(request, f'/pacientes/{paciente.pk}/')
    else:
        form = FormClass()

    return render(request, 'pacientes/form.html', {
        'form': form,
        'titulo': 'Registrar paciente',
        'modo_nuevo_doctora': request.user.es_medico,
    })


@login_required
def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    consultas = paciente.consultas.all().prefetch_related('adjuntos') if request.user.es_medico else None
    citas = paciente.citas.filter(tenant=request.tenant).order_by('-fecha', '-hora_inicio')[:10]

    from agenda.models import Cita
    from servicios.models import Servicio
    from consultas.models import Procedimiento

    ultima_cita_sin_consulta = Cita.objects.filter(
        paciente=paciente,
        tenant=request.tenant,
        consulta__isnull=True,
        fecha__gte=date.today(),
    ).order_by('fecha', 'hora_inicio').first()

    servicios_disponibles = Servicio.objects.filter(
        tenant=request.tenant, activo=True
    )

    procedimientos = Procedimiento.objects.filter(
        paciente=paciente, tenant=request.tenant
    ).select_related('servicio')

    # Vacunas: resumen para el perfil (atrasadas + próximas pendientes)
    vacunas_resumen = _vacunas_resumen(paciente, request.tenant)

    # Datos de evolución para gráficas + OMS (solo si es médico)
    graficas_json = None
    oms_json = None

    if request.user.es_medico and consultas is not None:
        from django.core.serializers.json import DjangoJSONEncoder
        import json
        from .oms_data import get_curvas, get_eje_meses, PERCENTILES, COLORES_PERCENTIL, DASH_PERCENTIL

        def _f(v, decimals=1):
            return round(float(v), decimals) if v is not None else None

        def _meses(consulta_fecha, nac_fecha):
            """Edad en meses completos en la fecha de consulta."""
            if not nac_fecha or not consulta_fecha:
                return None
            delta = consulta_fecha - nac_fecha
            return max(0, int(delta.days / 30.44))

        puntos = (
            paciente.consultas
            .filter(tenant=request.tenant)
            .exclude(peso__isnull=True, talla__isnull=True, perimetro_cefalico__isnull=True)
            .order_by('fecha')
            .values('pk', 'fecha', 'motivo_consulta', 'peso', 'talla', 'perimetro_cefalico',
                    'percentil_peso', 'percentil_talla', 'percentil_pc')
        )
        fechas, pesos, tallas, pcs = [], [], [], []
        p_peso, p_talla, p_pc = [], [], []
        meses_list = []      # edad en meses en cada consulta
        consulta_ids = []
        consulta_labels = []

        # Punto de nacimiento (si está registrado en la ficha)
        if paciente.fecha_nacimiento and (paciente.peso_nacer or paciente.talla_nacer):
            fechas.append(paciente.fecha_nacimiento.strftime('%d/%m/%Y') + ' (nacer)')
            pesos.append(round(float(paciente.peso_nacer) / 1000, 3) if paciente.peso_nacer else None)
            tallas.append(_f(paciente.talla_nacer, 1) if paciente.talla_nacer else None)
            pcs.append(None)
            p_peso.append(None)
            p_talla.append(None)
            p_pc.append(None)
            meses_list.append(0)
            consulta_ids.append(None)
            consulta_labels.append('Nacimiento')

        for p in puntos:
            fechas.append(p['fecha'].strftime('%d/%m/%Y'))
            pesos.append(_f(p['peso'], 2))
            tallas.append(_f(p['talla'], 1))
            pcs.append(_f(p['perimetro_cefalico'], 1))
            p_peso.append(_f(p['percentil_peso'], 0))
            p_talla.append(_f(p['percentil_talla'], 0))
            p_pc.append(_f(p['percentil_pc'], 0))
            m = _meses(p['fecha'], paciente.fecha_nacimiento)
            meses_list.append(m)
            consulta_ids.append(p['pk'])
            motivo = (p.get('motivo_consulta') or '')[:30]
            label = f"{p['fecha'].strftime('%d/%m/%Y')} — {m}m"
            if motivo:
                label += f' ({motivo})'
            consulta_labels.append(label)

        if fechas:
            # Calcular rango de meses para las curvas OMS
            meses_validos = [m for m in meses_list if m is not None]
            max_m = (max(meses_validos) + 6) if meses_validos else 60

            # Obtener curvas OMS según sexo del paciente
            sexo = getattr(paciente, 'sexo', '') or 'M'
            if sexo not in ('M', 'F'):
                sexo = 'M'

            curvas_peso = get_curvas(sexo, 'peso')
            curvas_talla = get_curvas(sexo, 'talla')
            curvas_pc = get_curvas(sexo, 'pc')

            # Respetar el límite real de los arrays OMS (evitar índices fuera de rango)
            def _limite(curvas, hasta):
                n = len(next(iter(curvas.values())))
                return min(hasta, n - 1)

            lim_peso  = _limite(curvas_peso,  max_m)
            lim_talla = _limite(curvas_talla, max_m)
            lim_pc    = _limite(curvas_pc,    min(max_m, 36))

            eje = get_eje_meses(lim_peso)

            oms_datasets = {}
            for ind, curvas, lim in [
                ('peso',  curvas_peso,  lim_peso),
                ('talla', curvas_talla, lim_talla),
                ('pc',    curvas_pc,    lim_pc),
            ]:
                oms_datasets[ind] = {
                    p: {'valores': curvas[p][:lim + 1],
                        'color': COLORES_PERCENTIL[p],
                        'dash': DASH_PERCENTIL[p]}
                    for p in PERCENTILES
                }

            graficas_json = json.dumps({
                'fechas': fechas,
                'pesos': pesos,
                'tallas': tallas,
                'pcs': pcs,
                'p_peso': p_peso,
                'p_talla': p_talla,
                'p_pc': p_pc,
                'meses': meses_list,
                'consulta_ids': consulta_ids,
                'consulta_labels': consulta_labels,
            }, cls=DjangoJSONEncoder)

            oms_json = json.dumps({
                'eje': eje,
                'sexo': sexo,
                'datasets': oms_datasets,
            }, cls=DjangoJSONEncoder)

    from agenda.models import LugarConsulta
    lugares = LugarConsulta.objects.filter(
        Q(tenant=request.tenant) | Q(tenant__isnull=True)
    ).order_by('nombre')

    return render(request, 'pacientes/detalle.html', {
        'paciente': paciente,
        'consultas': consultas,
        'citas': citas,
        'ultima_cita_sin_consulta': ultima_cita_sin_consulta,
        'servicios_disponibles': servicios_disponibles,
        'procedimientos': procedimientos,
        'graficas_json': graficas_json,
        'oms_json': oms_json,
        'vacunas_resumen': vacunas_resumen,
        'lugares': lugares,
    })


@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    FormClass = PacienteCompletoForm if request.user.es_medico else PacientePersonalForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=paciente)
        if form.is_valid():
            p = form.save(commit=False)
            p.tenant = request.tenant
            p.save()
            messages.success(request, 'Ficha actualizada correctamente.')
            return _r(request, f'/pacientes/{paciente.pk}/')
    else:
        form = FormClass(instance=paciente)

    return render(request, 'pacientes/form.html', {
        'form': form,
        'paciente': paciente,
        'titulo': 'Editar ficha',
    })


@login_required
def eliminar_paciente(request, pk):
    """
    POST → elimina el paciente solo si no tiene consultas ni procedimientos.
    Solo médicos pueden eliminar.
    """
    from django.http import HttpResponseForbidden, HttpResponseBadRequest
    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    if paciente.consultas.exists():
        messages.error(request, f'No se puede eliminar a {paciente.nombre_completo}: tiene consultas registradas.')
        return _r(request, '/pacientes/')

    nombre = paciente.nombre_completo
    paciente.delete()
    messages.success(request, f'Paciente {nombre} eliminada correctamente.')
    return _r(request, '/pacientes/')


# ── Curvas OMS — PDF ──────────────────────────────────────────────────────────

@login_required
def curvas_crecimiento_pdf(request, pk):
    """
    POST: recibe imagen base64 del canvas Chart.js y genera PDF con curvas OMS.
    """
    if not request.user.es_medico:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    grafica_b64 = request.POST.get('grafica_b64', '')
    indicador = request.POST.get('indicador', 'peso')

    # Limpiar prefijo data URI si viene incluido
    if ',' in grafica_b64:
        grafica_b64 = grafica_b64.split(',', 1)[1]

    from .curvas_pdf import generar_pdf_curvas
    from django.http import HttpResponse

    # Obtener config del consultorio (logo, teléfono, etc.)
    try:
        config = request.tenant.config
    except Exception:
        config = None

    pdf_bytes = generar_pdf_curvas(
        paciente=paciente,
        medico=request.user,
        config=config,
        grafica_b64=grafica_b64,
        indicador=indicador,
    )

    nombre_pdf = f'curvas_{paciente.cedula or paciente.pk}_{indicador}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_pdf}"'
    return response


# ── Constancias PDF ────────────────────────────────────────────────────────────

@login_required
def constancia_pdf(request, pk, tipo):
    """
    POST → genera un PDF de constancia y lo devuelve como descarga.
    tipo: 'nino_sano' | 'reposo' | 'lactancia'
    """
    from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest

    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    try:
        config = request.tenant.config
    except Exception:
        config = None

    from .constancias_pdf import (
        generar_constancia_nino_sano,
        generar_constancia_reposo,
        generar_certificado_lactancia,
        generar_constancia_lactancia_trabajo,
    )

    ciudad        = request.POST.get('ciudad', '').strip()
    incluir_firma = request.POST.get('incluir_firma') == 'on'

    if tipo == 'nino_sano':
        datos = {
            'ciudad': ciudad,
            'vacunas_ok': request.POST.get('vacunas_ok') == 'on',
            'incluir_vacunas': request.POST.get('incluir_vacunas') == 'on',
            'incluir_firma': incluir_firma,
        }
        pdf_bytes = generar_constancia_nino_sano(paciente, request.user, config, datos)
        nombre = f'constancia_nino_sano_{paciente.pk}.pdf'

    elif tipo == 'reposo':
        try:
            dias = int(request.POST.get('dias', 1))
        except ValueError:
            dias = 1
        from datetime import date as _date
        fecha_str = request.POST.get('fecha_inicio', '')
        try:
            from datetime import datetime
            fecha_inicio = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except Exception:
            fecha_inicio = _date.today()
        datos = {
            'ciudad': ciudad,
            'dias': dias,
            'motivo': request.POST.get('motivo', '').strip(),
            'fecha_inicio': fecha_inicio,
            'incluir_firma': incluir_firma,
        }
        pdf_bytes = generar_constancia_reposo(paciente, request.user, config, datos)
        nombre = f'reposo_{paciente.pk}.pdf'

    elif tipo == 'lactancia':
        try:
            duracion_meses = int(request.POST.get('duracion_meses', 6))
        except ValueError:
            duracion_meses = 6
        datos = {
            'ciudad': ciudad,
            'duracion_meses': duracion_meses,
            'incluir_firma': incluir_firma,
        }
        pdf_bytes = generar_certificado_lactancia(paciente, request.user, config, datos)
        nombre = f'certificado_lactancia_{paciente.pk}.pdf'

    elif tipo == 'constancia_trabajo':
        datos = {
            'ciudad': ciudad,
            'nombre_madre': request.POST.get('nombre_madre', '').strip(),
            'cedula_madre': request.POST.get('cedula_madre', '').strip(),
            'incluir_firma': incluir_firma,
        }
        pdf_bytes = generar_constancia_lactancia_trabajo(paciente, request.user, config, datos)
        nombre = f'constancia_lactancia_trabajo_{paciente.pk}.pdf'

    else:
        return HttpResponseBadRequest('Tipo de constancia no válido.')

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre}"'
    return response


# ── Informe de Referencia PDF ──────────────────────────────────────────────────

@login_required
def informe_referencia_pdf(request, pk):
    """
    POST → genera un PDF de Informe Médico de Referencia.
    """
    from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed

    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    try:
        config = request.tenant.config
    except Exception:
        config = None

    # Obtener última consulta con datos antropométricos
    ultima_consulta = (
        paciente.consultas
        .filter(peso__isnull=False)
        .order_by('-fecha', '-creado_en')
        .first()
    )

    from .informe_referencia_pdf import generar_informe_referencia

    datos = {
        'especialidad_ref': request.POST.get('especialidad_ref', '').strip(),
        'motivo_ref':        request.POST.get('motivo_ref', '').strip(),
        'antecedentes':      request.POST.getlist('antec[]'),
        'observaciones':     request.POST.get('observaciones', '').strip(),
        'ciudad':            request.POST.get('ciudad', '').strip(),
        'incluir_firma':     request.POST.get('incluir_firma') == 'on',
        'ultima_consulta':   ultima_consulta,
    }

    pdf_bytes = generar_informe_referencia(paciente, request.user, config, datos)

    nombre = f'informe_referencia_{paciente.cedula or paciente.pk}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre}"'
    return response


# ── Vacunas ────────────────────────────────────────────────────────────────────

def _esquema_por_grupos(esquema):
    """Agrupa el esquema de vacunas por grupo_etario para la UI y el PDF."""
    from collections import OrderedDict
    grupos = OrderedDict()
    for e in esquema:
        g = getattr(e['vacuna'], 'grupo_etario', '') or 'Otras vacunas'
        grupos.setdefault(g, []).append(e)
    return [{'label': k, 'vacunas': v} for k, v in grupos.items()]


def _vacunas_resumen(paciente, tenant):
    """Para el perfil: dict con conteos y listas cortas."""
    edad_meses = paciente.get_edad_en_meses()

    vacunas = Vacuna.objects.filter(activa=True).filter(
        _m.Q(tenant=None) | _m.Q(tenant=tenant)
    ).order_by('orden', 'edad_recomendada_meses', 'dosis_numero')

    aplicadas_ids = set(
        VacunaAplicada.objects.filter(paciente=paciente, tenant=tenant)
        .values_list('vacuna_id', flat=True)
    )

    total = vacunas.count()
    aplicadas = len(aplicadas_ids)
    atrasadas = []
    proximas = []

    for v in vacunas:
        if v.pk in aplicadas_ids:
            continue
        if edad_meses is None:
            continue
        if v.edad_max_meses and edad_meses > v.edad_max_meses:
            atrasadas.append(v)
        elif v.edad_recomendada_meses <= edad_meses:
            proximas.append(v)

    return {
        'total': total,
        'aplicadas': aplicadas,
        'pendientes': total - aplicadas,
        'atrasadas': atrasadas,
        'proximas': proximas[:3],  # máximo 3 en resumen
    }


def _estado_esquema(paciente, tenant):
    """Esquema completo con estado por dosis."""
    edad_meses = paciente.get_edad_en_meses()

    vacunas = Vacuna.objects.filter(activa=True).filter(
        _m.Q(tenant=None) | _m.Q(tenant=tenant)
    ).order_by('orden', 'edad_recomendada_meses', 'dosis_numero')

    aplicadas_map = {
        va.vacuna_id: va
        for va in VacunaAplicada.objects.filter(
            paciente=paciente, tenant=tenant
        ).select_related('vacuna')
    }

    resultado = []
    for v in vacunas:
        aplicada = aplicadas_map.get(v.pk)
        if aplicada:
            estado = 'aplicada'
        elif edad_meses is None:
            estado = 'pendiente'
        elif v.edad_max_meses and edad_meses > v.edad_max_meses:
            estado = 'atrasada'
        elif edad_meses >= v.edad_recomendada_meses:
            estado = 'pendiente'
        else:
            estado = 'futura'
        resultado.append({'vacuna': v, 'estado': estado, 'aplicada': aplicada})

    return resultado


@login_required
def vacunas_paciente(request, pk):
    """Página completa del esquema de vacunación."""
    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    esquema = _estado_esquema(paciente, request.tenant)
    grupos = _esquema_por_grupos(esquema)

    return render(request, 'pacientes/vacunas.html', {
        'paciente': paciente,
        'esquema': esquema,
        'grupos': grupos,
        'aplicadas': [e for e in esquema if e['estado'] == 'aplicada'],
        'pendientes': [e for e in esquema if e['estado'] == 'pendiente'],
        'atrasadas': [e for e in esquema if e['estado'] == 'atrasada'],
        'futuras': [e for e in esquema if e['estado'] == 'futura'],
        'today': date.today(),
    })


@login_required
def registrar_vacuna(request, pk):
    """POST: registrar dosis aplicada."""
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para registrar vacunas.')
        return _r(request, f'/pacientes/{pk}/vacunas/')

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        vacuna_id = request.POST.get('vacuna_id')
        if not vacuna_id:
            messages.error(request, 'Selecciona la vacuna.')
            return _r(request, f'/pacientes/{pk}/vacunas/')

        try:
            vacuna = Vacuna.objects.get(pk=vacuna_id, activa=True)
        except Vacuna.DoesNotExist:
            messages.error(request, 'Vacuna no encontrada.')
            return _r(request, f'/pacientes/{pk}/vacunas/')

        # Fecha es opcional — si no se provee, queda como None
        fecha_raw = request.POST.get('fecha', '').strip()
        fecha = None
        if fecha_raw:
            try:
                from datetime import datetime as _dt
                _dt.strptime(fecha_raw, '%Y-%m-%d')
                fecha = fecha_raw
            except ValueError:
                pass

        lote = request.POST.get('lote', '').strip()
        obs  = request.POST.get('observaciones', '').strip()

        obj, created = VacunaAplicada.objects.get_or_create(
            paciente=paciente,
            vacuna=vacuna,
            defaults=dict(
                tenant=request.tenant,
                fecha=fecha,
                lote=lote,
                observaciones=obs,
                aplicada_por=request.user,
            ),
        )
        if not created:
            # Actualizar sólo los campos que llegaron en el POST
            if fecha:
                obj.fecha = fecha
            if lote:
                obj.lote = lote
            if obs:
                obj.observaciones = obs
            obj.aplicada_por = request.user
            obj.save()

        if created:
            messages.success(request, f'✓ {vacuna.nombre} (d{vacuna.dosis_numero}) registrada.')
        else:
            messages.success(request, f'✓ {vacuna.nombre} (d{vacuna.dosis_numero}) actualizada.')

    return _r(request, f'/pacientes/{pk}/vacunas/')


@login_required
def marcar_vacunado(request, pk):
    """POST: marca una vacuna como aplicada con un solo clic (sin fecha ni lote)."""
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso para registrar vacunas.')
        return _r(request, f'/pacientes/{pk}/vacunas/')

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        vacuna_id = request.POST.get('vacuna_id')
        if not vacuna_id:
            return _r(request, f'/pacientes/{pk}/vacunas/')

        try:
            vacuna = Vacuna.objects.get(pk=vacuna_id, activa=True)
        except Vacuna.DoesNotExist:
            messages.error(request, 'Vacuna no encontrada.')
            return _r(request, f'/pacientes/{pk}/vacunas/')

        obj, created = VacunaAplicada.objects.get_or_create(
            paciente=paciente,
            vacuna=vacuna,
            defaults=dict(
                tenant=request.tenant,
                fecha=None,        # marcado rápido: sin fecha
                lote='',
                observaciones='',
                aplicada_por=request.user,
            ),
        )
        if created:
            messages.success(request, f'✓ {vacuna.nombre} (d{vacuna.dosis_numero}) marcada como aplicada.')
        else:
            messages.info(request, f'{vacuna.nombre} ya estaba registrada.')

    return _r(request, f'/pacientes/{pk}/vacunas/')


@login_required
def eliminar_vacuna_aplicada(request, pk, va_pk):
    """POST: eliminar registro de vacuna aplicada."""
    if not request.user.es_medico:
        messages.error(request, 'No tienes permiso.')
        return _r(request, f'/pacientes/{pk}/vacunas/')

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)
    va = get_object_or_404(VacunaAplicada, pk=va_pk, paciente=paciente, tenant=request.tenant)

    if request.method == 'POST':
        nombre = f'{va.vacuna.nombre} d{va.vacuna.dosis_numero}'
        va.delete()
        messages.success(request, f'Registro de {nombre} eliminado.')

    return _r(request, f'/pacientes/{pk}/vacunas/')


@login_required
def vacunas_pdf(request, pk):
    """POST → genera PDF del esquema de vacunación del paciente."""
    from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed

    if not request.user.es_medico:
        return HttpResponseForbidden()
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    paciente = get_object_or_404(Paciente, pk=pk, tenant=request.tenant)

    try:
        config = request.tenant.config
    except Exception:
        config = None

    from .vacunas_pdf import generar_vacunas_pdf

    esquema = _estado_esquema(paciente, request.tenant)
    datos = {
        'ciudad':        request.POST.get('ciudad', '').strip(),
        'incluir_firma': request.POST.get('incluir_firma') == 'on',
    }

    pdf_bytes = generar_vacunas_pdf(
        paciente=paciente,
        medico=request.user,
        config=config,
        esquema=esquema,
        datos=datos,
    )

    nombre = f'vacunas_{paciente.cedula or paciente.pk}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre}"'
    return response
