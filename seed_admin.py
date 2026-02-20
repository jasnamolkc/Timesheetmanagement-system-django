import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timesheet_system.settings')
django.setup()

from django.contrib.auth.models import User
from timesheet.models import Employee

def create_admin():
    username = 'admin'
    email = 'admin@example.com'
    password = 'password123'

    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username, email, password)
        user.first_name = 'System'
        user.last_name = 'Admin'
        user.save()

        Employee.objects.create(
            user=user,
            role='ADMIN',
            employee_id='EMP001'
        )
        print(f"Superuser '{username}' created with Employee profile.")
    else:
        print(f"User '{username}' already exists.")

if __name__ == '__main__':
    create_admin()
