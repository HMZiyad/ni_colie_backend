
import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

def remove_duplicates():
    # Find emails that are duplicated
    duplicates = User.objects.values('email').annotate(count=Count('email')).filter(count__gt=1)
    
    print(f"Found {duplicates.count()} emails with duplicates.")

    for entry in duplicates:
        email = entry['email']
        users = User.objects.filter(email=email).order_by('date_joined')
        # Keep the last one (most recent) or first one? 
        # Usually keeping the oldest (first joined) is safer, or just delete all but one.
        # Let's keep the first one.
        users_to_delete = users[1:]
        
        count = users_to_delete.count()
        print(f"Deleting {count} duplicate users for email: {email}")
        for user in users_to_delete:
            user.delete()

if __name__ == '__main__':
    remove_duplicates()
