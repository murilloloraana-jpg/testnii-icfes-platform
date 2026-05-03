from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),  # ahora esta vista se llama 'chat' dentro del namespace 'chat'
]
