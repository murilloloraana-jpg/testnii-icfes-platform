from django import forms
from .models import Estudiante, Examen, Resultado, Materia, Pregunta, RespuestaEstudiante, Profesor, Administrador

# Formulario para Estudiantes
class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = '__all__'
        widgets = {
            'contraseña': forms.PasswordInput(), # Para ocultar la contraseña
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

# Formulario para Exámenes
class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = '__all__'
        widgets = {
            'fecha_examen': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

# Formulario para Resultados
class ResultadoForm(forms.ModelForm):
    class Meta:
        model = Resultado
        fields = '__all__'

# Formulario para Materias
class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = '__all__'

# Formulario para Preguntas
class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = '__all__'

# Formulario para Respuestas de Estudiantes
class RespuestaEstudianteForm(forms.ModelForm):
    class Meta:
        model = RespuestaEstudiante
        fields = '__all__'

# Formulario para Profesores
class ProfesorForm(forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ['nombre', 'apellido', 'identificacion', 'correo', 'telefono', 'direccion', 'area_especializacion', 'institucion', 'grados'] # Excluir contraseña y estado
        # La contraseña se maneja por separado (ej. cambio de contraseña)
        # Los grados se manejan en la vista seleccionar_grados_profesor
        # El estado se puede manejar internamente o por un superadmin

# Formulario para Administradores
class AdministradorForm(forms.ModelForm):
    class Meta:
        model = Administrador
        fields = '__all__' # Asumiendo que se quieren todos los campos para edición general
        widgets = {
            'contraseña': forms.PasswordInput(render_value=True), # render_value=True para que no se borre al editar
        }

# Formulario para el Login del Administrador
class AdministradorLoginForm(forms.Form):
    identificacion = forms.CharField(label='Identificación (Usuario)', max_length=100, 
                                   widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu identificación'}))
    contraseña = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Tu contraseña'}))

# Formulario para el Signup (Registro) del Administrador
class AdministradorSignupForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crea una contraseña'}))
    confirmar_contraseña = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirma tu contraseña'}))

    class Meta:
        model = Administrador
        fields = ['nombre', 'apellido', 'identificacion', 'correo', 'telefono', 'rol', 'contraseña']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu apellido'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Identificación (será tu usuario)'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@correo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu número de teléfono (opcional)'}),
            'rol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rol (ej: Administrador Principal)'}),
        }

    def clean_confirmar_contraseña(self):
        contraseña = self.cleaned_data.get("contraseña")
        confirmar_contraseña = self.cleaned_data.get("confirmar_contraseña")
        if contraseña and confirmar_contraseña and contraseña != confirmar_contraseña:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return confirmar_contraseña

    def clean_identificacion(self):
        identificacion = self.cleaned_data.get('identificacion')
        if Administrador.objects.filter(identificacion=identificacion).exists():
            raise forms.ValidationError("Ya existe un administrador con esta identificación.")
        return identificacion
        
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo and Administrador.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Ya existe un administrador con este correo electrónico.")
        return correo

