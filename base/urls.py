app_name = "base"
from django.urls import path, include
from . import views
from .views import (
    home, authView, listar_estudiantes, editar_estudiante, agregar_estudiante, eliminar_estudiante,
    listar_examenes, editar_examen, agregar_examen, eliminar_examen,
    listar_resultados, editar_resultado, agregar_resultado, eliminar_resultado,
    listar_materias, editar_materia, agregar_materia, eliminar_materia,
    listar_preguntas, editar_pregunta, agregar_pregunta, eliminar_pregunta,
    listar_profesores, editar_profesor, agregar_profesor, eliminar_profesor,
    listar_administradores, editar_administrador, agregar_administrador, eliminar_administrador,
    estudiante_home,
    admin_agregar_pregunta,
    
)
from chat import views as viewsChat
urlpatterns = [
    path("", home, name="home"),  # Página principal
    # path("signup/", authView, name="authView"),  # Comentada: Usar signups específicos (estudiante, profesor, admin)
    # path("accounts/", include("django.contrib.auth.urls")),  # Comentada: Usar logins/logouts específicos
    
    # Estudiantes
    path("estudiantes/", listar_estudiantes, name="listar_estudiantes"),
    path("estudiantes/editar/<int:pk>/", editar_estudiante, name="editar_estudiante"),
    path("estudiantes/agregar/", agregar_estudiante, name="agregar_estudiante"),
    path("estudiantes/eliminar/<int:pk>/", eliminar_estudiante, name="eliminar_estudiante"),
    
    # Exámenes
    path("examenes/", listar_examenes, name="listar_examenes"),
    path("examenes/editar/<int:pk>/", editar_examen, name="editar_examen"),
    path("examenes/agregar/", agregar_examen, name="agregar_examen"),
    path("examenes/eliminar/<int:pk>/", eliminar_examen, name="eliminar_examen"),
    
    # Resultados
    path("resultados/", listar_resultados, name="listar_resultados"),
    path("resultados/editar/<int:pk>/", editar_resultado, name="editar_resultado"),
    path("resultados/agregar/", agregar_resultado, name="agregar_resultado"),
    path("resultados/eliminar/<int:pk>/", eliminar_resultado, name="eliminar_resultado"),
    
    # Materias
    path("materias/", listar_materias, name="listar_materias"),
    path("materias/editar/<int:pk>/", editar_materia, name="editar_materia"),
    path("materias/agregar/", agregar_materia, name="agregar_materia"),
    path("materias/eliminar/<int:pk>/", eliminar_materia, name="eliminar_materia"),
    
    # Preguntas
    path("preguntas/", listar_preguntas, name="listar_preguntas"),
    path("preguntas/editar/<int:pk>/", editar_pregunta, name="editar_pregunta"),
    path("preguntas/agregar/", agregar_pregunta, name="agregar_pregunta"),
    path("preguntas/eliminar/<int:pk>/", eliminar_pregunta, name="eliminar_pregunta"),
    
    # Profesores
    path("profesores/", listar_profesores, name="listar_profesores"),
    path("profesores/editar/<int:pk>/", editar_profesor, name="editar_profesor"),
    path("profesores/agregar/", agregar_profesor, name="agregar_profesor"),
    path("profesores/eliminar/<int:pk>/", eliminar_profesor, name="eliminar_profesor"),
    
    # Administradores
    path("administradores/", listar_administradores, name="listar_administradores"),
    path("administradores/editar/<int:pk>/", editar_administrador, name="editar_administrador"),
    path("administradores/agregar/", agregar_administrador, name="agregar_administrador"),
    path("administradores/eliminar/<int:pk>/", eliminar_administrador, name="eliminar_administrador"),
    
   path('estudiante/', views.estudiante_home, name='estudiante_home'),
    path('simulacro/<int:examen_id>/<int:pregunta_index>/', views.simulacro, name='simulacro'),
    path('lectura/iniciar/<str:tipo_examen>/', views.iniciar_simulacro, name='iniciar_simulacro'),
    path('resultado/', views.resultado_simulacro, name='resultado_simulacro'),
    path('fin/', views.fin_simulacro, name='fin_simulacro'),
    path('ver-respuestas/', views.ver_respuestas, name='ver_respuestas'),
    path('login/', views.login_estudiante, name='login_estudiante'),
    path('signup_estudiante/', views.signup_estudiante, name='signup_estudiante'),
    path('historial/eliminar/<int:resultado_id>/', views.eliminar_resultado_historial, name='eliminar_resultado_historial'),
    
    path('correcciones/', views.send_corrections, name='send_corrections'),

    path('chat/', include(("chat.urls", "chat"), namespace="chat")),
    path('inicio/', views.inicio, name='inicio'),
    #Chat 
      path('chat/', viewsChat.chat_view, name='chat'),
    
     path('chat/send/', viewsChat.send_message, name='send_message'),
     #profe
     path('loginprofe/', views.login_profesor, name='login_profesor'),
    path('signupprofe/', views.signup_profesor, name='signup_profesor'),
    path('profesor/seleccionar-grados/', views.seleccionar_grados_profesor, name='seleccionar_grados_profesor'),
    path('profesor/perfil/editar/', views.editar_perfil_profesor, name='editar_perfil_profesor'),
    path('profesor/logout/', views.logout_profesor, name='logout_profesor'),
    path('panelprofesor/', views.panel_profesor, name='panel_profesor'),
    path('agregar_modulo/', views.agregar_modulo, name='agregar_modulo'),
    path('modulo/<int:examen_id>/pregunta/nueva/', views.agregar_pregunta, name='agregar_pregunta'),
    path('modulo/<int:examen_id>/editar/', views.editar_modulo, name='editar_modulo'),
    path('modulo/<int:examen_id>/preguntas/', views.ver_preguntas_modulo, name='ver_preguntas_modulo'),
    path('modulo/<int:examen_id>/pregunta/<int:pregunta_id>/editar/', views.editar_pregunta_de_modulo, name='editar_pregunta_de_modulo'),
    path('modulo/<int:examen_id>/pregunta/<int:pregunta_id>/eliminar/', views.eliminar_pregunta_de_modulo, name='eliminar_pregunta_de_modulo'),
    path('modulo/<int:examen_id>/eliminar_completo/', views.eliminar_modulo_completo, name='eliminar_modulo_completo'),
    path('profesor/resultados-estudiantes/', views.ver_resultados_estudiantes_profesor, name='ver_resultados_estudiantes_profesor'),
    path('profesor/resultado/<int:resultado_id>/eliminar/', views.eliminar_resultado_profesor, name='eliminar_resultado_profesor'),
    #examenesprofe
    path("examenes-profesores/", views.examenes_profesores, name="examenes_profesores"),
 #cerrar sesion
    path('logout/', views.logout_estudiante, name='logout_estudiante'),

    # URLs de Administrador
    path('administrador/login/', views.login_administrador, name='login_administrador'),
    path('administrador/signup/', views.signup_administrador, name='signup_administrador'),
    path('administrador/logout/', views.logout_administrador, name='logout_administrador'),
    path('administrador/panel/', views.panel_administrador, name='panel_administrador'),
    path('gestor/preguntas/agregar/', views.admin_agregar_pregunta, name='admin_agregar_pregunta'),
]
