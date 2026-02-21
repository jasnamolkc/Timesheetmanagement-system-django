from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Employee(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    employee_code = models.CharField(max_length=20, unique=True, editable=False)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.employee_code:
            with transaction.atomic():
                year = timezone.now().year
                prefix = f"EMP-{year}-"
                # Use select_for_update to handle concurrency safely
                last_employee = Employee.objects.filter(
                    employee_code__startswith=prefix
                ).select_for_update().order_by('-employee_code').first()

                if last_employee:
                    try:
                        last_num = int(last_employee.employee_code.split('-')[-1])
                        new_num = last_num + 1
                    except (ValueError, IndexError):
                        new_num = 1
                else:
                    new_num = 1

                self.employee_code = f"{prefix}{new_num:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_code})"

class Project(models.Model):
    STATUS_CHOICES = (
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
    )
    name = models.CharField(max_length=200)
    project_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.project_code} - {self.name}"

    @property
    def allocated_employees_count(self):
        return self.allocations.filter(end_date__gte=timezone.now().date()).count()

class ProjectAllocation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='allocations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='allocations')
    allocation_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    role_in_project = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('employee', 'project', 'start_date')

    def clean(self):
        # Prevent allocation > 100%
        # This is a simplified check for overlapping periods
        # In a real system, we'd need more complex logic for any date in the range
        existing_allocations = ProjectAllocation.objects.filter(
            employee=self.employee
        ).exclude(pk=self.pk)

        # Check if total allocation for the period exceeds 100%
        # For simplicity, we check if there's any overlap and sum it up
        # This is basic and could be improved
        total_allocation = self.allocation_percentage
        for alloc in existing_allocations:
            # If date ranges overlap
            if not (self.end_date < alloc.start_date or self.start_date > alloc.end_date):
                total_allocation += alloc.allocation_percentage

        if total_allocation > 100:
            raise ValidationError(f"Total allocation for this employee would exceed 100% (currently {total_allocation}%).")

    def __str__(self):
        return f"{self.employee.user.username} -> {self.project.project_code}"

class TimesheetEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='timesheets')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='timesheets')
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.TextField()
    task_reference = models.CharField(max_length=100, blank=True)
    billable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Prevent logging hours if employee not allocated
        is_allocated = ProjectAllocation.objects.filter(
            employee=self.employee,
            project=self.project,
            start_date__lte=self.date,
            end_date__gte=self.date
        ).exists()

        if not is_allocated:
            raise ValidationError(f"Employee is not allocated to project {self.project.project_code} on {self.date}.")

    def __str__(self):
        return f"{self.employee.user.username} - {self.project.project_code} - {self.date}"
