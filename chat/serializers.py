from rest_framework import serializers
from .models import Room, Message
from users.serializers import FriendUserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender = FriendUserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'text', 'attachment', 'audio', 'created_at']
        read_only_fields = ['sender', 'room']

class RoomSerializer(serializers.ModelSerializer):
    participants = FriendUserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'name', 'is_group', 'participants', 'created_at', 'last_message']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
