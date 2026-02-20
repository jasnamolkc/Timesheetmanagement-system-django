from django import forms
from .models import Project, ProjectAllocation, TimesheetEntry, Employee

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_code', 'status', 'description', 'start_date', 'end_date', 'is_archived']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class AllocationForm(forms.ModelForm):
    class Meta:
        model = ProjectAllocation
        fields = ['employee', 'project', 'allocation_percentage', 'role_in_project', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TimesheetEntryForm(forms.ModelForm):
    class Meta:
        model = TimesheetEntry
        fields = ['project', 'date', 'hours', 'description', 'task_reference', 'billable']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        if self.employee:
            # Filter projects to only those where the employee is allocated
            allocated_projects = ProjectAllocation.objects.filter(
                employee=self.employee
            ).values_list('project_id', flat=True)
            self.fields['project'].queryset = Project.objects.filter(id__in=allocated_projects)

    def clean(self):
        cleaned_data = super().clean()
        if self.employee:
            instance = self.instance
            instance.employee = self.employee
            # The model's clean method will be called during full_clean
        return cleaned_data
