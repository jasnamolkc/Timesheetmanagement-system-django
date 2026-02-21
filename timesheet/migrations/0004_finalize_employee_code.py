from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('timesheet', '0003_populate_employee_codes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='employee_code',
            field=models.CharField(editable=False, max_length=20, unique=True),
        ),
    ]
