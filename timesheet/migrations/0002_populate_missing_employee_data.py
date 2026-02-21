from django.db import migrations, transaction
from django.utils import timezone

def populate_employee_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Employee = apps.get_model('timesheet', 'Employee')

    with transaction.atomic():
        # 1. Create missing Employee profiles for existing Users
        for user in User.objects.all():
            if not Employee.objects.filter(user=user).exists():
                # We can't use .save() because it's a historical model, but we can set fields
                Employee.objects.create(
                    user=user,
                    employee_id=f"TEMP-ID-{user.id}" # Temporary ID to satisfy uniqueness
                )

        # 2. Populate employee_code for all Employees
        # We process them in order to ensure sequential codes
        for employee in Employee.objects.filter(employee_code__isnull=True).order_by('id'):
            year = timezone.now().year
            prefix = f"EMP-{year}-"

            # Find the highest number for this year so far in the migration
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

            new_code = f"{prefix}{new_num:04d}"
            employee.employee_code = new_code
            employee.employee_id = new_code # Sync employee_id with the new code
            employee.save()

class Migration(migrations.Migration):

    dependencies = [
        ('timesheet', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'), # Ensure Auth is ready
    ]

    operations = [
        migrations.RunPython(populate_employee_data),
    ]
