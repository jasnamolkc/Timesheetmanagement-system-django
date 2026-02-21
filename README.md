# Timesheet Management System

A production-ready Timesheet Management System built with Django and Tailwind CSS.

## Features

- **Authentication:** Login, Logout, and User Registration.
- **Role-Based Access:** Admin, Manager, and Employee roles.
- **Projects Module:** Create, edit, and archive projects with status tracking.
- **Project Allocation:** Allocate employees to projects with percentage tracking and over-allocation prevention.
- **Timesheet Module:** Log hours against allocated projects with date and project filtering.
- **Reporting:** Project-wise and employee-wise hour breakdowns with CSV export.
- **Dashboard:** Quick overview of active projects, monthly hours, and employee allocations.
- **Modern UI:** Clean card-based layout with a dark navy theme (#0f172a).

## Production Setup Instructions

### 1. Database Configuration (PostgreSQL)

To use PostgreSQL in production, update the `DATABASES` setting in `timesheet_system/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Security

- Change the `SECRET_KEY` in `settings.py` to a secure, environment-specific value.
- Set `DEBUG = False` in production.
- Configure `ALLOWED_HOSTS`.

### 3. Dependencies

Install the required packages:

```bash
pip install django django-crispy-forms crispy-tailwind django-filter django-bootstrap5
```

### 4. Migrations

Run migrations to set up the database:

```bash
python manage.py migrate
```

## User Roles

- **Employee:** Can log timesheets for projects they are allocated to. Can see their own dashboard.
- **Manager:** Can manage projects and allocations. Can view reports and all timesheets.
- **Admin:** Full access to the system, including user management via the Django Admin panel.

---
Built with ❤️ using Django and Tailwind CSS.
