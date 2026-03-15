from django.contrib import admin
from django.utils.html import format_html
from .models import *


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'employee_code', 'employee_id', 'status', 'is_active')
    list_filter = ('role', 'status', 'is_active')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'employee_code',
        'employee_id'
    )
    raw_id_fields = ('user',)
    readonly_fields = ('employee_code',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'project_code',
        'status',
        'start_date',
        'end_date',
        'is_archived',
        'allocated_employees_count',
        'progress'
    )
    list_filter = ('status', 'is_archived', 'start_date')
    search_fields = ('name', 'project_code', 'description')
    ordering = ('-start_date',)


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
    list_filter = ('project', 'employee', 'start_date')
    search_fields = (
        'employee__user__username',
        'project__project_code',
        'role_in_project'
    )
    autocomplete_fields = ('employee', 'project')


# 🔹 Inline for multiple images
class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1
    readonly_fields = ["preview"]

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100"/>', obj.image.url)
        return "No Image"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'project',
        'assigned_to',
        'status',
        'estimated_hours',
        'created_at'
    )
    list_filter = ('status', 'project')
    search_fields = ('title', 'description', 'project__project_code')
    autocomplete_fields = ('project', 'assigned_to')
    
    inlines = [TaskImageInline]   # ✅ THIS IS REQUIRED


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
    list_filter = ('billable', 'date', 'project', 'employee')
    search_fields = (
        'description',
        'task__title',
        'employee__user__username',
        'project__project_code'
    )
    date_hierarchy = 'date'
    autocomplete_fields = ('employee', 'project', 'task')