import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, IntegerField, Sum, Q
from django.utils.timezone import now
from django.db.models import Max
from django.core.paginator import Paginator
from .forms import (
    EstudianteForm, ExamenForm, ResultadoForm, MateriaForm, 
    PreguntaForm, RespuestaEstudianteForm, ProfesorForm, AdministradorForm,
    AdministradorSignupForm, AdministradorLoginForm
)
from django.views.decorators.http import require_POST, require_GET

from .models import Estudiante, Examen, Resultado, Materia, Pregunta, RespuestaEstudiante, Profesor, Administrador
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

def home(request):
    # Verificar si el administrador ha iniciado sesión
    administrador_id = request.session.get('administrador_id')
    
    if not administrador_id:
        messages.error(request, "Debes iniciar sesión como administrador para acceder a esta página.")
        return redirect('base:login_administrador') # Redirigir al login de admin
 
    # Si el admin está logueado, continuar con la lógica original de la vista home
    total_estudiantes = Estudiante.objects.count()
    total_examenes = Examen.objects.count()
    total_resultados = Resultado.objects.count()
    total_materias = Materia.objects.count()
    total_preguntas = Pregunta.objects.count()
    total_respuestas = RespuestaEstudiante.objects.count()
    total_profesores = Profesor.objects.count()
    total_administradores = Administrador.objects.count()

    contexto = {
        "total_estudiantes": total_estudiantes,
        "total_examenes": total_examenes,
        "total_resultados": total_resultados,
        "total_materias": total_materias,
        "total_preguntas": total_preguntas,
        "total_respuestas": total_respuestas,
        "total_profesores": total_profesores,
        "total_administradores": total_administradores
    }

    return render(request, "dashboard.html", contexto)

def authView(request):
 if request.method == "POST":
  form = UserCreationForm(request.POST or None)
  if form.is_valid():
   form.save()
   return redirect("base:login")
 else:
  form = UserCreationForm()
 return render(request, "registration/signup.html", {"form": form})

# VISTAS DE LISTADO INDIVIDUALES
def listar_estudiantes(request):
    estudiantes_list = Estudiante.objects.all().order_by('id_estudiante')
    
    # Obtener grados únicos para el dropdown de filtro
    grados_existentes = Estudiante.objects.values_list('grado', flat=True).distinct().order_by('grado')
    grados_existentes = [grado for grado in grados_existentes if grado] # Filtrar None o vacíos

    # Búsqueda y Filtros
    query_busqueda = request.GET.get('q')
    grado_filtrado = request.GET.get('grado')

    if query_busqueda:
        estudiantes_list = estudiantes_list.filter(
            Q(nombre__icontains=query_busqueda) | 
            Q(apellido__icontains=query_busqueda)
        )
    
    if grado_filtrado:
        estudiantes_list = estudiantes_list.filter(grado=grado_filtrado)

    paginator = Paginator(estudiantes_list, 6) # 6 estudiantes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_estudiantes_count = Estudiante.objects.all().count() # Conteo total antes de filtrar para la tarjeta

    return render(request, 'lista_estudiantes.html', {
        'page_obj': page_obj, 
        'total_estudiantes_count': total_estudiantes_count,
        'grados_existentes': grados_existentes,
        'query_busqueda_actual': query_busqueda, # Para mantener el valor en el input de búsqueda
        'grado_filtrado_actual': grado_filtrado # Para mantener la selección en el dropdown de grado
    })

def listar_examenes(request):
    examenes_list = Examen.objects.all().order_by('-fecha_examen') # Ordenar por defecto

    # Búsqueda
    query = request.GET.get('q')
    if query:
        examenes_list = examenes_list.filter(
            Q(tipo__icontains=query) | 
            Q(id_examen__icontains=query) |
            Q(profesor__nombre__icontains=query) | # Asumiendo que Examen tiene un ForeignKey a Profesor
            Q(profesor__apellido__icontains=query)
        )

    # Filtro por estado
    estado_filter = request.GET.get('estado')
    if estado_filter and estado_filter != 'Todos los estados':
        examenes_list = examenes_list.filter(estado=estado_filter)

    # Filtro por tipo/materia
    tipo_filter = request.GET.get('tipo')
    if tipo_filter and tipo_filter != 'Todos los tipos':
        examenes_list = examenes_list.filter(tipo=tipo_filter)
    
    # Filtro por fecha
    fecha_filter = request.GET.get('fecha')
    if fecha_filter:
        examenes_list = examenes_list.filter(fecha_examen__date=fecha_filter)

    # Calcular conteos después de aplicar filtros para las tarjetas
    # Es importante hacer esto sobre la lista ya filtrada si quieres que los conteos reflejen los filtros.
    # O sobre Examen.objects.all() si quieres conteos globales. La plantilla parece esperar conteos filtrados.
    
    # Para ser consistentes con la plantilla que parece esperar conteos basados en la lista filtrada:
    count_activos = sum(1 for ex in examenes_list if ex.estado == 'Activo')
    count_pendientes = sum(1 for ex in examenes_list if ex.estado == 'Pendiente')
    count_realizados = sum(1 for ex in examenes_list if ex.estado == 'Realizado')
    # count_cancelados = sum(1 for ex in examenes_list if ex.estado == 'Cancelado') # Si lo necesitas

    paginator = Paginator(examenes_list, 5) # Mostrar 5 exámenes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener todos los tipos de examen únicos para el dropdown de filtro
    tipos_examen = Examen.objects.values_list('tipo', flat=True).distinct().order_by('tipo')


    context = {
        "examenes": page_obj, # Cambiado a page_obj para la paginación
        "tipos_examen": tipos_examen,
        "query": query or "",
        "estado_filter": estado_filter or "Todos los estados",
        "tipo_filter": tipo_filter or "Todos los tipos",
        "fecha_filter": fecha_filter or "",
        "count_activos": count_activos,
        "count_pendientes": count_pendientes,
        "count_realizados": count_realizados,
    }
    return render(request, "lista_examenes.html", context)

def listar_resultados(request):
    resultados_list = Resultado.objects.select_related('estudiante', 'examen').all().order_by('-fecha_resultado')

    # Búsqueda general (estudiante o examen)
    query_busqueda = request.GET.get('q')
    if query_busqueda:
        resultados_list = resultados_list.filter(
            Q(estudiante__nombre__icontains=query_busqueda) |
            Q(estudiante__apellido__icontains=query_busqueda) |
            Q(estudiante__identificacion__icontains=query_busqueda) |
            Q(examen__tipo__icontains=query_busqueda) 
        )

    # Filtro por estudiante (ID)
    estudiante_filter = request.GET.get('estudiante_id') 
    if estudiante_filter:
        resultados_list = resultados_list.filter(estudiante__id_estudiante=estudiante_filter)

    # Filtro por examen (tipo de examen)
    examen_filter = request.GET.get('examen_tipo')
    if examen_filter and examen_filter != 'Todos los exámenes':
        resultados_list = resultados_list.filter(examen__tipo__iexact=examen_filter)

    # Filtro por calificación (Aprobado/Reprobado)
    UMBRAL_APROBACION = 70 
    calificacion_filter = request.GET.get('calificacion')
    if calificacion_filter:
        if calificacion_filter == 'Aprobado':
            resultados_list = resultados_list.filter(puntaje_global__gte=UMBRAL_APROBACION)
        elif calificacion_filter == 'Reprobado':
            resultados_list = resultados_list.filter(puntaje_global__lt=UMBRAL_APROBACION)
    
    total_resultados_filtrados = resultados_list.count()
    count_aprobados = sum(1 for r in resultados_list if r.puntaje_global >= UMBRAL_APROBACION) 
    promedio_general_calculado = resultados_list.aggregate(Avg('puntaje_global'))['puntaje_global__avg']
    if promedio_general_calculado is None:
        promedio_general_calculado = 0 
    examenes_unicos_count = resultados_list.values('examen__id_examen').distinct().count()

    paginator = Paginator(resultados_list, 5)  # 5 resultados por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    todos_estudiantes = Estudiante.objects.all().order_by('apellido', 'nombre')
    tipos_examen_existentes = Examen.objects.values_list('tipo', flat=True).distinct().order_by('tipo')

    context = {
        'resultados': page_obj,
        'total_resultados_filtrados': total_resultados_filtrados,
        'count_aprobados': count_aprobados,
        'promedio_general_calculado': promedio_general_calculado,
        'examenes_unicos_count': examenes_unicos_count,
        'todos_estudiantes': todos_estudiantes,
        'tipos_examen_existentes': tipos_examen_existentes,
        'UMBRAL_APROBACION': UMBRAL_APROBACION, 
        'query_busqueda_actual': query_busqueda or "",
        'estudiante_filter_actual': estudiante_filter or "",
        'examen_filter_actual': examen_filter or "Todos los exámenes",
        'calificacion_filter_actual': calificacion_filter or "Calificación",
    }
    return render(request, "lista_resultados.html", context)

def listar_materias(request):
    materias_list = Materia.objects.all().order_by('id_materia')

    # Obtener valores únicos para el dropdown de filtro de área
    areas_existentes = Materia.objects.values_list('area', flat=True).distinct().order_by('area')
    areas_existentes = [area for area in areas_existentes if area]

    # Búsqueda y Filtros
    query_busqueda = request.GET.get('q')
    area_filtrada = request.GET.get('area')

    if query_busqueda:
        materias_list = materias_list.filter(nombre__icontains=query_busqueda)
    
    if area_filtrada:
        materias_list = materias_list.filter(area__iexact=area_filtrada)
    
    paginator = Paginator(materias_list, 6) # 6 materias por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Conteos para las tarjetas de estadísticas
    total_materias_count_global = Materia.objects.count()
    # Como no hay campo 'estado' confirmado, asumimos que todas las materias listadas se consideran 'activas' para la tarjeta.
    materias_activas_count = total_materias_count_global 
    numero_areas_unicas = len(areas_existentes)

    return render(request, 'lista_materias.html', {
        'page_obj': page_obj,
        'total_materias_count_global': total_materias_count_global,
        'materias_activas_count': materias_activas_count,
        'numero_areas_unicas': numero_areas_unicas,
        'areas_existentes': areas_existentes,
        'query_busqueda_actual': query_busqueda,
        'area_filtrada_actual': area_filtrada,
    })

def listar_preguntas(request):
    preguntas_list = Pregunta.objects.select_related('examen').all().order_by('-id_pregunta')

    # Búsqueda por enunciado
    query_busqueda = request.GET.get('q')
    if query_busqueda:
        preguntas_list = preguntas_list.filter(enunciado__icontains=query_busqueda)

    # Filtro por Materia (usando el tipo de examen asociado)
    materia_filter = request.GET.get('materia')
    if materia_filter and materia_filter != 'Todas las materias':
        preguntas_list = preguntas_list.filter(examen__tipo__iexact=materia_filter)

    # Filtro por Tipo de Pregunta
    tipo_pregunta_filter = request.GET.get('tipo_pregunta')
    if tipo_pregunta_filter and tipo_pregunta_filter != 'Todos los tipos':
        preguntas_list = preguntas_list.filter(tipo_pregunta__iexact=tipo_pregunta_filter)
    
    materias_existentes = Examen.objects.values_list('tipo', flat=True).distinct().order_by('tipo')
    tipos_pregunta_existentes = Pregunta.objects.values_list('tipo_pregunta', flat=True).distinct().order_by('tipo_pregunta')

    paginator = Paginator(preguntas_list, 5)  # 5 preguntas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_preguntas_filtradas = paginator.count # Total después de filtros
    count_activas_placeholder = total_preguntas_filtradas 
    count_materias_placeholder = len(materias_existentes)

    context = {
        'preguntas': page_obj,
        'total_preguntas_filtradas': total_preguntas_filtradas,
        'count_activas_placeholder': count_activas_placeholder,
        'count_materias_placeholder': count_materias_placeholder,
        'materias_existentes': materias_existentes,
        'tipos_pregunta_existentes': tipos_pregunta_existentes,
        'query_busqueda_actual': query_busqueda or "",
        'materia_filter_actual': materia_filter or "Todas las materias",
        'tipo_pregunta_filter_actual': tipo_pregunta_filter or "Todos los tipos",
    }
    return render(request, "lista_preguntas.html", context)

def listar_respuestas(request):
    respuestas = RespuestaEstudiante.objects.all()
    return render(request, "lista_respuestas.html", {"respuestas": respuestas})

def listar_profesores(request):
    profesores_list = Profesor.objects.all().order_by('id_profesor')

    # Obtener valores únicos para los dropdowns de filtro
    # Se asume que area_especializacion e institucion son campos de texto.
    # Si fueran ForeignKey, se obtendrían de los modelos relacionados.
    especializaciones_existentes = Profesor.objects.values_list('area_especializacion', flat=True).distinct().order_by('area_especializacion')
    especializaciones_existentes = [esp for esp in especializaciones_existentes if esp] # Filtrar None o vacíos

    instituciones_existentes = Profesor.objects.values_list('institucion', flat=True).distinct().order_by('institucion')
    instituciones_existentes = [inst for inst in instituciones_existentes if inst] # Filtrar None o vacíos
    
    # Para el filtro de estado, asumimos 'Activo' e 'Inactivo' como opciones fijas si no hay un campo con choices definidos.
    # Si el modelo Profesor tiene un campo 'estado' con choices, sería mejor derivarlos de ahí.
    # Por ahora, mantenemos la lógica de la plantilla.

    # Búsqueda y Filtros
    query_busqueda = request.GET.get('q')
    especializacion_filtrada = request.GET.get('especializacion')
    institucion_filtrada = request.GET.get('institucion')
    estado_filtrado = request.GET.get('estado')

    if query_busqueda:
        profesores_list = profesores_list.filter(
            Q(nombre__icontains=query_busqueda) |
            Q(apellido__icontains=query_busqueda) |
            Q(identificacion__icontains=query_busqueda) |
            Q(correo__icontains=query_busqueda)
        )
    
    if especializacion_filtrada:
        profesores_list = profesores_list.filter(area_especializacion__iexact=especializacion_filtrada)
    
    if institucion_filtrada:
        profesores_list = profesores_list.filter(institucion__iexact=institucion_filtrada)
        
    if estado_filtrado:
        # Asumimos que el modelo Profesor tiene un campo 'estado' (ej. CharField)
        # Si el campo 'estado' no existe o tiene otro nombre, esto necesitará ajuste.
        # La plantilla actual sugiere que 'estado' existe y puede tener valores como 'Activo'.
        profesores_list = profesores_list.filter(estado__iexact=estado_filtrado)

    paginator = Paginator(profesores_list, 6) # 6 profesores por página, igual que estudiantes
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Conteos para las tarjetas de estadísticas
    total_profesores_count_global = Profesor.objects.count() 
    # Asumiendo que el modelo Profesor tiene un campo 'estado' para este conteo.
    # Si no, este conteo no será preciso o deberá obtenerse de otra forma.
    profesores_activos_count = Profesor.objects.filter(estado__iexact='Activo').count()


    return render(request, 'lista_profesores.html', {
        'page_obj': page_obj,
        'total_profesores_count_global': total_profesores_count_global,
        'profesores_activos_count': profesores_activos_count,
        # Podrías añadir más conteos para otras tarjetas si los datos están disponibles
        # 'numero_especializaciones': ...
        # 'experiencia_promedio_profesores': ...
        'especializaciones_existentes': especializaciones_existentes,
        'instituciones_existentes': instituciones_existentes,
        # No es necesario pasar 'estados_existentes' si son fijos en la plantilla.
        'query_busqueda_actual': query_busqueda,
        'especializacion_filtrada_actual': especializacion_filtrada,
        'institucion_filtrada_actual': institucion_filtrada,
        'estado_filtrado_actual': estado_filtrado,
        # 'profesores': page_obj.object_list # 'profesores' ya no es necesario si se usa page_obj
    })

def listar_administradores(request):
    admin_list = Administrador.objects.all().order_by('-fecha_registro')

    query = request.GET.get('q')
    if query:
        admin_list = admin_list.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(identificacion__icontains=query) |
            Q(correo__icontains=query)
        )

    rol_filter = request.GET.get('rol')
    if rol_filter and rol_filter != 'Todos los roles':
        admin_list = admin_list.filter(rol__iexact=rol_filter)

    total_administradores_filtrados = admin_list.count()
    count_activos = total_administradores_filtrados # Asumiendo que todos los listados están activos
    
    rol_super_admin = "Super Admin"
    count_super_admins = admin_list.filter(rol__iexact=rol_super_admin).count()

    from django.utils import timezone
    from datetime import timedelta
    treinta_dias_atras = timezone.now() - timedelta(days=30)
    count_ultimos_30_dias = admin_list.filter(fecha_registro__gte=treinta_dias_atras).count()

    paginator = Paginator(admin_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    roles_existentes = Administrador.objects.values_list('rol', flat=True).distinct().order_by('rol')

    context = {
        "administradores": page_obj,
        "total_administradores_filtrados": total_administradores_filtrados,
        "count_activos": count_activos,
        "count_super_admins": count_super_admins,
        "count_ultimos_30_dias": count_ultimos_30_dias,
        "roles_existentes": roles_existentes,
        "query_actual": query or "",
        "rol_filter_actual": rol_filter or "Todos los roles",
    }
    return render(request, "lista_administradores.html", context)

# VISTAS DE ELIMINACIÓN
def eliminar_estudiante(request, pk):
    estudiante = get_object_or_404(Estudiante, id_estudiante=pk)
    estudiante.delete()
    messages.success(request, 'Estudiante eliminado exitosamente.')
    return redirect('base:listar_estudiantes')

def eliminar_examen(request, pk):
    examen = get_object_or_404(Examen, id_examen=pk)
    examen.delete()
    messages.success(request, 'Examen eliminado exitosamente.')
    return redirect('base:listar_examenes')

def eliminar_resultado(request, pk):
    resultado = get_object_or_404(Resultado, id_resultado=pk)
    resultado.delete()
    messages.success(request, 'Resultado eliminado exitosamente.')
    return redirect('base:listar_resultados')

def eliminar_materia(request, pk):
    materia = get_object_or_404(Materia, id_materia=pk)
    materia.delete()
    messages.success(request, 'Materia eliminada exitosamente.')
    return redirect('base:listar_materias')

def eliminar_pregunta(request, pk):
    pregunta = get_object_or_404(Pregunta, id_pregunta=pk)
    pregunta.delete()
    messages.success(request, 'Pregunta eliminada exitosamente.')
    return redirect('base:listar_preguntas')

def eliminar_respuesta(request, pk):
    respuesta = get_object_or_404(RespuestaEstudiante, id_respuesta=pk)
    respuesta.delete()
    messages.success(request, 'Respuesta eliminada exitosamente.')
    return redirect('base:listar_respuestas')

def eliminar_profesor(request, pk):
    profesor = get_object_or_404(Profesor, id_profesor=pk)
    profesor.delete()
    messages.success(request, 'Profesor eliminado exitosamente.')
    return redirect('base:listar_profesores')

def eliminar_administrador(request, pk):
    administrador = get_object_or_404(Administrador, id_administrador=pk)
    administrador.delete()
    messages.success(request, 'Administrador eliminado exitosamente.')
    return redirect('base:listar_administradores')

def editar_estudiante(request, pk):
    estudiante = get_object_or_404(Estudiante, id_estudiante=pk)
    
    if request.method == "POST":
        form = EstudianteForm(request.POST, instance=estudiante)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Estudiante actualizado exitosamente.')
            return redirect("base:listar_estudiantes")
        else:
            print(form.errors)  # Muestra errores en consola

    else:
        form = EstudianteForm(instance=estudiante)
    
    return render(request, "editar_estudiante.html", {"form": form})

# Editar Examen
def editar_examen(request, pk):
    examen = get_object_or_404(Examen, id_examen=pk)
    if request.method == "POST":
        form = ExamenForm(request.POST, instance=examen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Examen actualizado exitosamente.')
            return redirect("base:listar_examenes")
    else:
        form = ExamenForm(instance=examen)
    return render(request, "editar_examen.html", {"form": form})

# Editar Resultado
def editar_resultado(request, pk):
    resultado = get_object_or_404(Resultado, id_resultado=pk)
    if request.method == "POST":
        form = ResultadoForm(request.POST, instance=resultado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resultado actualizado exitosamente.')
            return redirect("base:listar_resultados")
    else:
        form = ResultadoForm(instance=resultado)
    return render(request, "editar_resultado.html", {"form": form})

# Editar Materia
def editar_materia(request, pk):
    materia = get_object_or_404(Materia, id_materia=pk)
    if request.method == "POST":
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada exitosamente.')
            return redirect("base:listar_materias")
    else:
        form = MateriaForm(instance=materia)
    return render(request, "editar_materia.html", {"form": form})

# Editar Pregunta
def editar_pregunta(request, pk):
    pregunta = get_object_or_404(Pregunta, id_pregunta=pk)
    if request.method == "POST":
        form = PreguntaForm(request.POST, instance=pregunta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pregunta actualizada exitosamente.')
            return redirect("base:listar_preguntas")
    else:
        form = PreguntaForm(instance=pregunta)
    return render(request, "editar_pregunta.html", {"form": form})

# Editar Respuesta del Estudiante
def editar_respuesta(request, pk):
    respuesta = get_object_or_404(RespuestaEstudiante, id_respuesta=pk)
    if request.method == "POST":
        form = RespuestaEstudianteForm(request.POST, instance=respuesta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Respuesta actualizada exitosamente.')
            return redirect("base:listar_respuestas")
    else:
        form = RespuestaEstudianteForm(instance=respuesta)
    return render(request, "editar_respuesta.html", {"form": form})

# Editar Profesor
def editar_profesor(request, pk):
    profesor = get_object_or_404(Profesor, id_profesor=pk)
    if request.method == "POST":
        form = ProfesorForm(request.POST, instance=profesor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor actualizado exitosamente.')
            return redirect("base:listar_profesores")
    else:
        form = ProfesorForm(instance=profesor)
    return render(request, "editar_profesor.html", {"form": form})

# Editar Administrador
def editar_administrador(request, pk):
    administrador = get_object_or_404(Administrador, id_administrador=pk)
    if request.method == "POST":
        form = AdministradorForm(request.POST, instance=administrador)
        if form.is_valid():
            form.save()
            messages.success(request, 'Administrador actualizado exitosamente.')
            return redirect("base:listar_administradores")
    else:
        form = AdministradorForm(instance=administrador)
    return render(request, "editar_administrador.html", {"form": form})

def agregar_estudiante(request):
    if request.method == 'POST':
        form = EstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estudiante agregado exitosamente.')
            return redirect('base:listar_estudiantes')
    else:
        form = EstudianteForm()
    
    return render(request, 'agregar_estudiante.html', {'form': form})

def agregar_respuesta(request):
    if request.method == 'POST':
        form = RespuestaEstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Respuesta agregada exitosamente.')
            return redirect('base:listar_respuestas')
    else:
        form = RespuestaEstudianteForm()
    
    return render(request, 'agregar_respuesta.html', {'form': form})

def agregar_resultado(request):
    if request.method == 'POST':
        form = ResultadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resultado agregado exitosamente.')
            return redirect('base:listar_resultados')  
    else:
        form = ResultadoForm()
    
    return render(request, 'agregar_resultado.html', {'form': form})

def agregar_examen(request):
    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Examen agregado exitosamente.')
            return redirect('base:listar_examenes')
    else:
        form = ExamenForm()
    
    return render(request, 'agregar_examen.html', {'form': form})

def agregar_profesor(request):
    if request.method == 'POST':
        form = ProfesorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor agregado exitosamente.')
            return redirect('base:listar_profesores')  
    else:
        form = ProfesorForm()
    
    return render(request, 'agregar_profesor.html', {'form': form})

def agregar_materia(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia agregada exitosamente.')
            return redirect('base:listar_materias')
    else:
        form = MateriaForm()
    
    return render(request, 'agregar_materia.html', {'form': form})

def agregar_administrador(request):
    if request.method == 'POST':
        form = AdministradorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Administrador agregado exitosamente.')
            return redirect('base:listar_administradores')
    else:
        form = AdministradorForm()
    
    return render(request, 'agregar_administrador.html', {'form': form})

def agregar_pregunta(request, examen_id):
    if request.method == 'POST':
        enunciado = request.POST.get('enunciado')
        tipo_pregunta = request.POST.get('tipo_pregunta')
        respuesta_correcta_seleccionada = request.POST.get('respuesta_correcta_selector') 
        respuestas_textos = request.POST.getlist('respuestas')

        # Validación básica
        if not enunciado or not respuesta_correcta_seleccionada or not respuestas_textos:
            return render(request, 'profesor/agregar_pregunta.html', {
                'error': 'Por favor completa todos los campos y selecciona una respuesta correcta.',
                'examen_id': examen_id
            })

        # Determinar el valor final para respuesta_correcta a guardar
        respuesta_correcta_final = ''
        if tipo_pregunta == "Opción Múltiple":
            try:
                indice_correcto = int(respuesta_correcta_seleccionada)
                if 0 <= indice_correcto < len(respuestas_textos):
                    # Para Opción Múltiple, AHORA guardamos el ÍNDICE como string.
                    respuesta_correcta_final = str(indice_correcto)
                else:
                    return render(request, 'profesor/agregar_pregunta.html', {
                        'error': 'El índice de la respuesta correcta no es válido.',
                        'examen_id': examen_id
                    })
            except ValueError:
                return render(request, 'profesor/agregar_pregunta.html', {
                    'error': 'El valor de la respuesta correcta para opción múltiple debe ser un índice numérico.',
                    'examen_id': examen_id
                })
        elif tipo_pregunta == "Verdadero/Falso":
            # Para Verdadero/Falso, el valor ya es "Verdadero" o "Falso"
            respuesta_correcta_final = respuesta_correcta_seleccionada
        else:
            # Manejar otros tipos de pregunta si existen
            return render(request, 'profesor/agregar_pregunta.html', {
                'error': 'Tipo de pregunta no soportado para determinar respuesta correcta.',
                'examen_id': examen_id
            })

        Pregunta.objects.create(
            examen_id=examen_id,
            enunciado=enunciado,
            tipo_pregunta=tipo_pregunta,
            respuestas_posibles={str(i): r for i, r in enumerate(respuestas_textos)},
            respuesta_correcta=respuesta_correcta_final
        )

        messages.success(request, 'Pregunta agregada exitosamente al módulo.')
        return redirect('base:panel_profesor')

    return render(request, 'profesor/agregar_pregunta.html', {'examen_id': examen_id})

def estudiante_home(request):
    estudiante_id = request.session.get('estudiante_id')

    if not estudiante_id:
        return redirect('base:login_estudiante')

    estudiante = Estudiante.objects.get(id_estudiante=estudiante_id)
    resultados = Resultado.objects.filter(estudiante=estudiante).order_by('-fecha_resultado')

    # Obtener el mejor resultado de cada materia
    ma = resultados.aggregate(Max('matematicas'))['matematicas__max'] or 0
    lc = resultados.aggregate(Max('lectura_critica'))['lectura_critica__max'] or 0
    cn = resultados.aggregate(Max('ciencias_naturales'))['ciencias_naturales__max'] or 0
    sc = resultados.aggregate(Max('sociales_ciudadanas'))['sociales_ciudadanas__max'] or 0
    ing = resultados.aggregate(Max('ingles'))['ingles__max'] or 0

    # Puntaje global según la mejor nota por materia
    materias_sum_ponderada = (ma * 3 + lc * 3 + cn * 3 + sc * 3 + ing)
    
    if materias_sum_ponderada > 0:
        # PGI = ((MA*3 + LC*3 + CN*3 + SC*3 + IN) / 13) * 5
        puntaje_global = round((materias_sum_ponderada / 13) * 5)
    else:
        puntaje_global = 0

    # Calcular nivel general basado en puntaje promedio (escala 0-500)
    # Ajustar umbrales según necesidad. Ejemplo:
    # Nivel 1: 0-199
    # Nivel 2: 200-349
    # Nivel 3: 350-500
    nivel_general = 1 if puntaje_global < 200 else 2 if puntaje_global < 350 else 3
    total_simulacros = resultados.count()

    # Calcular tiempo promedio real basado en duración de exámenes
    examenes_tomados = [r.examen for r in resultados if r.examen]
    tiempo_promedio = 45  # Valor por defecto
    if examenes_tomados:
        duraciones = [e.duracion for e in examenes_tomados if e.duracion]
        if duraciones:
            tiempo_promedio = round(sum(duraciones) / len(duraciones))

    # Obtener resultados por materia para el historial
    resultados_lectura = resultados.filter(examen__tipo='Lectura Critica', lectura_critica__gte=0)
    resultados_matematicas = resultados.filter(examen__tipo='Matematicas', matematicas__gte=0)
    resultados_sociales = resultados.filter(examen__tipo='Ciencias Sociales', sociales_ciudadanas__gte=0)
    resultados_ciencias = resultados.filter(examen__tipo='Ciencias Naturales', ciencias_naturales__gte=0)
    resultados_ingles = resultados.filter(examen__tipo='Ingles', ingles__gte=0)

    # Agregar datos calculados a cada resultado para el template
    for resultado in resultados_lectura:
        if resultado.examen:
            total_preguntas = resultado.examen.pregunta_set.count()
            resultado.total_preguntas_examen = total_preguntas
            if total_preguntas > 0:
                resultado.correctas_reales = round((resultado.lectura_critica / 100) * total_preguntas)
                resultado.incorrectas_reales = total_preguntas - resultado.correctas_reales
            else:
                resultado.correctas_reales = 0
                resultado.incorrectas_reales = 0
        else:
            resultado.total_preguntas_examen = 0
            resultado.correctas_reales = 0
            resultado.incorrectas_reales = 0
        resultado.nivel_lectura = 3 if resultado.lectura_critica >= 70 else 2 if resultado.lectura_critica >= 40 else 1

    for resultado in resultados_matematicas:
        if resultado.examen:
            total_preguntas = resultado.examen.pregunta_set.count()
            resultado.total_preguntas_examen = total_preguntas
            if total_preguntas > 0:
                resultado.correctas_reales = round((resultado.matematicas / 100) * total_preguntas)
                resultado.incorrectas_reales = total_preguntas - resultado.correctas_reales
            else:
                resultado.correctas_reales = 0
                resultado.incorrectas_reales = 0
        else:
            resultado.total_preguntas_examen = 0
            resultado.correctas_reales = 0
            resultado.incorrectas_reales = 0
        resultado.nivel_matematicas = 3 if resultado.matematicas >= 70 else 2 if resultado.matematicas >= 40 else 1

    for resultado in resultados_sociales:
        if resultado.examen:
            total_preguntas = resultado.examen.pregunta_set.count()
            resultado.total_preguntas_examen = total_preguntas
            if total_preguntas > 0:
                resultado.correctas_reales = round((resultado.sociales_ciudadanas / 100) * total_preguntas)
                resultado.incorrectas_reales = total_preguntas - resultado.correctas_reales
            else:
                resultado.correctas_reales = 0
                resultado.incorrectas_reales = 0
        else:
            resultado.total_preguntas_examen = 0
            resultado.correctas_reales = 0
            resultado.incorrectas_reales = 0
        resultado.nivel_sociales = 3 if resultado.sociales_ciudadanas >= 70 else 2 if resultado.sociales_ciudadanas >= 40 else 1

    for resultado in resultados_ciencias:
        if resultado.examen:
            total_preguntas = resultado.examen.pregunta_set.count()
            resultado.total_preguntas_examen = total_preguntas
            if total_preguntas > 0:
                resultado.correctas_reales = round((resultado.ciencias_naturales / 100) * total_preguntas)
                resultado.incorrectas_reales = total_preguntas - resultado.correctas_reales
            else:
                resultado.correctas_reales = 0
                resultado.incorrectas_reales = 0
        else:
            resultado.total_preguntas_examen = 0
            resultado.correctas_reales = 0
            resultado.incorrectas_reales = 0
        resultado.nivel_ciencias = 3 if resultado.ciencias_naturales >= 70 else 2 if resultado.ciencias_naturales >= 40 else 1

    for resultado in resultados_ingles:
        if resultado.examen:
            total_preguntas = resultado.examen.pregunta_set.count()
            resultado.total_preguntas_examen = total_preguntas
            if total_preguntas > 0:
                resultado.correctas_reales = round((resultado.ingles / 100) * total_preguntas)
                resultado.incorrectas_reales = total_preguntas - resultado.correctas_reales
            else:
                resultado.correctas_reales = 0
                resultado.incorrectas_reales = 0
        else:
            resultado.total_preguntas_examen = 0
            resultado.correctas_reales = 0
            resultado.incorrectas_reales = 0
        resultado.nivel_ingles = 3 if resultado.ingles >= 70 else 2 if resultado.ingles >= 40 else 1

    # Calcular progreso por materia (porcentaje del mejor puntaje sobre 100)
    progreso_materias = {
        'lectura': min(lc, 100),
        'matematicas': min(ma, 100),
        'sociales': min(sc, 100),
        'ciencias': min(cn, 100),
        'ingles': min(ing, 100),
        'general': round((puntaje_global / 500) * 100) if puntaje_global > 0 else 0 # Normalizado a 0-100 para el gráfico
    }

    # Calcular nivel por materia
    niveles_materias = {
        'lectura': 1 if lc < 40 else 2 if lc < 70 else 3,
        'matematicas': 1 if ma < 40 else 2 if ma < 70 else 3,
        'sociales': 1 if sc < 40 else 2 if sc < 70 else 3,
        'ciencias': 1 if cn < 40 else 2 if cn < 70 else 3,
        'ingles': 1 if ing < 40 else 2 if ing < 70 else 3,
    }

    # Datos del estudiante del modelo
    estudiante_info = {
        'nombre_completo': f"{estudiante.nombre} {estudiante.apellido}",
        'institucion': estudiante.institucion or 'No especificada',
        'grado': estudiante.grado or 'No especificado',
        'tipo_institucion': estudiante.tipo_institucion,
        'genero': estudiante.genero,
        'fecha_inscripcion': estudiante.fecha_inscripcion,
    }

    # Determinar texto del nivel
    nivel_texto = 'Principiante' if nivel_general == 1 else 'Intermedio' if nivel_general == 2 else 'Avanzado'

    return render(request, 'estudiante_home.html', {
        'estudiante': estudiante,
        'estudiante_info': estudiante_info,
        'resultados': resultados,
        'resultados_lectura': resultados_lectura,
        'resultados_matematicas': resultados_matematicas,
        'resultados_sociales': resultados_sociales,
        'resultados_ciencias': resultados_ciencias,
        'resultados_ingles': resultados_ingles,
        'puntaje_global': puntaje_global,
        'nivel_general': nivel_general,
        'nivel_texto': nivel_texto,
        'total_simulacros': total_simulacros,
        'tiempo_promedio': tiempo_promedio,
        'progreso_materias': progreso_materias,
        'niveles_materias': niveles_materias,
        'mejores_puntajes': {
            'lectura': lc,
            'matematicas': ma,
            'sociales': sc,
            'ciencias': cn,
            'ingles': ing,
        }
    })

@csrf_exempt
def simulacro(request, examen_id, pregunta_index):
    examen = get_object_or_404(Examen, id_examen=examen_id)
    # Convertir a lista para poder usar índices numéricos consistentemente
    preguntas = list(Pregunta.objects.filter(examen=examen).order_by('id_pregunta'))
    total_preguntas = len(preguntas)

    # Manejo si no hay preguntas en el examen
    if total_preguntas == 0:
        messages.error(request, f"El simulacro '{examen.tipo}' no tiene preguntas asignadas.")
        # Redirigir a una página apropiada, por ejemplo, el home del estudiante o el listado de exámenes
        if request.session.get('estudiante_id'):
            return redirect('base:estudiante_home')
        elif request.session.get('profesor_id'):
             return redirect('base:panel_profesor')
        else:
            return redirect('base:inicio') # O una página de error general

    # Redirigir a resultados si el índice está fuera de rango (al inicio o después de la última pregunta)
    if pregunta_index >= total_preguntas and total_preguntas > 0 : # Si hay preguntas pero el índice es muy alto
        return redirect('base:resultado_simulacro')
    if pregunta_index < 0: # Si el índice es negativo
        pregunta_index = 0 # Corregir al inicio


    # Inicializar o verificar la sesión del simulacro
    if 'examen_id' not in request.session or request.session.get('examen_id') != examen_id:
        request.session['examen_id'] = examen_id
        request.session['inicio_simulacro'] = timezone.now().isoformat()
        # Usar un diccionario para 'respuestas_usuario' donde la clave es el índice de la pregunta (como string)
        request.session['respuestas_usuario'] = {} 
        # Asegurarse de que, si es un nuevo simulacro, el índice comience en 0,
        # independientemente de lo que venga en la URL, si el examen_id cambió.
        if request.session.get('examen_id') == examen_id and pregunta_index != 0 :
             # Esto podría ser una reentrada a un simulacro diferente, forzar a la primera pregunta.
             # O si se está iniciando el simulacro, asegurar que empieza en la primera.
             if not request.session.get('respuestas_usuario'): # Solo si no hay respuestas guardadas aún.
                return redirect('base:simulacro', examen_id=examen_id, pregunta_index=0)


    if request.method == "POST":
        accion = request.POST.get('accion', 'siguiente')
        respuesta_seleccionada = request.POST.get('respuesta') # Este es el TEXTO de la opción

        # Guardar respuesta solo si se seleccionó algo
        if respuesta_seleccionada and (0 <= pregunta_index < total_preguntas):
            respuestas_guardadas_en_sesion = request.session.get('respuestas_usuario', {})
            current_pregunta_obj = preguntas[pregunta_index]
            
            es_correcta_calculada_para_sesion = False
            texto_para_mostrar_respuesta_correcta_en_sesion = "Error: Respuesta correcta no determinada"

            if current_pregunta_obj.tipo_pregunta == "Opción Múltiple":
                texto_real_opcion_correcta = None
                # rc_val_from_db es lo que está en Pregunta.respuesta_correcta
                rc_val_from_db = str(current_pregunta_obj.respuesta_correcta).strip()
                # rp_val_from_db es lo que está en Pregunta.respuestas_posibles (dict o list)
                rp_val_from_db = current_pregunta_obj.respuestas_posibles

                if isinstance(rp_val_from_db, dict):
                    # Intento 1: rc_val_from_db es una CLAVE en el diccionario de opciones
                    if rc_val_from_db in rp_val_from_db:
                        texto_real_opcion_correcta = str(rp_val_from_db[rc_val_from_db]).strip()
                    # Intento 2: rc_val_from_db es el TEXTO de una de las opciones
                    else:
                        rc_val_lower_for_text_match = rc_val_from_db.lower()
                        for texto_opcion_en_dict in rp_val_from_db.values():
                            if str(texto_opcion_en_dict).strip().lower() == rc_val_lower_for_text_match:
                                texto_real_opcion_correcta = str(texto_opcion_en_dict).strip()
                                break
                elif isinstance(rp_val_from_db, list):
                    # Intento 1: rc_val_from_db es un ÍNDICE numérico para la lista de opciones
                    try:
                        idx = int(rc_val_from_db)
                        if 0 <= idx < len(rp_val_from_db):
                            texto_real_opcion_correcta = str(rp_val_from_db[idx]).strip()
                    # Intento 2: rc_val_from_db es el TEXTO de una de las opciones en la lista
                    except ValueError: # rc_val_from_db no era un entero, así que no puede ser índice directo
                        rc_val_lower_for_text_match = rc_val_from_db.lower()
                        for texto_opcion_en_lista in rp_val_from_db:
                            if str(texto_opcion_en_lista).strip().lower() == rc_val_lower_for_text_match:
                                texto_real_opcion_correcta = str(texto_opcion_en_lista).strip()
                                break

                if texto_real_opcion_correcta is not None:
                    texto_para_mostrar_respuesta_correcta_en_sesion = texto_real_opcion_correcta
                    if respuesta_seleccionada.strip().lower() == texto_real_opcion_correcta.lower():
                        es_correcta_calculada_para_sesion = True

            elif current_pregunta_obj.tipo_pregunta == "Verdadero/Falso":
                texto_de_opcion_correcta_real = str(current_pregunta_obj.respuesta_correcta).strip()
                texto_para_mostrar_respuesta_correcta_en_sesion = texto_de_opcion_correcta_real
                if respuesta_seleccionada.strip().lower() == texto_de_opcion_correcta_real.lower():
                    es_correcta_calculada_para_sesion = True

            respuestas_guardadas_en_sesion[str(pregunta_index)] = {
                'pregunta_id_db': current_pregunta_obj.id_pregunta, # Guardar ID para referencia
                'enunciado': current_pregunta_obj.enunciado,
                'respuesta_usuario': respuesta_seleccionada,
                'respuesta_correcta_original_db': current_pregunta_obj.respuesta_correcta, # Para debugging
                'texto_respuesta_correcta_determinado': texto_para_mostrar_respuesta_correcta_en_sesion,
                'es_correcta': es_correcta_calculada_para_sesion,
                'tipo_pregunta': current_pregunta_obj.tipo_pregunta,
                'opciones_original_db': current_pregunta_obj.respuestas_posibles # Para debugging
            }
            request.session['respuestas_usuario'] = respuestas_guardadas_en_sesion

        if accion == 'anterior':
            next_index = pregunta_index - 1
            if next_index < 0: # No permitir ir antes de la primera pregunta
                next_index = 0 
        elif accion == 'finalizar':
            return redirect('base:resultado_simulacro')
        else:  # 'siguiente' o default
            next_index = pregunta_index + 1
            if next_index >= total_preguntas: # Si es la última y da siguiente, o si ya está fuera de rango
                return redirect('base:resultado_simulacro')
        
        # Solo redirigir si next_index es válido y diferente al actual o si se finaliza
        return redirect('base:simulacro', examen_id=examen_id, pregunta_index=next_index)

    # --- Lógica para GET (mostrar la pregunta) ---
    # Asegurarse de que pregunta_index sea válido para mostrar; si no, redirigir.
    if not (0 <= pregunta_index < total_preguntas):
        # Podría ser que se accedió a una URL con un índice inválido.
        # Redirigir al inicio del simulacro o a resultados podría ser una opción.
        # Por ahora, si está fuera de rango al inicio (GET), lo llevamos a la primera.
        # Si el total_preguntas es 0, esto también debe manejarse.
        if total_preguntas == 0:
             messages.error(request, f"El examen '{examen.tipo}' no tiene preguntas.")
             return redirect('base:estudiante_home') # O a donde sea apropiado
        # Si hay preguntas, pero el índice es malo, ir a la primera o última válida.
        # Aquí asumimos que si es inválido en GET, es porque se está intentando acceder a una pregunta que no existe.
        # Una opción es llevarlo a la primera.
        # return redirect('base:simulacro', examen_id=examen_id, pregunta_index=0)
        # O a resultados, si ya pasó el final.
        return redirect('base:resultado_simulacro')


    pregunta_actual = preguntas[pregunta_index]
    respuestas_guardadas = request.session.get('respuestas_usuario', {})
    respuesta_previa_info = respuestas_guardadas.get(str(pregunta_index), {})
    respuesta_previa_seleccionada = respuesta_previa_info.get('respuesta_usuario', '')
    
    opciones_para_plantilla = []
    if isinstance(pregunta_actual.respuestas_posibles, dict):
        opciones_para_plantilla = list(pregunta_actual.respuestas_posibles.values())
    elif isinstance(pregunta_actual.respuestas_posibles, list):
        opciones_para_plantilla = pregunta_actual.respuestas_posibles
    
    context = {
        'examen': examen, # Pasar el objeto examen completo
        'pregunta': pregunta_actual,
        'pregunta_index': pregunta_index,
        'total_preguntas': total_preguntas, # Renombrado para claridad
        'examen_id': examen_id,
        'opciones': opciones_para_plantilla,
        'tipo': examen.tipo, # Aunque ya está en examen.tipo
        'respuesta_previa': respuesta_previa_seleccionada
    }
    return render(request, 'modulos/simulacro.html', context)

def iniciar_simulacro(request, tipo_examen):
    examen = get_object_or_404(Examen, tipo=tipo_examen)
    request.session['examen_id'] = examen.id_examen
    request.session['inicio_simulacro'] = timezone.now().isoformat()
    request.session['respuestas_usuario'] = {}
    return redirect('base:simulacro', examen_id=examen.id_examen, pregunta_index=0)

def resultado_simulacro(request):
    estudiante_id = request.session.get('estudiante_id')
    examen_id_sesion = request.session.get('examen_id') # Usar un nombre diferente para evitar conflicto si se pasa examen_id en contexto
    respuestas_usuario = request.session.get('respuestas_usuario', {})

    correctas = sum(1 for respuesta in respuestas_usuario.values() if respuesta.get('es_correcta', False))
    total_preguntas_respondidas = len(respuestas_usuario)
    incorrectas = total_preguntas_respondidas - correctas
    
    # 'puntaje_final_porcentaje' es el porcentaje de aciertos (0-100) para el examen actual.
    puntaje_final_porcentaje = round((correctas / total_preguntas_respondidas) * 100) if total_preguntas_respondidas else 0
    nivel = 1 if puntaje_final_porcentaje < 40 else 2 if puntaje_final_porcentaje < 70 else 3

    inicio_str = request.session.get('inicio_simulacro')
    tiempo_total_segundos = 0
    if inicio_str:
        inicio = parse_datetime(inicio_str)
        if inicio: # Asegurarse que parse_datetime no devolvió None
            tiempo_total_segundos = (now() - inicio).total_seconds()

    examen_obj_para_contexto = None # Para el tipo de simulacro en el contexto

    if estudiante_id and examen_id_sesion:
        estudiante = get_object_or_404(Estudiante, id_estudiante=estudiante_id)
        examen_obj = get_object_or_404(Examen, id_examen=examen_id_sesion)
        examen_obj_para_contexto = examen_obj # Asignar para el contexto

        # Datos base para guardar el resultado.
        # Resultado.puntaje_global almacenará el % de aciertos (0-100) de este examen específico.
        data_para_resultado = {
            "estudiante": estudiante,
            "examen": examen_obj,
            "puntaje_global": puntaje_final_porcentaje, 
            # Inicializar los campos de materia ICFES específicos.
            "lectura_critica": 0,
            "matematicas": 0,
            "sociales_ciudadanas": 0,
            "ciencias_naturales": 0,
            "ingles": 0,
        }

        # Mapeo de tipos de examen ICFES a los campos del modelo Resultado.
        mapa_materias_icfes = {
            "Lectura Critica": "lectura_critica",
            "Matematicas": "matematicas",
            "Ciencias Naturales": "ciencias_naturales",
            "Ciencias Sociales": "sociales_ciudadanas",
            "Ingles": "ingles",
        }
        campo_materia_actual = mapa_materias_icfes.get(examen_obj.tipo)
        if campo_materia_actual:
            # Si es un examen de tipo ICFES, guardamos el mismo puntaje (0-100)
            # en el campo de la materia correspondiente para mantener la lógica de estudiante_home.
            data_para_resultado[campo_materia_actual] = puntaje_final_porcentaje
        
        Resultado.objects.create(**data_para_resultado)

    respuestas_para_template = list(respuestas_usuario.values())
    request.session['respuestas_resultado'] = respuestas_para_template

    # Limpiar sesión del simulacro
    for key_to_pop in ['inicio_simulacro', 'examen_id', 'respuestas_usuario']:
        request.session.pop(key_to_pop, None)

    contexto_resultado = {
        'correctas': correctas,
        'incorrectas': incorrectas,
        'puntaje': puntaje_final_porcentaje,
        'nivel': nivel,
        'tiempo_examen_minutos': round(tiempo_total_segundos / 60) if tiempo_total_segundos > 0 else 0,
        'tiempo_por_pregunta': round(tiempo_total_segundos / total_preguntas_respondidas, 1) if total_preguntas_respondidas > 0 else 0,
        'porcentaje_correctas': puntaje_final_porcentaje,
        'porcentaje_incorrectas': round((incorrectas / total_preguntas_respondidas) * 100) if total_preguntas_respondidas > 0 else 0,
        'porcentaje_nivel': nivel * 33, 
        'total': total_preguntas_respondidas,
        'examen_id': examen_id_sesion, # Necesario para el botón "Ver Respuestas"
        'tipo_simulacro': examen_obj_para_contexto.tipo if examen_obj_para_contexto else "Simulacro"
    }
    return render(request, 'modulos/resultado_simulacro.html', contexto_resultado)

def login_estudiante(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        password = request.POST.get('password')

        try:
            estudiante = Estudiante.objects.get(correo=correo)
            # Modificación: Comparación directa de contraseña
            if estudiante.contraseña == password:
                request.session['estudiante_id'] = estudiante.id_estudiante
                request.session['estudiante_nombre'] = f"{estudiante.nombre} {estudiante.apellido}"
                return redirect('base:estudiante_home')
            else:
                return render(request, 'Sesion/login.html', {'error': 'Contraseña incorrecta'})
        except Estudiante.DoesNotExist:
            return render(request, 'Sesion/login.html', {'error': 'El correo no está registrado'})

    return render(request, 'Sesion/login.html')

def fin_simulacro(request):
    return redirect('base:resultado_simulacro')

def signup_estudiante(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        genero = request.POST.get('genero')
        identificacion = request.POST.get('identificacion')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono') or None
        direccion = request.POST.get('direccion') or None
        institucion = request.POST.get('institucion') or None
        tipo_institucion = request.POST.get('tipo_institucion') or 'Pública'
        grado = request.POST.get('grado') or None
        contraseña = request.POST.get('contraseña')
        confirmar = request.POST.get('confirmar')

        # Validaciones
        if contraseña != confirmar:
            return render(request, 'Sesion/signup.html', {'error': 'Las contraseñas no coinciden.'})

        if Estudiante.objects.filter(correo=correo).exists():
            return render(request, 'Sesion/signup.html', {'error': 'El correo ya está registrado.'})

        if Estudiante.objects.filter(identificacion=identificacion).exists():
            return render(request, 'Sesion/signup.html', {'error': 'La identificación ya está registrada.'})

        # Crear estudiante
        Estudiante.objects.create(
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            identificacion=identificacion,
            correo=correo,
            telefono=telefono,
            direccion=direccion,
            institucion=institucion,
            tipo_institucion=tipo_institucion,
            grado=grado,
            fecha_inscripcion=now(),
            # Modificación: Guardar contraseña directamente
            contraseña=contraseña
        )

        return redirect('base:login_estudiante')

    return render(request, 'Sesion/signup.html')

def ver_respuestas(request):
    respuestas = request.session.get('respuestas_resultado', [])
    # Recuperar el examen_id guardado en la sesión
    examen_id = request.session.get('examen_id_para_ver_respuestas')
    # Convertir las respuestas a JSON para el JS del template
    respuestas_json = json.dumps(respuestas, ensure_ascii=False)
    # (Opcional) Limpiar el examen_id de la sesión después de usarlo
    if 'examen_id_para_ver_respuestas' in request.session:
        del request.session['examen_id_para_ver_respuestas']

    context = {
        'respuestas': respuestas,
        'respuestas_json': respuestas_json,
        'examen_id': examen_id,
    }
    return render(request, 'modulos/ver_respuestas.html', context)
    



@csrf_exempt
def send_corrections(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            incorrectas = data.get('incorrectas', [])
            if not incorrectas:
                return JsonResponse({'correcciones': []})

            prompt = "Estas son respuestas incorrectas de un estudiante. Por favor, explica cada error y luego enseña brevemente cómo resolverlo correctamente:\n"
            for r in incorrectas:
                # Usar los nombres de clave correctos de tu objeto de respuesta
                enunciado_pregunta = r.get('enunciado', 'Pregunta no disponible') 
                respuesta_correcta_texto = r.get('texto_respuesta_correcta_determinado', 'Respuesta correcta no disponible')
                
                prompt += (
                    f"\nPregunta: {enunciado_pregunta}"
                    f"\nRespuesta del estudiante: {r.get('respuesta_usuario', 'No respondida')}"
                    f"\nRespuesta correcta: {respuesta_correcta_texto}\n"
                )

            client = genai.Client(api_key=API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=[prompt + "\nPor cada error, explica por qué la respuesta es incorrecta y enseña cómo se debe hacer correctamente. Usa lenguaje claro y educativo. Solamente un parrafo por cada error. No uses * para negritas, usa el lenguaje normal. y respuestas cortas, no uses _ para negritas, usa el lenguaje normal. tampoco uses ** para negritas, usa el lenguaje normal. tampoco uses __ para negritas, usa el lenguaje normal. tampoco uses *** para negritas, usa el lenguaje normal. tampoco uses ___ para negritas, usa el lenguaje normal."], # 'contents' usualmente espera una lista
            )
            
            # Para Gemini API, la respuesta de texto podría estar en response.text o response.parts[0].text
            # dependiendo de la versión y configuración.
            # Es más seguro verificar la estructura de 'response'
            correccion_texto = ""
            if hasattr(response, 'text') and response.text:
                correccion_texto = response.text
            elif hasattr(response, 'parts') and response.parts and hasattr(response.parts[0], 'text'):
                correccion_texto = response.parts[0].text
            else:
                # Imprime la respuesta completa para depurar si no se encuentra el texto
                print("Respuesta completa de la API de GenAI:", response)
                return JsonResponse({'correcciones': "No se pudo extraer texto de la respuesta del modelo."})

            return JsonResponse({'correcciones': correccion_texto})

        except Exception as e:
            print(f"Error en send_corrections: {type(e).__name__} - {e}")
            # Para depuración, podrías retornar más detalles del error si estás en modo DEBUG
            # import traceback
            # print(traceback.format_exc())
            # if settings.DEBUG:
            #    return JsonResponse({'error': f'Error interno del servidor: {str(e)}', 'trace': traceback.format_exc()}, status=500)
            return JsonResponse({'error': 'Error interno del servidor al procesar la solicitud.'}, status=500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def panel_profesor(request):
    profesor_id = request.session.get('profesor_id')
    if not profesor_id:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('base:login_profesor')

    profesor = get_object_or_404(Profesor, id_profesor=profesor_id)
    examenes = Examen.objects.filter(profesor=profesor).prefetch_related('pregunta_set').annotate(resultados_count=Count('resultado'))

    # Calcular estadísticas
    total_modulos_profesor = examenes.count()
    total_preguntas_profesor = 0
    total_realizaciones_profesor = 0

    for examen in examenes:
        total_preguntas_profesor += examen.pregunta_set.count()
        total_realizaciones_profesor += examen.resultados_count

    # Esquemas de estilo y iconos para los módulos
    module_styles = [
        {
            "card_class": "scheme-purple",
            "icon_class": "bi bi-calculator-fill"  # Ejemplo para Matemáticas
        },
        {
            "card_class": "scheme-teal",
            "icon_class": "bi bi-book-fill"  # Ejemplo para Lectura
        },
        {
            "card_class": "scheme-amber",
            "icon_class": "bi bi-translate"  # Ejemplo para Inglés
        },
        {
            "card_class": "scheme-purple", # Se repiten si hay más módulos que esquemas
            "icon_class": "bi bi-compass-fill" # Ejemplo para Sociales
        },
        {
            "card_class": "scheme-teal",
            "icon_class": "bi bi-radioactive" # Ejemplo para Ciencias Naturales
        }
    ]

    examenes_con_estilos = []
    for i, examen in enumerate(examenes):
        estilo_aplicado = module_styles[i % len(module_styles)]
        if "matem" in examen.tipo.lower():
            estilo_aplicado["icon_class"] = "bi bi-calculator-fill"
        elif "lectura" in examen.tipo.lower() or "lenguaje" in examen.tipo.lower():
            estilo_aplicado["icon_class"] = "bi bi-book-fill"
        elif "inglés" in examen.tipo.lower() or "ingles" in examen.tipo.lower():
            estilo_aplicado["icon_class"] = "bi bi-translate"
        elif "sociales" in examen.tipo.lower():
            estilo_aplicado["icon_class"] = "bi bi-compass-fill"
        elif "naturales" in examen.tipo.lower() or "ciencia" in examen.tipo.lower():
            estilo_aplicado["icon_class"] = "bi bi-radioactive"
        examenes_con_estilos.append({
            "examen": examen,
            "estilo": estilo_aplicado
        })

    return render(request, 'profesor/panel_profesor.html', {
        "examenes_con_estilos": examenes_con_estilos,
        "profesor_nombre": request.session.get('profesor_nombre', 'Profesor'),
        "total_modulos_profesor": total_modulos_profesor,
        "total_preguntas_profesor": total_preguntas_profesor,
        "total_realizaciones_profesor": total_realizaciones_profesor
    })

def login_profesor(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contrasena = request.POST.get('contrasena')

        try:
            profesor = Profesor.objects.get(identificacion=usuario)
            # Modificación: Comparación directa de contraseña
            if profesor.contraseña == contrasena:
                request.session['profesor_id'] = profesor.id_profesor
                request.session['profesor_nombre'] = profesor.nombre
                return redirect('base:panel_profesor')
            else:
                messages.error(request, 'Contraseña incorrecta.')
        except Profesor.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')

    return render(request, 'profesor/login.html')

def signup_profesor(request):  # O puedes dejarlo como registro_profesor
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        identificacion = request.POST.get('identificacion')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        area_especializacion = request.POST.get('area_especializacion')
        institucion = request.POST.get('institucion')
        contraseña = request.POST.get('contraseña')
        confirmar = request.POST.get('confirmar')

        if contraseña != confirmar:
            return render(request, 'profesor/signup.html', {
                'error': 'Las contraseñas no coinciden.'
            })

        if Profesor.objects.filter(identificacion=identificacion).exists():
            return render(request, 'profesor/signup.html', {
                'error': 'Ya existe un profesor con esa identificación.'
            })

        profesor = Profesor.objects.create(
            nombre=nombre,
            apellido=apellido,
            identificacion=identificacion,
            correo=correo,
            telefono=telefono,
            direccion=direccion,
            area_especializacion=area_especializacion,
            institucion=institucion,
            # Modificación: Guardar contraseña directamente
            contraseña=contraseña
        )

        # Guardar ID y nombre del profesor en la sesión para la siguiente vista
        request.session['nuevo_profesor_id'] = profesor.id_profesor
        request.session['profesor_nombre'] = profesor.nombre # Para el saludo en la pág de selección
        
        messages.success(request, 'Registro exitoso. Por favor, selecciona tus grados.')
        return redirect('base:seleccionar_grados_profesor')

    return render(request, 'profesor/signup.html')

@require_GET
def seleccionar_grados_profesor_get(request):
    profesor_id = request.session.get('nuevo_profesor_id')
    if not profesor_id:
        messages.error(request, "No se encontró información del profesor. Por favor, regístrate de nuevo.")
        return redirect('base:signup_profesor')
    
    # Limpiar el ID de la sesión si ya se usó para la carga inicial de esta página
    # request.session.pop('nuevo_profesor_id', None) # Comentado para que persista si el usuario recarga

    return render(request, 'profesor/seleccionar_grados.html')

@require_POST
def seleccionar_grados_profesor_post(request):
    profesor_id = request.session.get('nuevo_profesor_id') # Usar el ID de la sesión
    if not profesor_id:
        # Esto no debería pasar si el flujo es correcto, pero como fallback
        messages.error(request, "Error de sesión. Intenta iniciar sesión o regístrate de nuevo.")
        return redirect('base:login_profesor')

    try:
        profesor = Profesor.objects.get(id_profesor=profesor_id)
    except Profesor.DoesNotExist:
        messages.error(request, "Profesor no encontrado. Por favor, regístrate de nuevo.")
        return redirect('base:signup_profesor')

    grados_seleccionados = request.POST.getlist('grados_seleccionados')

    if not grados_seleccionados:
        return render(request, 'profesor/seleccionar_grados.html', {
            'error': 'Debes seleccionar al menos un grado.',
            'profesor_nombre': request.session.get('profesor_nombre', profesor.nombre) # Pasar nombre para el saludo
        })

    grados_a_guardar = ""
    for grado_base in grados_seleccionados:
        if grado_base == "9":
            grados_a_guardar += ",9A,9B,"
        elif grado_base == "10":
            grados_a_guardar += ",10A,10B,"
        elif grado_base == "11":
            grados_a_guardar += ",11A,11B,"
    
    # Eliminar duplicados si el usuario selecciona y deselecciona, y normalizar comas
    grados_finales_lista = sorted(list(set(filter(None, grados_a_guardar.split(',')))))
    profesor.grados = "," + ",".join(grados_finales_lista) + "," if grados_finales_lista else None
        
    profesor.save()

    # Limpiar la información de nuevo profesor de la sesión ya que se completó el paso
    request.session.pop('nuevo_profesor_id', None)
    request.session.pop('profesor_nombre', None)

    # Iniciar sesión para el panel del profesor
    request.session['profesor_id'] = profesor.id_profesor
    request.session['profesor_nombre'] = profesor.nombre

    messages.success(request, 'Grados guardados exitosamente. ¡Bienvenido!')
    return redirect('base:panel_profesor')

# Unificar la vista para manejar GET y POST
def seleccionar_grados_profesor(request):
    if request.method == 'POST':
        return seleccionar_grados_profesor_post(request)
    else:
        return seleccionar_grados_profesor_get(request)

def agregar_modulo(request):
    profesor_id = request.session.get('profesor_id')

    if not profesor_id:
        return redirect('base:login_profesor')  # Protege si no hay sesión

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        duracion = request.POST.get('duracion')
        ubicacion = request.POST.get('ubicacion')
        estado = request.POST.get('estado')

        profesor = Profesor.objects.get(id_profesor=profesor_id)
        Examen.objects.create(
            tipo=tipo,
            duracion=duracion,
            ubicacion=ubicacion,
            estado=estado,
            profesor=profesor
        )

        messages.success(request, 'Examen creado exitosamente.')
        return redirect('base:panel_profesor')

    return render(request, 'profesor/agregar_modulo.html')

def editar_modulo(request, examen_id):
    examen = get_object_or_404(Examen, id_examen=examen_id)

    if request.method == 'POST':
        examen.tipo = request.POST.get('tipo')
        examen.duracion = request.POST.get('duracion')
        examen.ubicacion = request.POST.get('ubicacion')
        examen.estado = request.POST.get('estado')
        examen.save()
        return redirect('base:panel_profesor')

    estados = ['Activo', 'Pendiente', 'Realizado', 'Cancelado']
    return render(request, 'profesor/editar_modulo.html', {
        'examen': examen,
        'estados': estados
    })
    
def examenes_profesores(request):
    estudiante_id = request.session.get("estudiante_id")
    if not estudiante_id:
        return redirect("base:login_estudiante")

    estudiante = get_object_or_404(Estudiante, id_estudiante=estudiante_id)
    grado = estudiante.grado

    # Mostrar solo los exámenes activos de profesores que enseñan a su grado
    examenes = Examen.objects.filter(
    estado="Activo",
    profesor__grados__icontains=f",{grado},"
)

    return render(request, "simulacros/inicio.html", {
        "examenes": examenes,
    })

def logout_estudiante(request):
    request.session.flush()  # Borra toda la sesión
    return redirect('base:inicio')

def inicio(request):
    return render(request, 'inicio.html')

def eliminar_resultado_historial(request, resultado_id):
    if request.method == 'POST':
        estudiante_id = request.session.get('estudiante_id')
        if not estudiante_id:
            messages.error(request, 'Debes iniciar sesión para realizar esta acción.')
            return redirect('base:login_estudiante')

        resultado = get_object_or_404(Resultado, id_resultado=resultado_id)
        
        # Verificar que el resultado pertenece al estudiante logueado
        if resultado.estudiante.id_estudiante == estudiante_id:
            resultado.delete()
            messages.success(request, 'El resultado del simulacro ha sido eliminado exitosamente.')
        else:
            messages.error(request, 'No tienes permiso para eliminar este resultado.')
    else:
        messages.error(request, 'Método no permitido.')
    
    return redirect('base:estudiante_home')

def ver_preguntas_modulo(request, examen_id):
    examen = get_object_or_404(Examen, id_examen=examen_id)
    # Verificar que el examen pertenece al profesor en sesión (si aplica esta lógica de seguridad)
    # profesor_id = request.session.get('profesor_id')
    # if not profesor_id or examen.profesor_id != profesor_id:
    #     messages.error(request, "No tienes permiso para ver estas preguntas.")
    #     return redirect('base:panel_profesor')

    preguntas = Pregunta.objects.filter(examen=examen).order_by('id_pregunta')
    
    # Para el modal, necesitamos pasar las respuestas posibles como JSON
    for preg in preguntas:
        preg.respuestas_posibles_json = json.dumps(preg.respuestas_posibles)

    return render(request, 'profesor/ver_preguntas_modulo.html', {
        'examen': examen,
        'preguntas': preguntas
    })

@require_POST
def eliminar_pregunta_de_modulo(request, examen_id, pregunta_id):
    pregunta = get_object_or_404(Pregunta, id_pregunta=pregunta_id, examen_id=examen_id)
    # Aquí también podrías añadir una verificación de que el examen pertenece al profesor en sesión.
    
    pregunta.delete()
    messages.success(request, 'Pregunta eliminada exitosamente del módulo.')
    return redirect('base:ver_preguntas_modulo', examen_id=examen_id)

def editar_pregunta_de_modulo(request, examen_id, pregunta_id):
    examen = get_object_or_404(Examen, id_examen=examen_id)
    pregunta = get_object_or_404(Pregunta, id_pregunta=pregunta_id, examen=examen)
    # profesor_id = request.session.get('profesor_id')
    # if not profesor_id or examen.profesor_id != profesor_id:
    #     messages.error(request, "No tienes permiso para editar esta pregunta.")
    #     return redirect('base:panel_profesor')

    if request.method == 'POST':
        enunciado = request.POST.get('enunciado_modal')
        tipo_pregunta = request.POST.get('tipo_pregunta_modal')
        respuestas_posibles_list = request.POST.getlist('respuestas_modal')
        respuesta_correcta_seleccionada_modal = request.POST.get('respuesta_correcta_selector_modal')

        if not enunciado or not tipo_pregunta or not respuesta_correcta_seleccionada_modal or not respuestas_posibles_list:
            messages.error(request, 'Todos los campos son obligatorios en el formulario de edición.')
            # No podemos simplemente renderizar el modal de nuevo fácilmente sin recargar la página principal
            # o usar AJAX. Por ahora, redirigimos a la vista de preguntas.
            return redirect('base:ver_preguntas_modulo', examen_id=examen_id)
        
        respuesta_correcta_final_modal = ''
        if tipo_pregunta == "Opción Múltiple":
            try:
                indice_correcto_modal = int(respuesta_correcta_seleccionada_modal)
                if 0 <= indice_correcto_modal < len(respuestas_posibles_list):
                    # Para Opción Múltiple, guardamos el ÍNDICE como string.
                    respuesta_correcta_final_modal = str(indice_correcto_modal)
                else:
                    messages.error(request, 'El índice de la respuesta correcta (modal) no es válido.')
                    return redirect('base:ver_preguntas_modulo', examen_id=examen_id)
            except ValueError:
                messages.error(request, 'El valor de la respuesta correcta para opción múltiple (modal) debe ser un índice numérico.')
                return redirect('base:ver_preguntas_modulo', examen_id=examen_id)
        elif tipo_pregunta == "Verdadero/Falso":
            respuesta_correcta_final_modal = respuesta_correcta_seleccionada_modal
        else:
            messages.error(request, 'Tipo de pregunta no soportado (modal).')
            return redirect('base:ver_preguntas_modulo', examen_id=examen_id)
        
        # Validación para V/F
        if tipo_pregunta == "Verdadero/Falso" and respuesta_correcta_final_modal not in ["Verdadero", "Falso"]:
            messages.error(request, 'Respuesta inválida para pregunta de Verdadero/Falso (modal).')
            return redirect('base:ver_preguntas_modulo', examen_id=examen_id)

        pregunta.enunciado = enunciado
        pregunta.tipo_pregunta = tipo_pregunta
        pregunta.respuestas_posibles = {str(i): r for i, r in enumerate(respuestas_posibles_list)}
        pregunta.respuesta_correcta = respuesta_correcta_final_modal
        pregunta.save()

        messages.success(request, 'Pregunta actualizada exitosamente.')
        return redirect('base:ver_preguntas_modulo', examen_id=examen_id)
    else:
        # El modal se maneja en el frontend, así que un GET a esta URL
        # podría simplemente redirigir o mostrar un error si no se espera.
        # Por ahora, simplemente redirigimos si no es POST.
        return redirect('base:ver_preguntas_modulo', examen_id=examen_id)

@require_POST
def eliminar_modulo_completo(request, examen_id):
    profesor_id = request.session.get('profesor_id')
    examen = get_object_or_404(Examen, id_examen=examen_id)

    # Verificación de propiedad (¡Importante!)
    if not profesor_id or examen.profesor_id != profesor_id:
        messages.error(request, "No tienes permiso para eliminar este módulo.")
        return redirect('base:panel_profesor')

    # La eliminación del examen debería, por la configuración del modelo (on_delete=models.CASCADE en Pregunta.examen),
    # eliminar también todas las preguntas asociadas.
    nombre_examen = examen.tipo # Guardar para el mensaje
    examen.delete()
    messages.success(request, f'El módulo "{nombre_examen}" y todas sus preguntas han sido eliminados exitosamente.')
    return redirect('base:panel_profesor')

def ver_resultados_estudiantes_profesor(request):
    profesor_id = request.session.get('profesor_id')
    if not profesor_id:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('base:login_profesor')

    profesor = get_object_or_404(Profesor, id_profesor=profesor_id)
    
    # Obtener todos los exámenes creados por este profesor
    examenes_del_profesor = Examen.objects.filter(profesor=profesor)
    
    # Obtener todos los resultados de esos exámenes, seleccionando campos relacionados para eficiencia
    resultados_query = Resultado.objects.filter(examen__in=examenes_del_profesor).select_related('estudiante', 'examen').order_by('-fecha_resultado')

    # Mapeo del tipo de examen al campo del modelo Resultado (similar al de estudiante_home)
    tipo_materia_map = {
        "Lectura Critica": "lectura_critica",
        "Matematicas": "matematicas",
        "Ciencias Naturales": "ciencias_naturales",
        "Ciencias Sociales": "sociales_ciudadanas",
        "Ingles": "ingles",
        # Añade otros mapeos si tus tipos de examen son diferentes o más variados
    }

    for resultado in resultados_query:
        if resultado.examen:
            resultado.total_preguntas_examen = resultado.examen.pregunta_set.count()
            
            # 'puntaje_obtenido_en_examen' es el porcentaje de aciertos (0-100) almacenado en puntaje_global
            puntaje_obtenido_en_examen = resultado.puntaje_global # Leer directamente de puntaje_global
            
            if resultado.total_preguntas_examen > 0 and puntaje_obtenido_en_examen is not None:
                resultado.correctas_reales = round((puntaje_obtenido_en_examen / 100) * resultado.total_preguntas_examen)
                resultado.incorrectas_reales = resultado.total_preguntas_examen - resultado.correctas_reales
            else:
                resultado.correctas_reales = 0
                # Si no hay puntaje o no hay preguntas, las incorrectas pueden ser 0 o el total de preguntas
                if resultado.total_preguntas_examen == 0:
                    resultado.incorrectas_reales = 0
                elif puntaje_obtenido_en_examen is None: # Hay preguntas pero no puntaje
                    resultado.incorrectas_reales = resultado.total_preguntas_examen
                else: # Hay preguntas y puntaje es 0
                    resultado.incorrectas_reales = resultado.total_preguntas_examen
        else:
            resultado.total_preguntas_examen = 0
            resultado.correctas_reales = 0
            resultado.incorrectas_reales = 0

    # Estadísticas adicionales
    total_resultados_visibles = resultados_query.count()
    
    promedio_correctas_general = 0
    if total_resultados_visibles > 0:
        suma_correctas = sum(r.correctas_reales for r in resultados_query if hasattr(r, 'correctas_reales') and r.correctas_reales is not None)
        promedio_correctas_general = round(suma_correctas / total_resultados_visibles, 2) if total_resultados_visibles > 0 else 0

    # Examen más popular (más veces realizado)
    examen_mas_popular_info = None
    if total_resultados_visibles > 0:
        examenes_realizados_ids = [r.examen.id_examen for r in resultados_query if r.examen]
        if examenes_realizados_ids:
            mas_comun_id = max(set(examenes_realizados_ids), key=examenes_realizados_ids.count)
            examen_obj = Examen.objects.get(id_examen=mas_comun_id)
            examen_mas_popular_info = {
                'nombre': examen_obj.tipo,
                'veces': examenes_realizados_ids.count(mas_comun_id)
            }

    contexto = {
        'resultados': resultados_query, # Cambiado a resultados_query para claridad
        'profesor_nombre': request.session.get('profesor_nombre', 'Profesor'),
        'total_resultados_visibles': total_resultados_visibles,
        'promedio_correctas_general': promedio_correctas_general,
        'examen_mas_popular_info': examen_mas_popular_info,
    }
    return render(request, 'profesor/ver_resultados_estudiantes.html', contexto)

@require_POST
def eliminar_resultado_profesor(request, resultado_id):
    profesor_id = request.session.get('profesor_id')
    if not profesor_id:
        messages.error(request, "Debes iniciar sesión para realizar esta acción.")
        return redirect('base:login_profesor')

    resultado = get_object_or_404(Resultado, id_resultado=resultado_id)
    profesor_actual = get_object_or_404(Profesor, id_profesor=profesor_id)

    # Verificar que el examen al que pertenece el resultado fue creado por el profesor actual
    if resultado.examen.profesor == profesor_actual:
        resultado.delete()
        messages.success(request, 'El resultado del estudiante ha sido eliminado exitosamente.')
    else:
        messages.error(request, 'No tienes permiso para eliminar este resultado.')
    
    return redirect('base:ver_resultados_estudiantes_profesor')

def editar_perfil_profesor(request):
    profesor_id = request.session.get('profesor_id')
    if not profesor_id:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('base:login_profesor')

    profesor = get_object_or_404(Profesor, id_profesor=profesor_id)

    if request.method == 'POST':
        form = ProfesorForm(request.POST, instance=profesor)
        # La identificación y los grados no deben ser editables desde este formulario directamente.
        # El formulario ProfesorForm ya debería excluir 'contraseña' y 'grados' si se desea.
        # Si el ProfesorForm incluye campos que no deberían ser editados aquí (ej. contraseña),
        # es mejor crear un form específico para el perfil.
        # Por ahora, asumimos que ProfesorForm es adecuado, pero sin cambiar identificacion.
        
        # Creamos una copia de los datos del POST para poder modificarla
        post_data = request.POST.copy()
        post_data['identificacion'] = profesor.identificacion # Asegurar que la identificación no cambie
        form = ProfesorForm(post_data, instance=profesor)

        if form.is_valid():
            # Actualizar solo los campos permitidos
            profesor_actualizado = form.save(commit=False)
            profesor_actualizado.nombre = form.cleaned_data['nombre']
            profesor_actualizado.apellido = form.cleaned_data['apellido']
            profesor_actualizado.correo = form.cleaned_data['correo']
            profesor_actualizado.telefono = form.cleaned_data['telefono']
            profesor_actualizado.direccion = form.cleaned_data['direccion']
            profesor_actualizado.area_especializacion = form.cleaned_data['area_especializacion']
            profesor_actualizado.institucion = form.cleaned_data['institucion']
            # No actualizamos profesor.identificacion ni profesor.grados ni contraseña aquí.
            profesor_actualizado.save()
            
            # Actualizar el nombre en la sesión si cambió
            request.session['profesor_nombre'] = profesor_actualizado.nombre
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('base:editar_perfil_profesor') # Redirigir a la misma página para ver los cambios
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ProfesorForm(instance=profesor)

    return render(request, 'profesor/editar_perfil_profesor.html', {
        'form': form,
        'profesor': profesor # Pasar el objeto profesor para mostrar datos no editables si es necesario
    })

def logout_profesor(request):
    # Eliminar las claves de sesión específicas del profesor
    if 'profesor_id' in request.session:
        del request.session['profesor_id']
    if 'profesor_nombre' in request.session:
        del request.session['profesor_nombre']
    # También podrías usar request.session.flush() si quieres limpiar TODA la sesión,
    # pero esto podría afectar a otros usuarios si comparten sesión (poco común en Django estándar).
    # Es más seguro eliminar solo las claves relevantes.
    
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('base:login_profesor') # Redirigir a la página de login de profesor

# --- Vistas de Administrador ---

def signup_administrador(request):
    if request.method == 'POST':
        form = AdministradorSignupForm(request.POST)
        if form.is_valid():
            admin = form.save(commit=False)
            # Modificación: Guardar contraseña directamente
            admin.contraseña = form.cleaned_data['contraseña'] 
            admin.save()
            messages.success(request, '¡Cuenta de administrador creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('base:login_administrador')
        else:
            # Los errores específicos de los campos se mostrarán por el widget del formulario
            # Aquí podemos agregar mensajes generales si es necesario, o simplemente dejar que la plantilla los muestre
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AdministradorSignupForm()
    return render(request, 'administrador/signup_admin.html', {'form': form})

def login_administrador(request):
    if request.method == 'POST':
        form = AdministradorLoginForm(request.POST)
        if form.is_valid():
            identificacion = form.cleaned_data['identificacion']
            contraseña = form.cleaned_data['contraseña']
            try:
                admin = Administrador.objects.get(identificacion=identificacion)
                # Modificación: Comparación directa de contraseña
                if admin.contraseña == contraseña:
                    request.session['administrador_id'] = admin.id_administrador
                    request.session['administrador_nombre'] = admin.nombre
                    messages.success(request, f'¡Bienvenido de nuevo, {admin.nombre}!') 
                    return redirect('base:home') # Cambiado: Redirigir a la vista home (CRUD principal)
                else:
                    messages.error(request, 'La identificación o contraseña son incorrectas.')
            except Administrador.DoesNotExist:
                messages.error(request, 'La identificación o contraseña son incorrectas.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AdministradorLoginForm()
    return render(request, 'administrador/login_admin.html', {'form': form})


def logout_administrador(request):
    if 'administrador_id' in request.session:
        del request.session['administrador_id']
    if 'administrador_nombre' in request.session:
        del request.session['administrador_nombre']
    messages.success(request, "Has cerrado sesión como administrador exitosamente.")
    return redirect('base:login_administrador')

# Placeholder para el panel de administrador
def panel_administrador(request):
    administrador_id = request.session.get('administrador_id')
    if not administrador_id:
        messages.error(request, "Debes iniciar sesión como administrador para acceder a esta página.")
        return redirect('base:login_administrador')
    
    admin = get_object_or_404(Administrador, id_administrador=administrador_id)
    # Aquí puedes agregar la lógica para mostrar información en el panel de admin
    return render(request, 'administrador/panel_administrador.html', {'admin': admin})

def admin_agregar_pregunta(request):
    administrador_id = request.session.get('administrador_id')
    if not administrador_id:
        messages.error(request, "Debes iniciar sesión como administrador para acceder a esta página.")
        return redirect('base:login_administrador')

    if request.method == 'POST':
        examen_id = request.POST.get('examen')
        enunciado = request.POST.get('enunciado')
        tipo_pregunta = request.POST.get('tipo_pregunta')

        # Para repoblar el formulario en caso de error, pasamos los datos de nuevo
        form_data_dict = dict(request.POST.lists() if hasattr(request.POST, 'lists') else request.POST.items())

        if not all([examen_id, enunciado, tipo_pregunta]):
            messages.error(request, 'Todos los campos (Examen, Enunciado, Tipo de pregunta) son obligatorios.')
            examenes_admin = Examen.objects.all() # Necesario para repoblar el select de exámenes
            context = {
                'examenes': examenes_admin,
                'form_data': request.POST, # Pasar el request.POST para repoblar
                'form_data_json': json.dumps(form_data_dict) # Y el JSON para el script
            }
            return render(request, 'agregar_pregunta.html', context)
        
        try:
            examen_seleccionado = Examen.objects.get(id_examen=examen_id)
        except Examen.DoesNotExist:
            messages.error(request, 'El examen seleccionado no es válido.')
            examenes_admin = Examen.objects.all()
            context = {
                'examenes': examenes_admin,
                'form_data': request.POST,
                'form_data_json': json.dumps(form_data_dict)
            }
            return render(request, 'agregar_pregunta.html', context)

        respuestas_posibles_dict = {}
        respuesta_correcta_valor = None

        if tipo_pregunta == 'Opción Múltiple':
            opciones_texto = request.POST.getlist('opcion_texto') # Lista de textos de las opciones
            respuesta_correcta_indice_str = request.POST.get('respuesta_correcta_om_indice') # '0', '1', '2', etc.

            # Validación mínima para opciones múltiples
            if len(opciones_texto) < 2: # Necesita al menos 2 opciones
                messages.error(request, 'Debe haber al menos 2 opciones para una pregunta de opción múltiple.')
                examenes_admin = Examen.objects.all()
                context = {'examenes': examenes_admin, 'form_data': request.POST, 'form_data_json': json.dumps(form_data_dict)}
                return render(request, 'agregar_pregunta.html', context)
            
            if not respuesta_correcta_indice_str: # Debe seleccionar una correcta
                messages.error(request, 'Debes seleccionar una respuesta correcta para opción múltiple.')
                examenes_admin = Examen.objects.all()
                context = {'examenes': examenes_admin, 'form_data': request.POST, 'form_data_json': json.dumps(form_data_dict)}
                return render(request, 'agregar_pregunta.html', context)

            for i, texto_opcion in enumerate(opciones_texto):
                if not texto_opcion.strip(): # Opción no puede estar vacía
                    messages.error(request, f'El texto de la opción {i+1} no puede estar vacío.')
                    examenes_admin = Examen.objects.all()
                    context = {'examenes': examenes_admin, 'form_data': request.POST, 'form_data_json': json.dumps(form_data_dict)}
                    return render(request, 'agregar_pregunta.html', context)
                respuestas_posibles_dict[str(i)] = texto_opcion.strip()
            
            respuesta_correcta_valor = respuesta_correcta_indice_str # Guardamos el índice como string

        elif tipo_pregunta == 'Verdadero/Falso':
            respuesta_correcta_vf = request.POST.get('respuesta_correcta_vf') # "Verdadero" o "Falso"
            if not respuesta_correcta_vf:
                messages.error(request, 'Debes seleccionar Verdadero o Falso como respuesta correcta.')
                examenes_admin = Examen.objects.all()
                context = {'examenes': examenes_admin, 'form_data': request.POST, 'form_data_json': json.dumps(form_data_dict)}
                return render(request, 'agregar_pregunta.html', context)
            
            respuestas_posibles_dict = {"0": "Verdadero", "1": "Falso"}
            respuesta_correcta_valor = respuesta_correcta_vf # Guardamos "Verdadero" o "Falso"
        
        else: # Tipo de pregunta no soportado
            messages.error(request, 'Tipo de pregunta no válido.')
            examenes_admin = Examen.objects.all()
            context = {'examenes': examenes_admin, 'form_data': request.POST, 'form_data_json': json.dumps(form_data_dict)}
            return render(request, 'agregar_pregunta.html', context)

        if respuesta_correcta_valor is not None:
            Pregunta.objects.create(
                examen=examen_seleccionado,
                enunciado=enunciado,
                tipo_pregunta=tipo_pregunta,
                respuestas_posibles=respuestas_posibles_dict,
                respuesta_correcta=respuesta_correcta_valor
            )
            messages.success(request, 'Pregunta agregada exitosamente.')
            return redirect('base:listar_preguntas')
        else:
            messages.error(request, 'No se pudo determinar la respuesta correcta.')
            examenes_admin = Examen.objects.all()
            context = {'examenes': examenes_admin, 'form_data': request.POST, 'form_data_json': json.dumps(form_data_dict)}
            return render(request, 'agregar_pregunta.html', context)

    else:  # GET request
        examenes_admin = Examen.objects.all()
        context = {
            'examenes': examenes_admin,
            'form_data': {}, 
            'form_data_json': json.dumps({})
        }
        if not examenes_admin.exists():
            messages.warning(request, 'No hay exámenes disponibles para agregar preguntas. Por favor, crea un examen primero.')
        return render(request, 'agregar_pregunta.html', context)