from rest_framework import viewsets, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RoomSerializer

    def get_queryset(self):
        return Room.objects.filter(participants=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        room = serializer.save(is_group=True)
        room.participants.add(self.request.user)
        # Add other participants from request data if provided
        participant_ids = self.request.data.get('participant_ids', [])
        for pid in participant_ids:
            try:
                user = User.objects.get(id=pid)
                room.participants.add(user)
            except User.DoesNotExist:
                pass

    @action(detail=False, methods=['post'], url_path='private/(?P<user_id>\d+)')
    def get_or_create_private(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)
        
        # Find existing 1-on-1 room
        # We look for rooms with exactly 2 participants where both are present
        rooms = Room.objects.filter(is_group=False, participants=request.user).filter(participants=target_user)
        
        # This simple filter might return rooms with >2 people if logic was loose, but we enforce is_group=False
        # Ideally we should count participants but strict filtering with annotate is safer
        # For MVP:
        for room in rooms:
            if room.participants.count() == 2:
                return Response(RoomSerializer(room).data)
        
        # Create new
        room = Room.objects.create(is_group=False)
        room.participants.add(request.user, target_user)
        return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)

class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        room_id = self.request.query_params.get('room_id')
        if room_id:
            # Check if user is participant
            room = get_object_or_404(Room, id=room_id, participants=self.request.user)
            return Message.objects.filter(room=room).order_by('created_at')
        return Message.objects.none()

    def perform_create(self, serializer):
        room_id = self.request.data.get('room_id')
        room = get_object_or_404(Room, id=room_id, participants=self.request.user)
        serializer.save(sender=self.request.user, room=room)
