"""
F6: 实时语音指导 WebSocket Consumer
规则: Global cooldown >= 5-10s, Same-type cooldown >= 15-30s
优先级: Safety > Process > Correction > Encouragement
"""
import time
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class VoiceCoachingConsumer(AsyncJsonWebsocketConsumer):
    PRIORITY_ORDER = {'safety': 0, 'process': 1, 'correction': 2, 'encouragement': 3}

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'voice_coaching_{self.session_id}'
        self.last_event_time = 0
        self.last_type_times = {}

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        """接收客户端实时 IMU 数据，分析是否触发语音事件"""
        event_type = content.get('event_type', '')
        priority = content.get('priority', 'encouragement')
        message = content.get('message', '')
        now = time.time()

        if not self._should_play(event_type, now):
            return

        event = {
            'type': 'voice_event', 'event_type': event_type,
            'priority': priority, 'message': message,
        }
        await self.channel_layer.group_send(self.group_name, event)
        self.last_event_time = now
        self.last_type_times[event_type] = now

    async def voice_event(self, event):
        await self.send_json({
            'event_type': event['event_type'],
            'priority': event['priority'],
            'message': event['message'],
        })

    def _should_play(self, event_type: str, now: float) -> bool:
        if now - self.last_event_time < 5:
            return False
        if event_type in self.last_type_times:
            if now - self.last_type_times[event_type] < 15:
                return False
        return True
