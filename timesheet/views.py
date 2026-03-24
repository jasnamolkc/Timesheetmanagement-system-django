from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta

from .models import *
from .forms import *

# Template Mixins
class AjaxTemplateMixin:
    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal'):
            return ['timesheet/modal_form.html']
        return [self.template_name]

# Permission Mixins
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'employee') and self.request.user.employee.role == 'ADMIN'

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'employee') and self.request.user.employee.role in ['ADMIN', 'MANAGER']

# Auth Views
class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

# Dashboard
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'timesheet/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)

        employee = getattr(self.request.user, 'employee', None)

        if employee:
            context['total_hours_month'] = TimesheetEntry.objects.filter(
                employee=employee,
                date__gte=first_day_of_month
            ).aggregate(Sum('hours'))['hours__sum'] or 0

            context['total_active_projects_count'] = ProjectAllocation.objects.filter(
                employee=employee,
                end_date__gte=today
            ).count()
            context['recent_entries'] = TimesheetEntry.objects.filter(
                employee=employee
            ).select_related('project').order_by('-date')[:5]

            context['allocations'] = ProjectAllocation.objects.filter(
                employee=employee,
                end_date__gte=today
            ).select_related('project')

        if employee and employee.role in ['ADMIN', 'MANAGER']:
            context['total_employees_allocated'] = Employee.objects.filter(
                allocations__end_date__gte=today
            ).distinct().count()
            context['total_hours_month'] = TimesheetEntry.objects.filter(
                date__gte=first_day_of_month
            ).aggregate(Sum('hours'))['hours__sum'] or 0

            context['total_employees'] = Employee.objects.count()
            context['total_active_projects_count'] = Project.objects.filter(status='ACTIVE').count()
            context['recent_entries'] = TimesheetEntry.objects.select_related(
                'employee__user', 'project'
            ).order_by('-date')[:5]

            context['allocations'] = ProjectAllocation.objects.filter(
                end_date__gte=today
            ).select_related('employee__user', 'project')
        return context

# Project Views
# class ProjectListView(LoginRequiredMixin, ListView):
#     model = Project
#     template_name = 'timesheet/project_list.html'
#     context_object_name = 'projects'
#     paginate_by = 10
from django.db.models import Q

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Project

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .models import Project

from django.utils import timezone
from django.db.models import Prefetch, Q

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'timesheet/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        user_employee = getattr(user, 'employee', None)
        today = timezone.now().date()
        show_archived = self.request.GET.get('archived')

        queryset = Project.objects.all()

        # Admin / Manager / Superuser → all projects
        if user.is_superuser or (user_employee and user_employee.role in ['ADMIN', 'MANAGER']):
            if show_archived:
                queryset = queryset.filter(is_archived=True)
            else:
                queryset = queryset.filter(is_archived=False)

        # Employee → only allocated projects in current date range
        elif user_employee and user_employee.role == 'EMPLOYEE':
            queryset = queryset.filter(
                allocations__employee=user_employee
            ).filter(
                Q(allocations__end_date__gte=today) | Q(allocations__end_date__isnull=True)
            ).filter(
                
                is_archived=False
            ).distinct()
        else:
            queryset = Project.objects.none()
        # ✅ ADD THIS (VERY IMPORTANT)
        queryset = queryset.annotate(
            milestone_count=Count('milestones')   # 🔥 use your related_name
        )
        # Prefetch active allocations
        active_allocations = ProjectAllocation.objects.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        ).select_related('employee__user')

        queryset = queryset.prefetch_related(
            Prefetch('allocations', queryset=active_allocations, to_attr='active_allocs')
        )

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
# Archive Project View
class ProjectArchiveView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        project.is_archived = not project.is_archived
        project.save()

        return redirect(request.META.get('HTTP_REFERER', 'project_list'))
class ProjectCreateView(ManagerRequiredMixin, AjaxTemplateMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["milestone_formset"] = MilestoneFormSet(self.request.POST)
            context["document_formset"] = DocumentFormSet(self.request.POST, self.request.FILES)

        else:
            context["milestone_formset"] = MilestoneFormSet()
            context["document_formset"] = DocumentFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        milestone_formset = context["milestone_formset"]
        document_formset = context["document_formset"]
        print("ccc",context)

        # 🔥 SAVE PROJECT FIRST
        self.object = form.save()

        # 🔥 ATTACH INSTANCE BEFORE VALIDATION
        milestone_formset.instance = self.object
        document_formset.instance = self.object

        if milestone_formset.is_valid() and document_formset.is_valid():
            milestone_formset.save()
            document_formset.save()
            return redirect(self.success_url)

        return self.form_invalid(form)
class ProjectUpdateView(ManagerRequiredMixin, AjaxTemplateMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["milestone_formset"] = MilestoneFormSet(self.request.POST, instance=self.object)
            context["document_formset"] = DocumentFormSet(self.request.POST, self.request.FILES, instance=self.object)

        else:
            context["milestone_formset"] = MilestoneFormSet(instance=self.object)
            context["document_formset"] = DocumentFormSet(instance=self.object)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        milestone_formset = context["milestone_formset"]
        document_formset = context["document_formset"]
        print("ccc",context)
        # 🔥 DON'T SAVE YET
        self.object = form.save(commit=False)

        # attach instance BEFORE validation
        milestone_formset.instance = self.object
        document_formset.instance = self.object

        if milestone_formset.is_valid() and document_formset.is_valid():
            self.object.save()  # ✅ save project AFTER validation
            milestone_formset.save()
            document_formset.save()
            return redirect(self.success_url)

        return self.form_invalid(form)
def allocate_employee(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        employee_id = request.POST.get("employee")
        employee = Employee.objects.get(id=employee_id)
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        ProjectAllocation.objects.get_or_create(
            project=project,
            employee=employee,defaults={"allocation_percentage": 100},
            start_date=start_date,
            end_date=end_date
        )

        return redirect("project_list")

    employees = Employee.objects.filter(status = "APPROVED",role = 'EMPLOYEE')

    return render(request, "projects/allocate_employee.html", {
        "project": project,
        "employees": employees
    })
# Allocation Views
class AllocationListView(ManagerRequiredMixin, ListView):
    model = ProjectAllocation
    template_name = 'timesheet/allocation_list.html'
    context_object_name = 'allocations'

    def get_queryset(self):
        return super().get_queryset().select_related('employee__user', 'project')

class AllocationCreateView(ManagerRequiredMixin, AjaxTemplateMixin, CreateView):
    model = ProjectAllocation
    form_class = AllocationForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('allocation_list')

class AllocationUpdateView(ManagerRequiredMixin, AjaxTemplateMixin, UpdateView):
    model = ProjectAllocation
    form_class = AllocationForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('allocation_list')

class AllocationDeleteView(ManagerRequiredMixin, DeleteView):
    model = ProjectAllocation
    template_name = 'timesheet/entry_confirm_delete.html'
    success_url = reverse_lazy('allocation_list')

# # Timesheet Views
# class TimesheetListView(LoginRequiredMixin, ListView):
#     model = TimesheetEntry
#     template_name = 'timesheet/timesheet_list.html'
#     context_object_name = 'entries'
#     paginate_by = 15

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         user_employee = self.request.user.employee

#         if user_employee.role == 'EMPLOYEE':
#             queryset = queryset.filter(employee=user_employee)

#         # Filtering
#         project_id = self.request.GET.get('project')
#         if project_id:
#             queryset = queryset.filter(project_id=project_id)

#         employee_id = self.request.GET.get('employee')
#         if employee_id and user_employee.role in ['ADMIN', 'MANAGER']:
#             queryset = queryset.filter(employee_id=employee_id)

#         start_date = self.request.GET.get('start_date')
#         if start_date:
#             queryset = queryset.filter(date__gte=start_date)

#         end_date = self.request.GET.get('end_date')
#         if end_date:
#             queryset = queryset.filter(date__lte=end_date)

#         return queryset.select_related('project', 'employee__user').order_by('-date')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user_employee = self.request.user.employee

#         if user_employee.role in ['ADMIN', 'MANAGER']:
#             context['all_employees'] = Employee.objects.select_related('user').all()
#             context['all_projects'] = Project.objects.all()
#         else:
#             context['all_projects'] = Project.objects.filter(allocations__employee=user_employee).distinct()

#         return context

# class TimesheetCreateView(LoginRequiredMixin, AjaxTemplateMixin, CreateView):
#     model = TimesheetEntry
#     form_class = TimesheetEntryForm
#     template_name = 'timesheet/form_page.html'
#     success_url = reverse_lazy('timesheet_list')

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['employee'] = self.request.user.employee
#         return kwargs

#     def form_valid(self, form):
#         form.instance.employee = self.request.user.employee
#         return super().form_valid(form)

# class TimesheetUpdateView(LoginRequiredMixin, UserPassesTestMixin, AjaxTemplateMixin, UpdateView):
#     model = TimesheetEntry
#     form_class = TimesheetEntryForm
#     template_name = 'timesheet/form_page.html'
#     success_url = reverse_lazy('timesheet_list')

#     def test_func(self):
#         obj = self.get_object()
#         return obj.employee == self.request.user.employee or self.request.user.employee.role in ['ADMIN', 'MANAGER']

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['employee'] = self.request.user.employee
#         return kwargs

# class TimesheetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
#     model = TimesheetEntry
#     template_name = 'timesheet/entry_confirm_delete.html'
#     success_url = reverse_lazy('timesheet_list')

#     def test_func(self):
#         obj = self.get_object()
#         return obj.employee == self.request.user.employee or self.request.user.employee.role in ['ADMIN', 'MANAGER']
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import TimesheetEntry, Employee, Project
from .forms import TimesheetEntryForm


# =========================
# TIMESHEET LIST
# =========================
# class TimesheetListView(LoginRequiredMixin, ListView):
#     model = TimesheetEntry
#     template_name = 'timesheet/timesheet_list.html'
#     context_object_name = 'entries'
#     paginate_by = 15

#     def get_queryset(self):
#         user = self.request.user
#         user_employee = getattr(user, "employee", None)

#         queryset = TimesheetEntry.objects.select_related(
#             'project',
#             'employee__user'
#         )

#         # Employee restriction
#         if user_employee and user_employee.role == 'EMPLOYEE':
#             queryset = queryset.filter(employee=user_employee)

#         # Filters
#         project_id = self.request.GET.get('project')
#         if project_id:
#             queryset = queryset.filter(project_id=project_id)

#         employee_id = self.request.GET.get('employee')
#         if employee_id and user_employee and user_employee.role in ['ADMIN', 'MANAGER']:
#             queryset = queryset.filter(employee_id=employee_id)

#         start_date = self.request.GET.get('start_date')
#         if start_date:
#             queryset = queryset.filter(date__gte=start_date)

#         end_date = self.request.GET.get('end_date')
#         if end_date:
#             queryset = queryset.filter(date__lte=end_date)

#         return queryset.order_by('-date')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         user_employee = getattr(user, "employee", None)

#         # Permission flag (clean template usage)
#         context["can_manage"] = (
#             user.is_superuser or
#             (user_employee and user_employee.role in ['ADMIN', 'MANAGER'])
#         )

#         # Employee & Project filter lists
#         if context["can_manage"]:
#             context['all_employees'] = Employee.objects.select_related('user').all()
#             context['all_projects'] = Project.objects.filter(is_archived=False)
#         else:
#             context['all_projects'] = Project.objects.filter(
#                 allocations__employee=user_employee,
#                 is_archived=False
#             ).distinct()

#         # Total Hours
#         context['total_hours'] = self.get_queryset().aggregate(
#             total=Sum('hours')
#         )['total'] or 0

#         return context


# # =========================
# # CREATE
# # =========================
# # class TimesheetCreateView(LoginRequiredMixin, CreateView):
# #     model = TimesheetEntry
# #     form_class = TimesheetEntryForm
# #     template_name = 'timesheet/form_page.html'
# #     success_url = reverse_lazy('timesheet_list')

# #     def get_form_kwargs(self):
# #         kwargs = super().get_form_kwargs()
# #         user_employee = getattr(self.request.user, "employee", None)
# #         if user_employee:
# #             kwargs['employee'] = user_employee
# #         return kwargs

# #     def form_valid(self, form):
# #         user_employee = getattr(self.request.user, "employee", None)
# #         if user_employee:
# #             form.instance.employee = user_employee
# #         return super().form_valid(form)

# from django.urls import reverse_lazy
# from django.template.loader import render_to_string
# from django.http import JsonResponse
# from django.shortcuts import redirect

# class TimesheetCreateView(LoginRequiredMixin, CreateView):
#     model = TimesheetEntry
#     form_class = TimesheetEntryForm
#     template_name = 'timesheet/form_page.html'
#     success_url = reverse_lazy('timesheet_list')

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         user_employee = getattr(self.request.user, "employee", None)
#         if user_employee:
#             kwargs['employee'] = user_employee
#         return kwargs

#     def form_valid(self, form):
#         user_employee = getattr(self.request.user, "employee", None)
#         if user_employee:
#             form.instance.employee = user_employee

#         self.object = form.save()

#         # ✅ If AJAX → return JSON success
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({"success": True})

#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         # ✅ If AJAX → return form HTML again
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             html = render_to_string(
#                 "timesheet/modal_form.html",
#                 {"form": form},
#                 request=self.request
#             )
#             return JsonResponse({"html": html}, status=400)

#         return super().form_invalid(form)

#     def get_template_names(self):
#         # ✅ If AJAX → return only modal form
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return ["timesheet/modal_form.html"]

#         return [self.template_name]
# =========================
# UPDATE
# =========================
class TimesheetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('timesheet_list')

    def test_func(self):
        obj = self.get_object()
        user_employee = getattr(self.request.user, "employee", None)

        return (
            obj.employee == user_employee or
            (user_employee and user_employee.role in ['ADMIN', 'MANAGER'])
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_employee = getattr(self.request.user, "employee", None)
        if user_employee:
            kwargs['employee'] = user_employee
        return kwargs


# =========================
# DELETE
# =========================
class TimesheetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TimesheetEntry
    template_name = 'timesheet/entry_confirm_delete.html'
    success_url = reverse_lazy('timesheet_list')

    def test_func(self):
        obj = self.get_object()
        user_employee = getattr(self.request.user, "employee", None)

        return (
            obj.employee == user_employee or
            (user_employee and user_employee.role in ['ADMIN', 'MANAGER'])
        )
# Summary Report
class SummaryReportView(ManagerRequiredMixin, TemplateView):
    template_name = 'timesheet/summary_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = timezone.now().strftime('%Y-%m-%d')

        entries = TimesheetEntry.objects.filter(date__range=[start_date, end_date])

        context['project_summary'] = entries.values('project__name', 'project__project_code').annotate(
            total_hours=Sum('hours'),
            billable_hours=Sum('hours', filter=models.Q(billable=True)),
            non_billable_hours=Sum('hours', filter=models.Q(billable=False))
        )

        context['employee_summary'] = entries.values('employee__user__first_name', 'employee__user__last_name').annotate(
            total_hours=Sum('hours')
        )

        context['start_date'] = start_date
        context['end_date'] = end_date

        return context

class ExportCSVView(ManagerRequiredMixin, View):
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            return HttpResponse("Please provide both start_date and end_date.", status=400)

        entries = TimesheetEntry.objects.filter(date__range=[start_date, end_date]).select_related(
            'employee__user', 'project'
        ).values_list(
            'date', 'employee__user__username', 'project__project_code', 'hours', 'description', 'billable'
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="timesheet_report_{start_date}_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Employee', 'Project', 'Hours', 'Description', 'Billable'])
        for entry in entries:
            writer.writerow(entry)

        return response
from django.db.models import Q

class EmployeeListView(ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 10

    def get_queryset(self):
        queryset = Employee.objects.select_related("user")

        search = self.request.GET.get("search")
        role = self.request.GET.get("role")

        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_code__icontains=search)
            )

        if role:
            queryset = queryset.filter(role=role)

        return queryset.order_by("-id")
from django.shortcuts import redirect, get_object_or_404


def approve_employee(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.status = "APPROVED"
    emp.save()
    return redirect("employee_list")
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Task, Project, Employee
from django.db.models import Q


from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from .models import Task, Project, ProjectAllocation

def task_page(request):
    user = request.user
    employee = getattr(user, "employee", None)
    today = timezone.now().date()

   # 👑 SUPERUSER or ADMIN or MANAGER → ALL tasks
    if user.is_superuser or not employee or employee.role in ["ADMIN", "MANAGER"]:
        tasks = Task.objects.select_related("project", "assigned_to")\
                            .order_by('-id')

        projects = Project.objects.all()

    # 👤 EMPLOYEE → ONLY assigned tasks
    else:
        tasks = Task.objects.select_related("project", "assigned_to")\
                            .filter(assigned_to=employee)\
                            .order_by('-id')

        projects = Project.objects.filter(tasks__assigned_to=employee).distinct()
    return render(request, "tasks/task_list.html", {
        "tasks": tasks,
        "projects": projects
    })


def task_list(request):

    search = request.GET.get("search")
    project = request.GET.get("project")

    tasks = Task.objects.select_related("project","milestone", "assigned_to")

    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    if project:
        tasks = tasks.filter(project_id=project)

    data = []

    for t in tasks:
        data.append({
            "id": t.id,
            "title": t.title,
            "project": t.project.name,
            "milestone": t.milestone.name if t.milestone else "",
            "employee": t.assigned_to.user.username if t.assigned_to else "",
            "status": t.status,
        })

    return JsonResponse(data, safe=False)


# def task_create(request):
#     if request.method == "POST":

#         task = Task(
#             title=request.POST.get("title"),
#             project_id=request.POST.get("project"),
#             assigned_to_id=request.POST.get("assigned_to") or None,
#             status=request.POST.get("status"),
#             estimated_hours=request.POST.get("estimated_hours") or 0,
#             description=request.POST.get("description") or ""
#         )

#         task.full_clean()
#         task.save()

#         return JsonResponse({
#             "success": True,
#             "redirect": "/tasks/"   # Task list page URL
#         })

#     projects = Project.objects.all()

#     # Only employees
#     employees = Employee.objects.filter(role="EMPLOYEE", is_active=True)

#     return render(request, "tasks/task_form.html", {
#         "projects": projects,
#         "employees": employees
#     })
# class TaskCreateView(LoginRequiredMixin, CreateView):
#     model = Task
#     form_class = TaskForm
#     template_name = "tasks/modal_form.html"
#     success_url = reverse_lazy("task_page")

#     def form_valid(self, form):
#         self.object = form.save()

#         if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             return JsonResponse({
#                 "success": True,
#                 "redirect": reverse("task_page")
#             })

#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             html = render_to_string(
#                 "tasks/modal_form.html",
#                 {"form": form},
#                 request=self.request
#             )
#             return JsonResponse({"html": html}, status=400)

#         return super().form_invalid(form)

#     def get_template_names(self):
#         if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             return ["tasks/modal_form.html"]
#         return [self.template_name]
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/modal_form.html"
    success_url = reverse_lazy("task_page")
    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")  # get project from query string
        if project_id:
            initial["project"] = project_id
        return initial
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["milestones"] = Milestone.objects.select_related("project")
        return context
    def form_valid(self, form):
        self.object = form.save()
        # handle multiple images
        images = self.request.FILES.getlist("images")

        for img in images:
            TaskImage.objects.create(
                task=self.object,
                image=img
            )

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "task_id": self.object.id,
                "task_name": str(self.object)
            })

        return redirect(self.success_url)

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html = render_to_string(
                "tasks/modal_form.html",
                {"form": form},
                request=self.request
            )
            return JsonResponse({"html": html}, status=400)

        return super().form_invalid(form)

    def get_template_names(self):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ["tasks/modal_form.html"]
        return [self.template_name]
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/modal_form.html"
    success_url = reverse_lazy("task_page")
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["milestones"] = Milestone.objects.select_related("project")
        return context
    def form_valid(self, form):
        self.object = form.save()
        images = self.request.FILES.getlist("images")

        for img in images:
            TaskImage.objects.create(
                task=self.object,
                image=img
            )

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "redirect": reverse("task_page")
            })

        return redirect(self.success_url)

    def form_invalid(self, form):
        # Print form errors in terminal
        print("FORM ERRORS:", form.errors)
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html = render_to_string(
                "tasks/modal_form.html",
                {"form": form},
                request=self.request
            )
            return JsonResponse({"html": html}, status=400)

        return super().form_invalid(form)

    def get_template_names(self):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ["tasks/modal_form.html"]
        return [self.template_name]

def task_delete(request, id):

    task = get_object_or_404(Task, id=id)
    task.delete()

    return JsonResponse({"status": "deleted"})

from django.views.generic import ListView, CreateView
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import TimesheetEntry
from .forms import TimesheetEntryForm


from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q
from .models import TimesheetEntry, Project, ProjectAllocation

class TimesheetListView(ListView):
    model = TimesheetEntry
    template_name = "timesheet/list.html"
    context_object_name = "entries"
    paginate_by = 10  # optional

    def get_queryset(self):
        user = self.request.user
        employee = getattr(user, 'employee', None)
        today = timezone.now().date()

        # Base queryset with related objects
        qs = TimesheetEntry.objects.select_related("employee__user", "project", "task")

        # Admin / Manager / Superuser → see all entries
        if not (employee and employee.role == 'EMPLOYEE'):
            pass  # leave qs as all entries

        # Employee → filter by their allocated projects
        else:
            allocated_projects = ProjectAllocation.objects.filter(
                employee=employee
            ).filter(
                Q(end_date__gte=today) | Q(end_date__isnull=True)
            ).values_list('project_id', flat=True)

            qs = qs.filter(
                employee=employee,
                project_id__in=allocated_projects
            )

        # Optional project filter from GET
        project_id = self.request.GET.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)

        return qs.order_by("-date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        employee = getattr(user, 'employee', None)
        today = timezone.now().date()

        # Projects for filter dropdown
        if not (employee and employee.role == 'EMPLOYEE'):
            context['all_projects'] = Project.objects.filter(is_archived=False)
            context['all_employees'] = Employee.objects.filter(status='APPROVED')
            context['can_manage'] = True
        else:
            allocated_projects = ProjectAllocation.objects.filter(
                employee=employee
            ).filter(
                Q(end_date__gte=today) | Q(end_date__isnull=True)
            ).values_list('project_id', flat=True)
            context['all_projects'] = Project.objects.filter(id__in=allocated_projects, is_archived=False)
            context['all_employees'] = None
            context['can_manage'] = False

        return context

class TimesheetCreateView(LoginRequiredMixin, CreateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = "timesheet/modal_form.html"
    success_url = reverse_lazy('timesheet_list')  # redirect after non-AJAX submit

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_employee = getattr(self.request.user, "employee", None)
        kwargs['employee'] = user_employee
        return kwargs

    def form_valid(self, form):
        user_employee = getattr(self.request.user, "employee", None)

        if not user_employee:
            return JsonResponse({"error": "Employee profile not found"}, status=400)

        obj = form.save(commit=False)
        obj.employee = user_employee
        obj.save()

        # Return JSON for AJAX
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        # Normal POST fallback
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string("timesheet/modal_form.html", {"form": form}, request=self.request)
            return JsonResponse({"success": False, "html": html}, status=400)
        return super().form_invalid(form)

    def get_template_names(self):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ["timesheet/modal_form.html"]
        return [self.template_name]
# def tasks_by_project(request, project_id):
#     tasks = Task.objects.filter(project_id=project_id)
#     data = {
#         "tasks": [{"id": t.id, "name": t.name} for t in tasks]
#     }
#     return JsonResponse(data)
def tasks_by_project(request, project_id):
    try:
        tasks = Task.objects.filter(project_id=project_id).values('id', 'title')
        return JsonResponse({'tasks': list(tasks)})
    except Task.DoesNotExist:
        return JsonResponse({'tasks': []})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def milestone_list(request):
    milestones = Milestone.objects.select_related("project")
    return render(request, "milestones/milestone_list.html", {"milestones": milestones})


def milestone_create(request):

    form = MilestoneForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect("milestone_list")

    return render(request, "milestones/milestone_form.html", {"form": form})


def milestone_update(request, pk):

    milestone = get_object_or_404(Milestone, pk=pk)

    form = MilestoneForm(request.POST or None, instance=milestone)

    if form.is_valid():
        form.save()
        return redirect("milestone_list")

    return render(request, "milestones/milestone_form.html", {"form": form})


def milestone_delete(request, pk):

    milestone = get_object_or_404(Milestone, pk=pk)

    if request.method == "POST":
        milestone.delete()
        return redirect("milestone_list")

    return render(request, "confirm_delete.html", {"object": milestone})
def milestones_by_project(request, project_id):

    milestones = Milestone.objects.filter(project_id=project_id)

    data = {
        "milestones": [
            {
                "id": m.id,
                "name": m.name
            }
            for m in milestones
        ]
    }

    return JsonResponse(data)
def employees_by_project(request, project_id):

    allocations = ProjectAllocation.objects.select_related(
        "employee__user"
    ).filter(project_id=project_id)

    data = {
        "employees": [
            {
                "id": a.employee.id,
                "name": a.employee.user.get_full_name() or a.employee.user.username
            }
            for a in allocations
        ]
    }

    return JsonResponse(data)

from django.views.decorators.http import require_POST

@require_POST
def delete_task_image(request, pk):

    image = TaskImage.objects.get(pk=pk)
    image.delete()

    return JsonResponse({"success": True})
from datetime import date

def project_milestones(request, pk):
    project = Project.objects.get(pk=pk)
    milestones = project.milestones.all()

    return render(request, "timesheet/milestone_list.html", {
        "project": project,
        "milestones": milestones,
        "today": date.today()   # 🔥 REQUIRED
    })
def project_documents(request, pk):
    project = Project.objects.get(pk=pk)
    documents = project.documents.all()

    return render(request, "timesheet/document_list.html", {
        "project": project,
        "documents": documents
    })