from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponse
import pandas as pd
from datetime import datetime, timedelta

from .models import Project, ProjectAllocation, TimesheetEntry, Employee
from .forms import ProjectForm, AllocationForm, TimesheetEntryForm

# Permission Mixins
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'employee') and self.request.user.employee.role == 'ADMIN'

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'employee') and self.request.user.employee.role in ['ADMIN', 'MANAGER']

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

        if self.request.user.employee.role in ['ADMIN', 'MANAGER']:
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

class ProjectCreateView(ManagerRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/modal_form.html'
    success_url = reverse_lazy('project_list')

class ProjectUpdateView(ManagerRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'timesheet/modal_form.html'
    success_url = reverse_lazy('project_list')

# Allocation Views
class AllocationListView(ManagerRequiredMixin, ListView):
    model = ProjectAllocation
    template_name = 'timesheet/allocation_list.html'
    context_object_name = 'allocations'

    def get_queryset(self):
        return super().get_queryset().select_related('employee__user', 'project')

class AllocationCreateView(ManagerRequiredMixin, CreateView):
    model = ProjectAllocation
    form_class = AllocationForm
    template_name = 'timesheet/modal_form.html'
    success_url = reverse_lazy('allocation_list')

class AllocationUpdateView(ManagerRequiredMixin, UpdateView):
    model = ProjectAllocation
    form_class = AllocationForm
    template_name = 'timesheet/modal_form.html'
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
        if self.request.user.employee.role == 'EMPLOYEE':
            queryset = queryset.filter(employee=self.request.user.employee)

        # Filtering
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset.order_by('-date')

class TimesheetCreateView(LoginRequiredMixin, CreateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/modal_form.html'
    success_url = reverse_lazy('timesheet_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.request.user.employee
        return kwargs

    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        return super().form_valid(form)

class TimesheetUpdateView(LoginRequiredMixin, UpdateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/modal_form.html'
    success_url = reverse_lazy('timesheet_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employee'] = self.object.employee
        return kwargs

class TimesheetDeleteView(LoginRequiredMixin, DeleteView):
    model = TimesheetEntry
    template_name = 'timesheet/entry_confirm_delete.html'
    success_url = reverse_lazy('timesheet_list')

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

        entries = TimesheetEntry.objects.filter(date__range=[start_date, end_date]).values(
            'date', 'employee__user__username', 'project__project_code', 'hours', 'description', 'billable'
        )

        df = pd.DataFrame(list(entries))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="timesheet_report_{start_date}_{end_date}.csv"'

        df.to_csv(path_or_buf=response, index=False)
        return response
