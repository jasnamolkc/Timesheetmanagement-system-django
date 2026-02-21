from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.models import User
import csv
from datetime import datetime, timedelta

from .models import Project, ProjectAllocation, TimesheetEntry, Employee
from .forms import ProjectForm, AllocationForm, TimesheetEntryForm, RegistrationForm
from .permissions import AdminRequiredMixin, ManagerRequiredMixin, EmployeeRequiredMixin

# Auth Views - Central Dashboard Redirection
class DashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'employee'):
            return HttpResponse("Employee profile missing. Please contact admin.", status=403)

        role = request.user.employee.role
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'manager':
            return redirect('manager_dashboard')
        else:
            return redirect('employee_dashboard')

# Admin Views
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'timesheet/dashboard/admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_projects'] = Project.objects.filter(status='ACTIVE').count()
        context['total_hours_month'] = TimesheetEntry.objects.filter(
            date__month=timezone.now().month
        ).aggregate(Sum('hours'))['hours__sum'] or 0
        return context

# Manager Views
class ManagerDashboardView(ManagerRequiredMixin, TemplateView):
    template_name = 'timesheet/dashboard/manager.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_allocations'] = ProjectAllocation.objects.count()
        context['active_projects'] = Project.objects.filter(status='ACTIVE').count()
        return context

# Employee Views
class EmployeeDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'timesheet/dashboard/employee.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.request.user.employee
        context['my_hours_month'] = TimesheetEntry.objects.filter(
            employee=employee,
            date__month=timezone.now().month
        ).aggregate(Sum('hours'))['hours__sum'] or 0
        context['my_projects'] = ProjectAllocation.objects.filter(
            employee=employee,
            end_date__gte=timezone.now().date()
        ).count()
        return context

# Project Views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'timesheet/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

class AjaxTemplateMixin:
    def get_template_names(self):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('modal'):
            return ['timesheet/modal_form.html']
        return [self.template_name]

class ProjectCreateView(AdminRequiredMixin, AjaxTemplateMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('project_list')

class ProjectUpdateView(AdminRequiredMixin, AjaxTemplateMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('project_list')

# User Management (Admin Only)
class UserListView(AdminRequiredMixin, ListView):
    model = Employee
    template_name = 'timesheet/admin/user_list.html'
    context_object_name = 'employees'

class UserCreateView(AdminRequiredMixin, AjaxTemplateMixin, CreateView):
    form_class = RegistrationForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('user_list')

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
        user_employee = self.request.user.employee

        if user_employee.role == 'employee':
            queryset = queryset.filter(employee=user_employee)

        # Filtering
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        employee_id = self.request.GET.get('employee')
        if employee_id and user_employee.role in ['admin', 'manager']:
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
        user_employee = self.request.user.employee

        if user_employee.role in ['admin', 'manager']:
            context['all_employees'] = Employee.objects.select_related('user').all()
            context['all_projects'] = Project.objects.all()
        else:
            context['all_projects'] = Project.objects.filter(allocations__employee=user_employee).distinct()

        return context

class TimesheetCreateView(LoginRequiredMixin, AjaxTemplateMixin, CreateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('timesheet_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.request.user.employee
        return kwargs

    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        return super().form_valid(form)

class TimesheetUpdateView(LoginRequiredMixin, UserPassesTestMixin, AjaxTemplateMixin, UpdateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('timesheet_list')

    def test_func(self):
        obj = self.get_object()
        return obj.employee == self.request.user.employee or self.request.user.employee.role in ['admin', 'manager']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.request.user.employee
        return kwargs

class TimesheetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TimesheetEntry
    template_name = 'timesheet/entry_confirm_delete.html'
    success_url = reverse_lazy('timesheet_list')

    def test_func(self):
        obj = self.get_object()
        return obj.employee == self.request.user.employee or self.request.user.employee.role in ['admin', 'manager']

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
            billable_hours=Sum('hours', filter=Q(billable=True)),
            non_billable_hours=Sum('hours', filter=Q(billable=False))
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
