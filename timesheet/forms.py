from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Project, ProjectAllocation, TimesheetEntry, Employee

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_code', 'status', 'description', 'start_date', 'end_date', 'is_archived']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            for field, value in cleaned_data.items():
                setattr(self.instance, field, value)
            try:
                self.instance.clean()
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return cleaned_data

class AllocationForm(forms.ModelForm):
    class Meta:
        model = ProjectAllocation
        fields = ['employee', 'project', 'allocation_percentage', 'role_in_project', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow allocating to non-archived projects
        self.fields['project'].queryset = Project.objects.filter(is_archived=False)
        if self.instance.pk and self.instance.project.is_archived:
            # If editing an existing allocation for an archived project, include it in the queryset
            self.fields['project'].queryset = Project.objects.filter(
                models.Q(is_archived=False) | models.Q(pk=self.instance.project.pk)
            )

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            # Update the current instance with cleaned_data to ensure clean() works correctly
            for field, value in cleaned_data.items():
                setattr(self.instance, field, value)
            try:
                self.instance.clean()
            except ValidationError as e:
                # Add the error to the non-field errors
                raise forms.ValidationError(e.messages)
        return cleaned_data

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
            # Filter projects to only those where the employee is allocated AND project is not archived
            allocated_projects = ProjectAllocation.objects.filter(
                employee=self.employee
            ).values_list('project_id', flat=True)
            self.fields['project'].queryset = Project.objects.filter(id__in=allocated_projects, is_archived=False)

    def clean(self):
        cleaned_data = super().clean()
        if self.employee and not self.errors:
            # We need to set the employee on the instance before calling clean
            self.instance.employee = self.employee
            for field, value in cleaned_data.items():
                setattr(self.instance, field, value)
            try:
                self.instance.clean()
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return cleaned_data
