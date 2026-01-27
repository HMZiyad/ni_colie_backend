import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from chat.models import Room, Message

User = get_user_model()

def verify():
    print("--- Starting Chat HTTP Verification ---")
    
    # 1. Setup Users
    user1, _ = User.objects.get_or_create(username='user1', email='user1@example.com', defaults={'password': 'password123'})
    user2, _ = User.objects.get_or_create(username='user2', email='user2@example.com', defaults={'password': 'password123'})
    user1.set_password('password123'); user1.save()
    user2.set_password('password123'); user2.save()

    # 2. Get Token
    token = str(RefreshToken.for_user(user1).access_token)
    headers = {'Authorization': f'Bearer {token}'}
    print(f"Got token for {user1.username}")

    # 3. Create/Get Private Room
    # Using Django ORM directly to simulate backend state first, then testing API? 
    # Or just use `requests` to localhost? 
    # Since server might not be running, I should use Django Test Client or just ORM verification?
    # The user asked for "Module Implementation", so running a script against live server is best but I don't control the server run loop easily.
    # I will use Django Test Client to verify API without running server.
    
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=user1)

    print("Testing Get/Create Private Room...")
    response = client.post(f'/api/v1/chat/rooms/private/{user2.id}/')
    if response.status_code in [200, 201]:
        print(f"SUCCESS: Room created/retrieved. ID: {response.data['id']}")
        room_id = response.data['id']
    else:
        print(f"FAIL: {response.status_code} - {response.data}")
        return

    # 4. Send Message (HTTP)
    print("Testing Send Message (HTTP)...")
    data = {'room_id': room_id, 'text': 'Hello from HTTP'}
    response = client.post('/api/v1/chat/messages/', data)
    if response.status_code == 201:
        print("SUCCESS: Message sent.")
    else:
        print(f"FAIL: {response.status_code} - {response.data}")

    # 5. List Messages
    print("Testing List Messages...")
    response = client.get(f'/api/v1/chat/messages/?room_id={room_id}')
    if response.status_code == 200:
        print(f"SUCCESS: Retrieved {len(response.data)} messages.")
    else:
        print(f"FAIL: {response.status_code} - {response.data}")

    print("--- Verification Complete ---")

if __name__ == '__main__':
    verify()
