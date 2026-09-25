# Pediae — Contexto de sesión

## Qué es
SaaS multi-tenant para gestión de consultas pediátricas.
Misma arquitectura base que Ginea — instancia Django, subdominios por pediatra.

## Stack
- Django · PostgreSQL · Bootstrap 5 · HTMX · ReportLab · PWA
- Cloudinary (media/almacenamiento — NO Google Drive)
- Railway (misma estrategia de despliegue que Ginea)

## Arranque local
```powershell
cd C:\proyectos\pediae
.venv\Scripts\activate
python manage.py runserver
```

## Tenants activos
| Tenant | Tipo |
|--------|------|
| Dra. Anais Báez | Producción |
| Dra. María Virginia Hernández Escalona | Producción |
| Pediae | Prueba (Darwin) |

## Arquitectura multi-tenant
- Misma lógica de subdominios que Ginea
- Activación de suscripciones: **manual por Darwin** en panel admin

## Módulo de consultas
- `consultas/views.py` — lógica principal; incluye `imprimir_consulta`, `toggle_pago`, `recipe_pdf_view`
- `consultas/recipe_pdf.py` — generación de récipe médico en PDF con ReportLab
- `consultas/models.py` — modelo `Consulta` con campos pediátricos: antropometría, signos vitales, desarrollo psicomotor, medicamentos, indicaciones
- `consultas/forms.py` — formularios de consulta y medicamentos
- Medicamentos: cálculo de dosis por peso (mg/kg), rangos de edad, modo de cálculo configurable

## Template de impresión (`templates/consultas/imprimir_consulta.html`)
- Diseño moderno con CSS variables, flexbox y gradientes — **no usar xhtml2pdf** (incompatible)
- Vista previa en pantalla: tarjeta blanca elevada sobre fondo gris
- Secciones: membrete · ficha paciente · antropometría (tarjetas con percentiles) · signos vitales (chips) · secciones clínicas · diagnóstico/tratamiento destacados · firma · pie
- Responsive móvil (`@media max-width: 640px`): header apilado, grilla 2 col en antropometría, ficha en columna
- Al imprimir: `print-color-adjust: exact` preserva colores; `@media print` elimina la envoltura de pantalla
- La vista `imprimir_consulta` renderiza HTML puro (no genera PDF en servidor) — el PDF se obtiene desde el navegador con Ctrl+P → Guardar como PDF

## Notas clave
- Arquitectura espejo de Ginea — si hay un cambio estructural en uno, evaluar duplicarlo en el otro
- Media → Cloudinary (no storage local, no Google Drive)
- Funcional en producción
- `venv` local: `.venv\Scripts\activate` (no `venv\`)
