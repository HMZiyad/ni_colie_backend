from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message
from .serializers import MessageSerializer

@receiver(post_save, sender=Message)
def broadcast_message(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{instance.room.id}'
        
        # Serialize the message
        # Note: We don't have request context here, so file URLs might be relative
        serializer = MessageSerializer(instance)
        message_data = serializer.data

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'id': message_data['id'],
                'message': message_data['text'],
                'sender': message_data['sender'], # This is a dict from FriendUserSerializer
                'attachment': message_data['attachment'],
                'audio': message_data['audio'],
                'timestamp': message_data['created_at']
            }
        )
