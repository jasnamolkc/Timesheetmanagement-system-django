from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Employee(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')
    employee_id = models.CharField(max_length=20, unique=True)
    employee_code = models.CharField(max_length=20, unique=True, editable=False)
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    is_active = models.BooleanField(default=True)
    def generate_employee_code(self):
        year = timezone.now().year

        if self.role == 'ADMIN':
            prefix = 'ADM'
        elif self.role == 'MANAGER':
            prefix = 'MGR'
        else:
            prefix = 'EMP'

        last_employee = Employee.objects.filter(
            employee_code__startswith=f"{prefix}-{year}"
        ).order_by('-employee_code').first()

        if last_employee:
            last_number = int(last_employee.employee_code.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{year}-{str(new_number).zfill(3)}"

    def save(self, *args, **kwargs):
        if not self.employee_code:
            self.employee_code = self.generate_employee_code()
        # 🔥 Auto-fill employee_id if empty (compatibility support)
        if not self.employee_id:
            self.employee_id = self.employee_code
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_code})"
    # def save(self, *args, **kwargs):
    #     if not self.employee_code:
    #         with transaction.atomic():
    #             year = timezone.now().year
    #             prefix = f"EMP-{year}-"
    #             # Use select_for_update to handle concurrency safely
    #             last_employee = Employee.objects.filter(
    #                 employee_code__startswith=prefix
    #             ).select_for_update().order_by('-employee_code').first()

    #             if last_employee:
    #                 try:
    #                     last_num = int(last_employee.employee_code.split('-')[-1])
    #                     new_num = last_num + 1
    #                 except (ValueError, IndexError):
    #                     new_num = 1
    #             else:
    #                 new_num = 1

    #             self.employee_code = f"{prefix}{new_num:04d}"

    #             # Also auto-fill employee_id if it's empty to maintain compatibility
    #             if not self.employee_id:
    #                 self.employee_id = self.employee_code

    #     super().save(*args, **kwargs)

    # def __str__(self):
    #     return f"{self.user.get_full_name()} ({self.employee_code})"


from django.db.models import Q, Sum


class Project(models.Model):

    STATUS_CHOICES = (
        ('REQUIREMENT_ANALYSIS', 'Requirement Analysis'),
        ('DEVELOPMENT', 'Development'),
        ('TESTING', 'Testing'),
        ('DEPLOYMENT', 'Deployment'),
        ('COMPLETED', 'Completed'),
    )

    name = models.CharField(max_length=200)

    project_code = models.CharField(
        max_length=50,
        unique=True
    )
    logo = models.ImageField(
        upload_to='project_logos/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='REQUIREMENT_ANALYSIS'
    )

    description = models.TextField(blank=True)

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True
    )

    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date', 'name']

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    "End date cannot be before start date."
                )

    def __str__(self):
        return f"{self.project_code} - {self.name}"

    @property
    def allocated_employees_count(self):
        today = timezone.now().date()

        return self.allocations.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        ).count()
    @property
    def progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status="COMPLETED").count()
        return int((completed / total) * 100)
    @property
    def milestone_progress(self):
        total = self.milestones.count()
        if total == 0:
            return 0
        completed = self.milestones.filter(status="COMPLETED").count()
        return int((completed / total) * 100)

class ProjectAllocation(models.Model):

    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='allocations'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='allocations'
    )

    allocation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    role_in_project = models.CharField(max_length=100)

    start_date = models.DateField()

    end_date = models.DateField()

    class Meta:
        unique_together = ('employee', 'project', 'start_date')
        ordering = ['-start_date']

    def clean(self):

        existing_allocations = ProjectAllocation.objects.filter(
            employee=self.employee
        ).exclude(pk=self.pk)

        total_allocation = self.allocation_percentage or 0

        for alloc in existing_allocations:

            if not (self.end_date < alloc.start_date or self.start_date > alloc.end_date):

                total_allocation += alloc.allocation_percentage or 0

        # if total_allocation > 1000:
        #     raise ValidationError(
        #         f"Total allocation exceeds 1000% (currently {total_allocation}%)."
        #     )
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
    
    def __str__(self):
        return f"{self.employee.user.username} -> {self.project.project_code}"

class Milestone(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones"
    )

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    start_date = models.DateField()

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date"]

    def clean(self):
        if self.due_date < self.start_date:
            raise ValidationError("Milestone due date cannot be before start date.")

    def __str__(self):
        return f"{self.project.project_code} - {self.name}"

    @property
    def progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status="COMPLETED").count()
        return int((completed / total) * 100)

class Task(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    )
    milestone = models.ForeignKey(
        'Milestone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks"
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    due_date = models.DateField(
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks_user"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        if self.milestone and self.milestone.project != self.project:
            raise ValidationError(
                "Milestone must belong to the same project."
            )
        # Optional: Task due date should not exceed milestone due date
        if self.milestone and self.due_date:
            if self.due_date > self.milestone.due_date:
                raise ValidationError(
                    "Task due date cannot be later than milestone due date."
                )
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # 🔹 Update milestone status automatically
        if self.milestone:
            tasks = self.milestone.tasks.all()

            if tasks.filter(status="IN_PROGRESS").exists():
                self.milestone.status = "IN_PROGRESS"

            elif tasks.filter(status="COMPLETED").count() == tasks.count():
                self.milestone.status = "COMPLETED"

            else:
                self.milestone.status = "PENDING"

            self.milestone.save()

    def __str__(self):
        return f"{self.project.project_code} - {self.title}"

class TaskImage(models.Model):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="task_images/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Image for {self.task.title}"
class TimesheetEntry(models.Model):

    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='timesheets'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='timesheets'
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='timesheets',
        null=True,
        blank=True
    )

    date = models.DateField(default=timezone.now)

    hours = models.DecimalField(
        max_digits=4,
        decimal_places=2
    )

    description = models.TextField()

    billable = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):

        # ✅ Skip allocation check for Admin / Manager
        if self.employee.role not in ['ADMIN', 'MANAGER'] and not self.employee.user.is_superuser:
        
            is_allocated = ProjectAllocation.objects.filter(
                employee=self.employee,
                project=self.project,
                start_date__lte=self.date
            ).filter(
                Q(end_date__gte=self.date) | Q(end_date__isnull=True)
            ).exists()
        
            if not is_allocated:
                raise ValidationError(
                    f"Employee not allocated to project {self.project.project_code}"
                )

        # Prevent logging for completed project
        if self.project.status == "COMPLETED":
            raise ValidationError(
                "Cannot log time for completed project."
            )

        # Prevent logging for archived project
        if self.project.is_archived:
            raise ValidationError(
                "Cannot log time for archived project."
            )

        # Check task belongs to project
        if self.task and self.task.project != self.project:
            raise ValidationError(
                "Selected task does not belong to this project."
            )

        # Check daily hours limit
        existing_hours = TimesheetEntry.objects.filter(
            employee=self.employee,
            date=self.date
        ).exclude(pk=self.pk).aggregate(
            total_hours=Sum('hours')
        )['total_hours'] or 0

        # Ensure self.hours is not None
        hours_to_add = self.hours or 0

        if existing_hours + hours_to_add > 12:
            raise ValidationError(
                "Total hours for this day cannot exceed 12."
        )
        if self.date > timezone.now().date():
            raise ValidationError("Cannot log timesheet for future date.")
        if self.task and self.task.status == "COMPLETED":
            raise ValidationError("Cannot log hours for completed task.")

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

        # Auto complete project if all tasks finished
        project = self.project
        tasks = project.tasks.all()

        if tasks.exists() and not tasks.exclude(status="COMPLETED").exists():
            project.status = "COMPLETED"
            project.save()

    def __str__(self):
        return f"{self.employee.user.username} - {self.project.project_code} - {self.date}"
   
    @property
    def pending_hours(self):
        if not self.task:
            return 0

        estimated = self.task.estimated_hours or 0

        qs = TimesheetEntry.objects.filter(
            project=self.project,
            task=self.task
        )

        # if self.pk:
        #     qs = qs.exclude(pk=self.pk)

        total_logged = qs.aggregate(total=Sum('hours'))['total'] or 0

        return max(estimated - total_logged, 0)
class Document(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="project_docs/")
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
# models.py
class Poster(models.Model):
    title = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/')
    content_image = models.ImageField(upload_to='content/')
    content_video = models.FileField(upload_to='videos/content/', null=True, blank=True)

    video_thumbnail = models.ImageField(
        upload_to='videos/thumbnails/',
        null=True,
        blank=True
    )
    instagram_image = models.ImageField(upload_to='posters/insta/', null=True, blank=True)
    whatsapp_image = models.ImageField(upload_to='posters/whatsapp/', null=True, blank=True)
    facebook_image = models.ImageField(upload_to='posters/facebook/', null=True, blank=True)
     # 🔥 NEW OUTPUT VIDEOS
    video_instagram = models.FileField(upload_to='videos/insta/', null=True, blank=True)
    video_whatsapp = models.FileField(upload_to='videos/whatsapp/', null=True, blank=True)
    video_facebook = models.FileField(upload_to='videos/facebook/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
