from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from timesheet.models import Employee, Project, ProjectAllocation, TimesheetEntry
from django.utils import timezone
from datetime import date, timedelta
from django.core.exceptions import ValidationError

class TimesheetModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='emp1', password='password')
        self.employee = self.user.employee

        self.project = Project.objects.create(name='P1', project_code='P1', start_date=date(2026, 1, 1))

        # Allocate emp1 to P1 for Jan 2026
        ProjectAllocation.objects.create(
            employee=self.employee, project=self.project, allocation_percentage=100,
            role_in_project='Dev', start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
        )

    def test_logging_within_allocation(self):
        entry = TimesheetEntry(
            employee=self.employee, project=self.project,
            date=date(2026, 1, 15), hours=8, description='Working'
        )
        entry.full_clean() # Should pass
        entry.save()

    def test_logging_outside_allocation(self):
        # logging on Feb 1st (not allocated)
        entry = TimesheetEntry(
            employee=self.employee, project=self.project,
            date=date(2026, 2, 1), hours=8, description='Working'
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_logging_for_archived_project(self):
        self.project.is_archived = True
        self.project.save()

        entry = TimesheetEntry(
            employee=self.employee, project=self.project,
            date=date(2026, 1, 15), hours=8, description='Working'
        )
        with self.assertRaises(ValidationError) as cm:
            entry.full_clean()
        self.assertIn("archived", str(cm.exception))

    def test_timesheet_list_filtering(self):
        # Create some entries
        TimesheetEntry.objects.create(
            employee=self.employee, project=self.project,
            date=date(2026, 1, 10), hours=4, description='Day 1'
        )
        TimesheetEntry.objects.create(
            employee=self.employee, project=self.project,
            date=date(2026, 1, 20), hours=6, description='Day 2'
        )

        client = Client()
        client.login(username='emp1', password='password')

        # All entries
        response = client.get(reverse('timesheet_list'))
        self.assertEqual(len(response.context['entries']), 2)

        # Date filter
        response = client.get(reverse('timesheet_list') + '?start_date=2026-01-15')
        self.assertEqual(len(response.context['entries']), 1)
        self.assertEqual(response.context['entries'][0].description, 'Day 2')
