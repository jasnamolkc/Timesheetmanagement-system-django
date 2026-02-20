from django.test import TestCase
from django.contrib.auth.models import User
from timesheet.models import Employee, Project, ProjectAllocation, TimesheetEntry
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class TimesheetModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Employee profile is created by signal
        self.employee = self.user.employee

        self.project = Project.objects.create(
            name='Test Project',
            project_code='TEST001',
            status='ACTIVE',
            start_date=timezone.now().date()
        )

    def test_allocation_validation(self):
        # Create first allocation of 60%
        ProjectAllocation.objects.create(
            employee=self.employee,
            project=self.project,
            allocation_percentage=60,
            role_in_project='Developer',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )

        # Try to create another allocation of 50% for the same period
        # Total would be 110%
        allocation = ProjectAllocation(
            employee=self.employee,
            project=self.project,
            allocation_percentage=50,
            role_in_project='Lead',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )

        with self.assertRaises(ValidationError):
            allocation.full_clean()

    def test_timesheet_allocation_validation(self):
        # No allocation yet
        entry = TimesheetEntry(
            employee=self.employee,
            project=self.project,
            date=timezone.now().date(),
            hours=8,
            description='Test entry'
        )

        with self.assertRaises(ValidationError):
            entry.full_clean()

        # Now allocate
        ProjectAllocation.objects.create(
            employee=self.employee,
            project=self.project,
            allocation_percentage=100,
            role_in_project='Developer',
            start_date=timezone.now().date() - timedelta(days=5),
            end_date=timezone.now().date() + timedelta(days=5)
        )

        # Now it should be valid
        entry.full_clean()
        entry.save()
        self.assertEqual(TimesheetEntry.objects.count(), 1)
