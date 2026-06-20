from django.urls import path
from apps.ai_coach.consumers import VoiceCoachingConsumer

websocket_urlpatterns = [
    path('ws/voice-coaching/<uuid:session_id>/', VoiceCoachingConsumer.as_asgi()),
]
