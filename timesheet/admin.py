from django.contrib import admin
from django.utils.html import format_html
from .models import *


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'employee_code',
        'employee_id',
        'status',
        'is_active'
    )

    list_filter = (
        'role',
        'status',
        'is_active'
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'employee_code',
        'employee_id'
    )

    raw_id_fields = ('user',)
    readonly_fields = ('employee_code',)


# ---------------- PROJECT ---------------- #

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'project_code',
        'status',
        'start_date',
        'end_date',
        'allocated_employees_count',
        'progress',
        'milestone_progress'
    )

    list_filter = (
        'status',
        'start_date',
        'is_archived'
    )

    search_fields = (
        'name',
        'project_code',
        'description'
    )

    ordering = ('-start_date',)


# ---------------- PROJECT ALLOCATION ---------------- #

@admin.register(ProjectAllocation)
class ProjectAllocationAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'project',
        'allocation_percentage',
        'role_in_project',
        'start_date',
        'end_date'
    )

    list_filter = (
        'project',
        'employee',
        'start_date'
    )

    search_fields = (
        'employee__user__username',
        'project__project_code',
        'role_in_project'
    )

    autocomplete_fields = (
        'employee',
        'project'
    )


# ---------------- MILESTONE ---------------- #

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'project',
        'status',
        'start_date',
        'due_date',
        'task_count',
        'progress'
    )

    list_filter = (
        'project',
        'status',
        'start_date',
        'due_date'
    )

    search_fields = (
        'name',
        'project__name',
        'project__project_code'
    )

    autocomplete_fields = ('project',)

    def task_count(self, obj):
        return obj.tasks.count()

    task_count.short_description = "Tasks"


# ---------------- TASK IMAGE INLINE ---------------- #

class TaskImageInline(admin.TabularInline):

    model = TaskImage
    extra = 1

    readonly_fields = ("preview",)

    def preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="100"/>',
                obj.image.url
            )

        return "No Image"


# ---------------- TASK ---------------- #

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'project',
        'milestone',
        'assigned_to',
        'status',
        'estimated_hours',
        'created_at'
    )

    list_filter = (
        'status',
        'project',
        'milestone'
    )

    search_fields = (
        'title',
        'description',
        'project__project_code'
    )

    autocomplete_fields = (
        'project',
        'milestone',
        'assigned_to'
    )

    inlines = [TaskImageInline]


# ---------------- TIMESHEET ---------------- #

@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'project',
        'task',
        'date',
        'hours',
        'billable'
    )

    list_filter = (
        'billable',
        'date',
        'project',
        'employee'
    )

    search_fields = (
        'description',
        'task__title',
        'employee__user__username',
        'project__project_code'
    )

    date_hierarchy = 'date'

    autocomplete_fields = (
        'employee',
        'project',
        'task'
    )
@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):

    list_display = (
        "task",
        "preview",
        "uploaded_at",
    )

    list_filter = (
        "task__project",
        "uploaded_at",
    )

    search_fields = (
        "task__title",
        "task__project__name",
    )

    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="120" style="border-radius:6px"/>',
                obj.image.url
            )
        return "No Image"

    preview.short_description = "Image Preview"