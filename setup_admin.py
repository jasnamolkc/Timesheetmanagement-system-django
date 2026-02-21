import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timesheet_system.settings')
django.setup()

from django.contrib.auth.models import User
from timesheet.models import Employee

def setup_data():
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'password123')
        admin.first_name = 'System'
        admin.last_name = 'Admin'
        admin.save()

        # Signal will create Employee, but let's make it admin
        emp = admin.employee
        emp.role = 'admin'
        emp.department = 'IT'
        emp.designation = 'Administrator'
        emp.save()
        print(f"Admin created: {emp.employee_code}")

if __name__ == '__main__':
    setup_data()
