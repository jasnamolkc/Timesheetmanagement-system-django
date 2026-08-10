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
        self.is_fixed = kwargs.pop('is_fixed', False)
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

        # Determine selected task / project from POST data, initial values, or instance
        task_id = None
        if 'task' in self.data:
            try:
                task_id = int(self.data.get('task'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('task'):
            try:
                task_id = int(self.initial.get('task'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.task:
            task_id = self.instance.task.id

        project_id = None
        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('project'):
            try:
                project_id = int(self.initial.get('project'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.project:
            project_id = self.instance.project.id

        # If task_id is specified but project_id is not set, derive project_id from the task
        if task_id and not project_id:
            try:
                task_obj = Task.objects.select_related('project').get(id=task_id)
                project_id = task_obj.project_id
            except Task.DoesNotExist:
                pass

        if project_id:
            # Guarantee the selected project is included in project queryset
            self.fields['project'].queryset = (
                self.fields['project'].queryset | Project.objects.filter(id=project_id)
            ).distinct()
            self.fields['task'].queryset = Task.objects.filter(project_id=project_id)
            self.initial['project'] = project_id

        if task_id:
            self.initial['task'] = task_id

        # Lock/Disable project and task if is_fixed is requested or when logging for a specific task
        if self.is_fixed or (self.initial.get('project') and self.initial.get('task')):
            self.is_fixed = True
            self.fields['project'].disabled = True
            self.fields['task'].disabled = True

        # Light theme input styling
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                cls = "w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-2xs"
                if field.disabled:
                    cls = "w-full bg-slate-100 border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-700 font-semibold cursor-not-allowed pointer-events-none"
                field.widget.attrs.update({"class": cls})

    def clean(self):
        cleaned_data = super().clean()
        if self.employee:
            self.instance.employee = self.employee

        proj = cleaned_data.get('project')
        if not proj and self.is_fixed and self.initial.get('project'):
            proj_id = self.initial.get('project')
            proj = Project.objects.filter(id=proj_id).first()

        if proj:
            self.instance.project = proj
            cleaned_data['project'] = proj

        task = cleaned_data.get('task')
        if not task and self.is_fixed and self.initial.get('task'):
            task_id = self.initial.get('task')
            task = Task.objects.filter(id=task_id).first()

        if task:
            self.instance.task = task
            cleaned_data['task'] = task

        if cleaned_data.get('date'):
            self.instance.date = cleaned_data.get('date')

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
            "due_date"
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Default empty
        self.fields["milestone"].queryset = Milestone.objects.none()
        self.fields["assigned_to"].queryset = Employee.objects.none()

        # Determine selected project from POST data, initial values, or instance
        project_id = None
        if "project" in self.data:
            try:
                project_id = int(self.data.get("project"))
            except (ValueError, TypeError):
                pass
        elif self.initial.get("project"):
            try:
                project_id = int(self.initial.get("project"))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.project:
            project_id = self.instance.project.id

        if project_id:
            # Milestones of selected project
            milestone_qs = Milestone.objects.filter(project_id=project_id)
            if self.instance.pk and self.instance.milestone:
                milestone_qs = milestone_qs | Milestone.objects.filter(id=self.instance.milestone.id)
            self.fields["milestone"].queryset = milestone_qs.distinct()

            # Allocated employees
            allocated = ProjectAllocation.objects.filter(project_id=project_id).values_list("employee_id", flat=True)
            employee_qs = Employee.objects.filter(id__in=allocated, is_active=True)
            if self.instance.pk and self.instance.assigned_to:
                employee_qs = employee_qs | Employee.objects.filter(id=self.instance.assigned_to.id)
            self.fields["assigned_to"].queryset = employee_qs.distinct()

        # Styling
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({
                    "class": "w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-2xs"
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
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({
                    "class": "w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-2xs"
                })

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'file']
from django.forms import inlineformset_factory

MilestoneFormSet = inlineformset_factory(
    Project,
    Milestone,
    form=MilestoneForm,
    extra=0,
    can_delete=True

)

DocumentFormSet = inlineformset_factory(
    Project,
    Document,
    form=DocumentForm,
    extra=0,
    can_delete=True
)


# Add this at bottom of your forms.py

class PosterForm(forms.ModelForm):
    class Meta:
        model = Poster
        fields = ['title', 'logo', 'content_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply your UI styling
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({
                    "class": "w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-2xs"
                })

class VideoPosterForm(forms.ModelForm):
    class Meta:
        model = Poster
        fields = ['title', 'logo', 'content_video']
