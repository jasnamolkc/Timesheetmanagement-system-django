from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta

from .models import Project, ProjectAllocation, TimesheetEntry, Employee
from .forms import ProjectForm, AllocationForm, TimesheetEntryForm, RegistrationForm

# Template Mixins
class AjaxTemplateMixin:
    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal'):
            return ['timesheet/modal_form.html']
        return [self.template_name]

# Permission Mixins
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        return hasattr(self.request.user, 'employee') and self.request.user.employee.role == 'ADMIN'

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        return hasattr(self.request.user, 'employee') and self.request.user.employee.role in ['ADMIN', 'MANAGER']

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

            context['active_projects_count'] = ProjectAllocation.objects.filter(
                employee=employee,
                end_date__gte=today
            ).count()

        if (employee and employee.role in ['ADMIN', 'MANAGER']) or self.request.user.is_superuser:
            context['total_employees_allocated'] = Employee.objects.filter(
                allocations__end_date__gte=today
            ).distinct().count()
            context['total_active_projects'] = Project.objects.filter(status='ACTIVE').count()

        return context

# Project Views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'timesheet/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        # Annotate with assigned employee count for efficiency
        queryset = Project.objects.annotate(
            assigned_count=Count('allocations', distinct=True)
        ).order_by('-start_date', 'name')

        user_employee = getattr(self.request.user, 'employee', None)
        # Employees should only see projects they are allocated to
        if user_employee and user_employee.role == 'EMPLOYEE' and not self.request.user.is_superuser:
            queryset = queryset.filter(allocations__employee=user_employee).distinct()

        if self.request.GET.get('archived') == '1':
            return queryset.filter(is_archived=True)
        return queryset.filter(is_archived=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_archived'] = self.request.GET.get('archived') == '1'
        return context

class ProjectArchiveView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        project.is_archived = not project.is_archived
        project.save()
        return redirect('project_list')

class ProjectCreateView(ManagerRequiredMixin, AjaxTemplateMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('project_list')

class ProjectUpdateView(ManagerRequiredMixin, AjaxTemplateMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('project_list')

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

# Timesheet Views
class TimesheetListView(LoginRequiredMixin, ListView):
    model = TimesheetEntry
    template_name = 'timesheet/timesheet_list.html'
    context_object_name = 'entries'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        user_employee = getattr(self.request.user, 'employee', None)

        if not user_employee:
            return queryset.none() if not self.request.user.is_superuser else queryset

        if user_employee.role == 'EMPLOYEE':
            queryset = queryset.filter(employee=user_employee)

        # Filtering
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        employee_id = self.request.GET.get('employee')
        if employee_id and (self.request.user.is_superuser or (user_employee and user_employee.role in ['ADMIN', 'MANAGER'])):
            queryset = queryset.filter(employee_id=employee_id)

        start_date = self.request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        end_date = self.request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset.select_related('project', 'employee__user').order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_employee = getattr(self.request.user, 'employee', None)

        if self.request.user.is_superuser or (user_employee and user_employee.role in ['ADMIN', 'MANAGER']):
            context['all_employees'] = Employee.objects.select_related('user').all()
            context['all_projects'] = Project.objects.all()
        elif user_employee:
            context['all_projects'] = Project.objects.filter(allocations__employee=user_employee).distinct()
        else:
            context['all_projects'] = Project.objects.none()

        return context

class TimesheetCreateView(LoginRequiredMixin, AjaxTemplateMixin, CreateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('timesheet_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = getattr(self.request.user, 'employee', None)
        return kwargs

    def form_valid(self, form):
        form.instance.employee = getattr(self.request.user, 'employee', None)
        return super().form_valid(form)

class TimesheetUpdateView(LoginRequiredMixin, UserPassesTestMixin, AjaxTemplateMixin, UpdateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('timesheet_list')

    def test_func(self):
        obj = self.get_object()
        user_employee = getattr(self.request.user, 'employee', None)
        if self.request.user.is_superuser:
            return True
        if not user_employee:
            return False
        return obj.employee == user_employee or user_employee.role in ['ADMIN', 'MANAGER']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = getattr(self.request.user, 'employee', None)
        return kwargs

class TimesheetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TimesheetEntry
    template_name = 'timesheet/entry_confirm_delete.html'
    success_url = reverse_lazy('timesheet_list')

    def test_func(self):
        obj = self.get_object()
        user_employee = getattr(self.request.user, 'employee', None)
        if self.request.user.is_superuser:
            return True
        if not user_employee:
            return False
        return obj.employee == user_employee or user_employee.role in ['ADMIN', 'MANAGER']

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

def csrf_failure(request, reason=""):
    return render(request, 'timesheet/csrf_failure.html', {'reason': reason}, status=403)
