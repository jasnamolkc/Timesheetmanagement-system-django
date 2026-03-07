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

        if self.request.user.employee.role in ['ADMIN', 'MANAGER']:
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
            print(context)
        return context

# Project Views
# class ProjectListView(LoginRequiredMixin, ListView):
#     model = Project
#     template_name = 'timesheet/project_list.html'
#     context_object_name = 'projects'
#     paginate_by = 10
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'timesheet/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        user_employee = self.request.user.employee
        print(self.request.user.username)
        show_archived = self.request.GET.get('archived')
        # queryset = Project.objects.annotate(
        #     allocated_employees_count=Count('allocations', distinct=True)
        # )
        queryset = Project.objects.all()   # ✅ remove annotate

        # Employee → only ACTIVE and not archived
        if user_employee.role == 'EMPLOYEE':
            queryset = queryset.filter(
                status='ACTIVE',
                is_archived=False
            )

        else:
            if show_archived:
                queryset = queryset.filter(is_archived=True)
            else:
                queryset = queryset.filter(is_archived=False)

        return queryset
        
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
class TimesheetListView(LoginRequiredMixin, ListView):
    model = TimesheetEntry
    template_name = 'timesheet/timesheet_list.html'
    context_object_name = 'entries'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        user_employee = getattr(user, "employee", None)

        queryset = TimesheetEntry.objects.select_related(
            'project',
            'employee__user'
        )

        # Employee restriction
        if user_employee and user_employee.role == 'EMPLOYEE':
            queryset = queryset.filter(employee=user_employee)

        # Filters
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        employee_id = self.request.GET.get('employee')
        if employee_id and user_employee and user_employee.role in ['ADMIN', 'MANAGER']:
            queryset = queryset.filter(employee_id=employee_id)

        start_date = self.request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        end_date = self.request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_employee = getattr(user, "employee", None)

        # Permission flag (clean template usage)
        context["can_manage"] = (
            user.is_superuser or
            (user_employee and user_employee.role in ['ADMIN', 'MANAGER'])
        )

        # Employee & Project filter lists
        if context["can_manage"]:
            context['all_employees'] = Employee.objects.select_related('user').all()
            context['all_projects'] = Project.objects.filter(is_archived=False)
        else:
            context['all_projects'] = Project.objects.filter(
                allocations__employee=user_employee,
                is_archived=False
            ).distinct()

        # Total Hours
        context['total_hours'] = self.get_queryset().aggregate(
            total=Sum('hours')
        )['total'] or 0

        return context


# =========================
# CREATE
# =========================
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
#         return super().form_valid(form)

from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import redirect

class TimesheetCreateView(LoginRequiredMixin, CreateView):
    model = TimesheetEntry
    form_class = TimesheetEntryForm
    template_name = 'timesheet/form_page.html'
    success_url = reverse_lazy('timesheet_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_employee = getattr(self.request.user, "employee", None)
        if user_employee:
            kwargs['employee'] = user_employee
        return kwargs

    def form_valid(self, form):
        user_employee = getattr(self.request.user, "employee", None)
        if user_employee:
            form.instance.employee = user_employee

        self.object = form.save()

        # ✅ If AJAX → return JSON success
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"success": True})

        return redirect(self.success_url)

    def form_invalid(self, form):
        # ✅ If AJAX → return form HTML again
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                "timesheet/modal_form.html",
                {"form": form},
                request=self.request
            )
            return JsonResponse({"html": html}, status=400)

        return super().form_invalid(form)

    def get_template_names(self):
        # ✅ If AJAX → return only modal form
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return ["timesheet/modal_form.html"]

        return [self.template_name]
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
