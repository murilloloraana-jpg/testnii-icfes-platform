from django.db import models
from django.utils import timezone

# Tabla de Estudiantes
class Estudiante(models.Model):
    id_estudiante = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default="Desconocido")
    apellido = models.CharField(max_length=100, default="Desconocido")
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.CharField(
        max_length=10,
        choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
        default='O'
    )
    identificacion = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(default="", blank=True, null=True)
    institucion = models.CharField(max_length=200, default="", blank=True, null=True)
    tipo_institucion = models.CharField(
        max_length=20,
        choices=[('Pública', 'Pública'), ('Privada', 'Privada')],
        default='Pública'
    )
    grado = models.CharField(max_length=20, default="", blank=True, null=True)
    fecha_inscripcion = models.DateTimeField(default=timezone.now)
    contraseña = models.CharField(max_length=128, default="")

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
class Profesor(models.Model):
    id_profesor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default="Desconocido")
    apellido = models.CharField(max_length=100, default="Desconocido")
    identificacion = models.CharField(max_length=20, unique=True)  # Usado como 'usuario'
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(default="", blank=True, null=True)
    area_especializacion = models.CharField(max_length=200, default="", blank=True, null=True)
    institucion = models.CharField(max_length=200, default="", blank=True, null=True)
    contraseña = models.CharField(max_length=128, default="1234")  # ⚠️ Puedes luego usar make_password()
    grados = models.CharField(max_length=100, blank=True, null=True, help_text="Grados que enseña, formato: ,9A,9B,10A,")
    estado = models.CharField(
        max_length=10,
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        default='Activo'
    )
    

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
# Tabla de Exámenes
class Examen(models.Model):
    id_examen = models.AutoField(primary_key=True)
    fecha_examen = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=50, default="General")
    duracion = models.IntegerField(default=2)
    ubicacion = models.CharField(max_length=255, default="", blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=[('Activo', 'Activo'), ('Pendiente', 'Pendiente'), ('Realizado', 'Realizado'), ('Cancelado', 'Cancelado')],
        default='Pendiente'
    )
    
    profesor = models.ForeignKey(
        'Profesor',
        on_delete=models.CASCADE,
        related_name='examenes',
        null=True,  # Esto es clave para que no afecte los exámenes existentes
        blank=True
    )

    def __str__(self):
        return f"{self.tipo} - {self.fecha_examen}"
# Tabla de Resultados
class Resultado(models.Model):
    id_resultado = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    puntaje_global = models.IntegerField(default=0)
    lectura_critica = models.IntegerField(default=0)
    matematicas = models.IntegerField(default=0)
    sociales_ciudadanas = models.IntegerField(default=0)
    ciencias_naturales = models.IntegerField(default=0)
    ingles = models.IntegerField(default=0)
    fecha_resultado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resultado {self.id_resultado} - {self.estudiante}"

# Tabla de Materias
class Materia(models.Model):
    id_materia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default="General")
    area = models.CharField(max_length=100, default="", blank=True, null=True)

    def __str__(self):
        return self.nombre

# Tabla de Preguntas
class Pregunta(models.Model):
    id_pregunta = models.AutoField(primary_key=True)
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    enunciado = models.TextField()
    tipo_pregunta = models.CharField(
        max_length=50,
        choices=[('Opción Múltiple', 'Opción Múltiple'), ('Verdadero/Falso', 'Verdadero/Falso')],
        default='Opción Múltiple'
    )
    respuestas_posibles = models.JSONField(default=dict)  # ✅ Evita errores con valores predeterminados
    respuesta_correcta = models.CharField(max_length=255)

    def __str__(self):
        return self.enunciado

# Tabla de Respuestas de Estudiantes
class RespuestaEstudiante(models.Model):
    id_respuesta = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    respuesta_seleccionada = models.CharField(max_length=255)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta {self.id_respuesta} - {self.estudiante}"

# Tabla de Profesores

# Tabla de Administradores
class Administrador(models.Model):
    id_administrador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default="Admin")
    apellido = models.CharField(max_length=100, default="Sistema")
    identificacion = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    rol = models.CharField(max_length=50, default="Administrador")
    contraseña = models.CharField(max_length=255, default="")  
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
