from django.db import migrations, transaction
from django.utils import timezone

def populate_codes(apps, schema_editor):
    Employee = apps.get_model('timesheet', 'Employee')

    with transaction.atomic():
        for employee in Employee.objects.filter(employee_code__isnull=True):
            year = timezone.now().year
            prefix = f"EMP-{year}-"

            # Find last code for the year
            last_employee = Employee.objects.filter(
                employee_code__startswith=prefix
            ).order_by('-employee_code').first()

            if last_employee and last_employee.employee_code:
                try:
                    last_num = int(last_employee.employee_code.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            employee.employee_code = f"{prefix}{new_num:04d}"
            # Also update employee_id if it's generic
            if not employee.employee_id or employee.employee_id.startswith('EMP0'):
                employee.employee_id = employee.employee_code
            employee.save()

class Migration(migrations.Migration):

    dependencies = [
        ('timesheet', '0002_employee_employee_code'),
    ]

    operations = [
        migrations.RunPython(populate_codes),
    ]
