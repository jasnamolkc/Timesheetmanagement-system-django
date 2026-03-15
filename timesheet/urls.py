from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Projects
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/archive/', views.ProjectArchiveView.as_view(), name='project_archive'),
    path('projects/<int:project_id>/allocate/',views.allocate_employee,name='allocate_employee'),

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

    #Employee
    path("employees/", views.EmployeeListView.as_view(), name="employee_list"),
    path("employees/<int:pk>/approve/", views.approve_employee, name="approve_employee"),   
    path("employees-by-project/<int:project_id>/",views.employees_by_project,name="employees_by_project"),

    path("tasks/", views.task_page, name="task_page"),
    path("tasks/list/", views.task_list, name="task_list"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:id>/delete/", views.task_delete, name="task_delete"),
    path("tasks/by-project/<int:project_id>/", views.tasks_by_project, name="tasks_by_project"),

    path("milestones/", views.milestone_list, name="milestone_list"),
    path("milestone/create/", views.milestone_create, name="milestone_create"),
    path("milestone/<int:pk>/edit/", views.milestone_update, name="milestone_update"),
    path("milestone/<int:pk>/delete/", views.milestone_delete, name="milestone_delete"),
    path("milestones-by-project/<int:project_id>/",views.milestones_by_project,name="milestones_by_project"),

    path("delete-task-image/<int:pk>/", views.delete_task_image, name="delete_task_image"),
    
]
