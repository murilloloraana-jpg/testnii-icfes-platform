from django.contrib import admin
from .models import Estudiante, Examen, Resultado, Materia, Pregunta, RespuestaEstudiante, Profesor, Administrador

admin.site.register(Estudiante)
admin.site.register(Examen)
admin.site.register(Resultado)
admin.site.register(Materia)
admin.site.register(Pregunta)
admin.site.register(RespuestaEstudiante)
admin.site.register(Profesor)
admin.site.register(Administrador)

# Register your models here.