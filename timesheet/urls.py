from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Projects
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),

    # Allocations
    path('allocations/', views.AllocationListView.as_view(), name='allocation_list'),
    path('allocations/create/', views.AllocationCreateView.as_view(), name='allocation_create'),
    path('allocations/<int:pk>/edit/', views.AllocationUpdateView.as_view(), name='allocation_edit'),
    path('allocations/<int:pk>/delete/', views.AllocationDeleteView.as_view(), name='allocation_delete'),

    # Timesheets
    path('timesheets/', views.TimesheetListView.as_view(), name='timesheet_list'),
    path('timesheets/create/', views.TimesheetCreateView.as_view(), name='timesheet_create'),
    path('timesheets/<int:pk>/edit/', views.TimesheetUpdateView.as_view(), name='timesheet_edit'),
    path('timesheets/<int:pk>/delete/', views.TimesheetDeleteView.as_view(), name='timesheet_delete'),

    # Reports
    path('reports/', views.SummaryReportView.as_view(), name='summary_report'),
    path('reports/export/', views.ExportCSVView.as_view(), name='export_csv'),
]
