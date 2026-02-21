from django.contrib import admin
from .models import Employee, Project, ProjectAllocation, TimesheetEntry

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'employee_id')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
    raw_id_fields = ('user',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_code', 'status', 'start_date', 'end_date', 'is_archived')
    list_filter = ('status', 'is_archived', 'start_date')
    search_fields = ('name', 'project_code', 'description')
    ordering = ('-start_date',)

@admin.register(ProjectAllocation)
class ProjectAllocationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'allocation_percentage', 'role_in_project', 'start_date', 'end_date')
    list_filter = ('project', 'employee', 'start_date')
    search_fields = ('employee__user__username', 'project__project_code', 'role_in_project')
    autocomplete_fields = ('employee', 'project')

@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'date', 'hours', 'billable')
    list_filter = ('billable', 'date', 'project', 'employee')
    search_fields = ('description', 'task_reference', 'employee__user__username', 'project__project_code')
    date_hierarchy = 'date'
    autocomplete_fields = ('employee', 'project')
