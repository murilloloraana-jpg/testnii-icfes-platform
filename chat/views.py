from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from google import genai

# API key para Gemini
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

def chat_view(request):
    return render(request, 'chat/chat.html')

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            
            # Crear cliente usando la clase Client
            client = genai.Client(api_key=API_KEY)
            
            try:
                # Generar contenido usando el modelo gemini-pro
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_message+' responde el mensaje corto ',
                    
                )
                
                # Obtener el texto de la respuesta
                if hasattr(response, 'text'):
                    reply = response.text
                    print("Respuesta exitosa de Gemini:", reply[:50] + "..." if len(reply) > 50 else reply)
                else:
                    print("Formato de respuesta inesperado:", response)
                    reply = "Lo siento, no pude generar una respuesta."
                
            except Exception as api_error:
                print(f"Error de la API de Gemini: {api_error}")
                reply = "Lo siento, ocurrió un error al procesar tu mensaje con Gemini."
            
            return JsonResponse({"reply": reply})
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Error al procesar la solicitud JSON"}, status=400)
        except Exception as e:
            print(f"Error inesperado: {e}")
            return JsonResponse({"error": "Error interno del servidor"}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)

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

