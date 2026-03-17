from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *

class RegistrationForm(UserCreationForm):
    # first_name = forms.CharField(max_length=30, required=True)
    # last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class ProjectForm(forms.ModelForm):
    
    class Meta:
        model = Project
        fields = ['name', 'project_code', 'status', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        instance = Project(**cleaned_data)
        try:
            instance.clean()
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return cleaned_data

class AllocationForm(forms.ModelForm):
    class Meta:
        model = ProjectAllocation
        fields = ['employee', 'project', 'role_in_project', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow allocating to non-archived projects
        self.fields['project'].queryset = Project.objects.filter(is_archived=False)
        if self.instance.pk and self.instance.project.is_archived:
            # If editing an existing allocation for an archived project, include it in the queryset
            self.fields['project'].queryset = Project.objects.filter(
                models.Q(is_archived=False) | models.Q(pk=self.instance.project.pk))

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            instance = ProjectAllocation(**cleaned_data)
            try:
                instance.clean()
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return cleaned_data

# class TimesheetEntryForm(forms.ModelForm):
#     class Meta:
#         model = TimesheetEntry
#         fields = ['project', 'task', 'date', 'hours', 'description', 'billable']
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#             'description': forms.Textarea(attrs={'rows': 3}),
#         }

#     def __init__(self, *args, **kwargs):
#         self.employee = kwargs.pop('employee', None)
#         super().__init__(*args, **kwargs)
#         if self.employee:
#             # Filter projects to only those where the employee is allocated AND project is not archived
#             allocated_projects = ProjectAllocation.objects.filter(
#                 employee=self.employee
#             ).values_list('project_id', flat=True)
#             self.fields['project'].queryset = Project.objects.filter(id__in=allocated_projects, is_archived=False)

#     def clean(self):
#         cleaned_data = super().clean()
#         if self.employee and not self.errors:
#             # We need to set the employee on the instance before calling clean
#             self.instance.employee = self.employee
#             self.instance.project = cleaned_data.get('project')
#             self.instance.date = cleaned_data.get('date')
#             try:
#                 self.instance.clean()
#             except ValidationError as e:
#                 raise forms.ValidationError(e.messages)
#         return cleaned_data
# class TimesheetEntryForm(forms.ModelForm):
#     class Meta:
#         model = TimesheetEntry
#         fields = ['project', 'task', 'date', 'hours', 'description', 'billable']
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#             'description': forms.Textarea(attrs={'rows': 3}), }

#     def __init__(self, *args, **kwargs):
#         self.employee = kwargs.pop('employee', None)
#         super().__init__(*args, **kwargs)

#         # Filter projects based on allocation
#         if self.employee:
#             allocated_projects = ProjectAllocation.objects.filter(
#                 employee=self.employee
#             ).values_list('project_id', flat=True)

#             self.fields['project'].queryset = Project.objects.filter(id__in=allocated_projects,is_archived=False)

#         # Default: no tasks until project selected
#         self.fields['task'].queryset = Task.objects.none()

#         # When project selected (POST or GET)
#         if 'project' in self.data:
#             try:
#                 project_id = int(self.data.get('project'))
#                 self.fields['task'].queryset = Task.objects.filter(project_id=project_id)
#             except (ValueError, TypeError):
#                 pass

#         # When editing existing entry
#         elif self.instance.pk and self.instance.project:
#             self.fields['task'].queryset = Task.objects.filter(
#                 project=self.instance.project)

#     def clean(self):
#         cleaned_data = super().clean()

#         if self.employee and not self.errors:
#             self.instance.employee = self.employee
#             self.instance.project = cleaned_data.get('project')
#             self.instance.date = cleaned_data.get('date')

#             try:
#                 self.instance.clean()
#             except ValidationError as e:
#                 raise forms.ValidationError(e.messages)

#         return cleaned_data
class TimesheetEntryForm(forms.ModelForm):
    class Meta:
        model = TimesheetEntry
        fields = ['project', 'task', 'date', 'hours', 'description', 'billable']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)

        if self.employee:
            # Admin / Manager / Superuser → show all non-archived projects
            if self.employee.role in ['ADMIN', 'MANAGER'] or self.employee.user.is_superuser:
                self.fields['project'].queryset = Project.objects.filter(is_archived=False)
            else:
                # Employee → only allocated projects
                allocated_projects = ProjectAllocation.objects.filter(
                    employee=self.employee
                ).values_list('project_id', flat=True)

                self.fields['project'].queryset = Project.objects.filter(
                    id__in=allocated_projects,
                    is_archived=False
                )

        else:
            # fallback: empty queryset
            self.fields['project'].queryset = Project.objects.none()

        # Default: no tasks until project selected
        self.fields['task'].queryset = Task.objects.none()

        # When project selected (POST or GET)
        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
                self.fields['task'].queryset = Task.objects.filter(project_id=project_id)
            except (ValueError, TypeError):
                pass

        # When editing existing entry
        elif self.instance.pk and self.instance.project:
            self.fields['task'].queryset = Task.objects.filter(
                project=self.instance.project
            )

    def clean(self):
        cleaned_data = super().clean()
        if self.employee and not self.errors:
            self.instance.employee = self.employee
            self.instance.project = cleaned_data.get('project')
            self.instance.date = cleaned_data.get('date')

            try:
                self.instance.clean()
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return cleaned_data
from django import forms
from .models import Task, Employee


class TaskForm(forms.ModelForm):
    # images = MultipleFileField(required=False)


    class Meta:
        model = Task
        fields = [
            "project",
            "title",
            "description",
            "milestone",
            "assigned_to",
            "status",
            "estimated_hours",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Default empty
        self.fields["milestone"].queryset = Milestone.objects.none()
        self.fields["assigned_to"].queryset = Employee.objects.none()

        # When project selected in form (Create)
        if "project" in self.data:
            try:
                project_id = int(self.data.get("project"))

                # Milestones of selected project
                self.fields["milestone"].queryset = Milestone.objects.filter(
                    project_id=project_id
                )

                # Allocated employees
                allocated = ProjectAllocation.objects.filter(
                    project_id=project_id
                ).values_list("employee_id", flat=True)

                self.fields["assigned_to"].queryset = Employee.objects.filter(
                    id__in=allocated,
                    is_active=True
                )

            except (ValueError, TypeError):
                pass

        # When editing existing task
        elif self.instance.pk and self.instance.project:

            project = self.instance.project

            # Milestones
            milestone_qs = Milestone.objects.filter(project=project)

            if self.instance.milestone:
                milestone_qs = milestone_qs | Milestone.objects.filter(id=self.instance.milestone.id)

            self.fields["milestone"].queryset = milestone_qs.distinct()

            # Allocated employees
            allocated = ProjectAllocation.objects.filter(
                project=project
            ).values_list("employee_id", flat=True)

            employee_qs = Employee.objects.filter(
                id__in=allocated,
                is_active=True
            )

            if self.instance.assigned_to:
                employee_qs = employee_qs | Employee.objects.filter(id=self.instance.assigned_to.id)

            self.fields["assigned_to"].queryset = employee_qs.distinct()

        # Styling
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
            })
class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = [
            "project",
            "name",
            "start_date",
            "due_date",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        for field in self.fields.values():
                field.widget.attrs.update({
                    "class": "w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                })
from django.forms import inlineformset_factory

MilestoneFormSet = inlineformset_factory(
    Project,
    Milestone,
    form=MilestoneForm,
    extra=0,
    can_delete=True
)