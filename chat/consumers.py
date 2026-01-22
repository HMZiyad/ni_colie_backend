import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Verify User
        user = await self.get_user_from_token()
        if user is None:
            await self.close()
            return

        self.scope['user'] = user

        # Verify Room Participation
        if not await self.is_participant(user, self.room_id):
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json.get('message')
        
        if not message_text:
            return

        user = self.scope['user']
        room_id = self.room_id

        # Save to DB
        message = await self.save_message(user, room_id, message_text)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender': user.username,
                'timestamp': str(message.created_at)
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_user_from_token(self):
        query_string = self.scope['query_string'].decode()
        params = dict(x.split('=') for x in query_string.split('&') if '=' in x)
        token = params.get('token')
        
        if not token:
            return None
        
        try:
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
            return user
        except Exception:
            return None

    @database_sync_to_async
    def is_participant(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            return room.participants.filter(id=user.id).exists()
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, room_id, text):
        room = Room.objects.get(id=room_id)
        return Message.objects.create(sender=user, room=room, text=text)
