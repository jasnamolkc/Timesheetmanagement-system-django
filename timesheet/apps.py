from django.apps import AppConfig


class TimesheetConfig(AppConfig):
    name = "timesheet"

    def ready(self):
        import timesheet.signals
