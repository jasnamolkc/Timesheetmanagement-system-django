from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from timesheet.models import Employee, Project, ProjectAllocation, TimesheetEntry
from django.utils import timezone
from datetime import timedelta

class ProjectModuleTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.admin_employee = self.admin_user.employee
        self.admin_employee.role = 'ADMIN'
        self.admin_employee.save()

        self.employee_user = User.objects.create_user(username='employee', password='password')
        self.employee = self.employee_user.employee

        self.client = Client()

    def test_project_date_validation(self):
        # Admin can create project
        self.client.login(username='admin', password='password')

        # Valid project
        project = Project(
            name='Valid Project',
            project_code='VAL001',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=10)
        )
        project.full_clean() # Should not raise

        # Invalid project (end before start)
        invalid_project = Project(
            name='Invalid Project',
            project_code='INV001',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() - timedelta(days=1)
        )
        with self.assertRaises(Exception): # ValidationError
            invalid_project.full_clean()

    def test_project_archiving(self):
        self.client.login(username='admin', password='password')

        project = Project.objects.create(
            name='Archive Me',
            project_code='ARC001',
            start_date=timezone.now().date()
        )

        # Archive via POST
        response = self.client.post(reverse('project_archive', args=[project.pk]))
        self.assertEqual(response.status_code, 302)

        project.refresh_from_db()
        self.assertTrue(project.is_archived)

        # Unarchive
        self.client.post(reverse('project_archive', args=[project.pk]))
        project.refresh_from_db()
        self.assertFalse(project.is_archived)

    def test_project_list_filtering(self):
        self.client.login(username='admin', password='password')

        Project.objects.create(name='Active Project', project_code='ACT001', start_date=timezone.now().date(), is_archived=False)
        Project.objects.create(name='Archived Project', project_code='ARC002', start_date=timezone.now().date(), is_archived=True)

        # Default list (active only)
        response = self.client.get(reverse('project_list'))
        self.assertEqual(len(response.context['projects']), 1)
        self.assertEqual(response.context['projects'][0].name, 'Active Project')

        # Archived list
        response = self.client.get(reverse('project_list') + '?archived=1')
        self.assertEqual(len(response.context['projects']), 1)
        self.assertEqual(response.context['projects'][0].name, 'Archived Project')

    def test_archived_project_not_in_forms(self):
        self.client.login(username='admin', password='password')

        active_project = Project.objects.create(name='Active', project_code='ACT', start_date=timezone.now().date())
        archived_project = Project.objects.create(name='Archived', project_code='ARC', start_date=timezone.now().date(), is_archived=True)

        # AllocationForm should not show archived project
        from timesheet.forms import AllocationForm
        form = AllocationForm()
        self.assertIn(active_project, form.fields['project'].queryset)
        self.assertNotIn(archived_project, form.fields['project'].queryset)

        # TimesheetEntryForm should not show archived project
        # First allocate employee to both
        ProjectAllocation.objects.create(
            employee=self.employee, project=active_project, allocation_percentage=50,
            role_in_project='Dev', start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=10)
        )
        ProjectAllocation.objects.create(
            employee=self.employee, project=archived_project, allocation_percentage=50,
            role_in_project='Dev', start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=10)
        )

        from timesheet.forms import TimesheetEntryForm
        form = TimesheetEntryForm(employee=self.employee)
        self.assertIn(active_project, form.fields['project'].queryset)
        self.assertNotIn(archived_project, form.fields['project'].queryset)

    def test_employee_project_visibility(self):
        # Create two projects
        p1 = Project.objects.create(name='Project 1', project_code='P1', start_date=timezone.now().date())
        p2 = Project.objects.create(name='Project 2', project_code='P2', start_date=timezone.now().date())

        # Allocate employee only to Project 1
        ProjectAllocation.objects.create(
            employee=self.employee, project=p1, allocation_percentage=50,
            role_in_project='Dev', start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=10)
        )

        # Login as employee
        self.client.login(username='employee', password='password')

        # Employee should only see Project 1
        response = self.client.get(reverse('project_list'))
        self.assertEqual(len(response.context['projects']), 1)
        self.assertEqual(response.context['projects'][0].name, 'Project 1')

        # Admin should see both
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('project_list'))
        # Both projects are active, so admin sees both
        self.assertEqual(len(response.context['projects']), 2)
