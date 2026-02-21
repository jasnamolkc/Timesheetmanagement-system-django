from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import connection
from .models import Employee

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    if created:
        # Check if the table exists to avoid errors during initial migrations
        if Employee._meta.db_table in connection.introspection.table_names():
            Employee.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_employee_profile(sender, instance, **kwargs):
    if Employee._meta.db_table in connection.introspection.table_names():
        if hasattr(instance, 'employee'):
            instance.employee.save()
