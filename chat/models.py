from django.db import models
from django.conf import settings

class Room(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.name:
            return self.name
        return f"Room {self.id}"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='chat/attachments/', blank=True, null=True)
    audio = models.FileField(upload_to='chat/voice/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} from {self.sender}"
