from django.test import TestCase
from django.contrib.auth.models import User
from timesheet.models import Employee, Project, ProjectAllocation
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta

class AllocationModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='emp1', password='password')
        self.employee = self.user.employee

        self.project1 = Project.objects.create(name='P1', project_code='P1', start_date=date(2026, 1, 1))
        self.project2 = Project.objects.create(name='P2', project_code='P2', start_date=date(2026, 1, 1))
        self.project3 = Project.objects.create(name='P3', project_code='P3', start_date=date(2026, 1, 1))

    def test_allocation_overlap_complex(self):
        # Alloc 1: Jan 1 to Jan 20 (60%)
        ProjectAllocation.objects.create(
            employee=self.employee, project=self.project1, allocation_percentage=60,
            role_in_project='Dev', start_date=date(2026, 1, 1), end_date=date(2026, 1, 20)
        )

        # Alloc 2: Jan 15 to Jan 31 (50%)
        # This overlaps with Alloc 1 from Jan 15-20. Total = 110%
        alloc2 = ProjectAllocation(
            employee=self.employee, project=self.project2, allocation_percentage=50,
            role_in_project='Dev', start_date=date(2026, 1, 15), end_date=date(2026, 1, 31)
        )
        with self.assertRaises(ValidationError) as cm:
            alloc2.full_clean()
        self.assertIn("Total allocation on 2026-01-15 would be 110.00%", str(cm.exception))

        # Alloc 3: Jan 21 to Jan 31 (50%) - Should be OK
        ProjectAllocation.objects.create(
            employee=self.employee, project=self.project2, allocation_percentage=50,
            role_in_project='Dev', start_date=date(2026, 1, 21), end_date=date(2026, 1, 31)
        )

        # New Alloc 4: Jan 10 to Jan 25 (30%)
        # Overlaps with Alloc 1 (Jan 10-20) -> 60 + 30 = 90% (OK)
        # Overlaps with Alloc 3 (Jan 21-25) -> 50 + 30 = 80% (OK)
        # Should pass
        alloc4 = ProjectAllocation(
            employee=self.employee, project=self.project3, allocation_percentage=30,
            role_in_project='Lead', start_date=date(2026, 1, 10), end_date=date(2026, 1, 25)
        )
        alloc4.full_clean()
        alloc4.save()

        # Try to increase Alloc 4 to 50%
        # Jan 10-20: 60 + 50 = 110% (Fail)
        alloc4.allocation_percentage = 50
        with self.assertRaises(ValidationError):
            alloc4.full_clean()

    def test_date_validation(self):
        alloc = ProjectAllocation(
            employee=self.employee, project=self.project1, allocation_percentage=50,
            role_in_project='Dev', start_date=date(2026, 1, 10), end_date=date(2026, 1, 5)
        )
        with self.assertRaises(ValidationError):
            alloc.full_clean()

    def test_allocation_update_self_exclude(self):
        # Create an allocation of 100%
        alloc = ProjectAllocation.objects.create(
            employee=self.employee, project=self.project1, allocation_percentage=100,
            role_in_project='Dev', start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
        )

        # Updating it (e.g. changing role) should not trigger >100% error with itself
        alloc.role_in_project = 'Lead'
        alloc.full_clean() # Should not raise
