from django.contrib import admin
from django.utils.html import format_html
from .models import *


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'employee_code',
        'employee_id',
        'status',
        'is_active'
    )

    list_filter = (
        'role',
        'status',
        'is_active'
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'employee_code',
        'employee_id'
    )

    raw_id_fields = ('user',)
    readonly_fields = ('employee_code',)


# ---------------- PROJECT ---------------- #
class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1

    readonly_fields = ("file_preview",)

    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">View</a>',
                obj.file.url
            )
        return "-"
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'project_code',
        'status',
        'start_date',
        'end_date',
        'allocated_employees_count',
        'progress',
        'milestone_progress'
    )

    list_filter = (
        'status',
        'start_date',
        'is_archived'
    )

    search_fields = (
        'name',
        'project_code',
        'description'
    )

    ordering = ('-start_date',)
    inlines = [DocumentInline]   # 🔥 ADD THIS


# ---------------- PROJECT ALLOCATION ---------------- #

@admin.register(ProjectAllocation)
class ProjectAllocationAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'project',
        'allocation_percentage',
        'role_in_project',
        'start_date',
        'end_date'
    )

    list_filter = (
        'project',
        'employee',
        'start_date'
    )

    search_fields = (
        'employee__user__username',
        'project__project_code',
        'role_in_project'
    )

    autocomplete_fields = (
        'employee',
        'project'
    )


# ---------------- MILESTONE ---------------- #

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'project',
        'status',
        'start_date',
        'due_date',
        'task_count',
        'progress'
    )

    list_filter = (
        'project',
        'status',
        'start_date',
        'due_date'
    )

    search_fields = (
        'name',
        'project__name',
        'project__project_code'
    )

    autocomplete_fields = ('project',)

    def task_count(self, obj):
        return obj.tasks.count()

    task_count.short_description = "Tasks"


# ---------------- TASK IMAGE INLINE ---------------- #

class TaskImageInline(admin.TabularInline):

    model = TaskImage
    extra = 1

    readonly_fields = ("preview",)

    def preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="100"/>',
                obj.image.url
            )

        return "No Image"


# ---------------- TASK ---------------- #

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'project',
        'milestone',
        'assigned_to',
        'status',
        'estimated_hours',
        'created_at'
    )

    list_filter = (
        'status',
        'project',
        'milestone'
    )

    search_fields = (
        'title',
        'description',
        'project__project_code'
    )

    autocomplete_fields = (
        'project',
        'milestone',
        'assigned_to'
    )

    inlines = [TaskImageInline]


# ---------------- TIMESHEET ---------------- #

@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'project',
        'task',
        'date',
        'hours',
        'billable'
    )

    list_filter = (
        'billable',
        'date',
        'project',
        'employee'
    )

    search_fields = (
        'description',
        'task__title',
        'employee__user__username',
        'project__project_code'
    )

    date_hierarchy = 'date'

    autocomplete_fields = (
        'employee',
        'project',
        'task'
    )
@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):

    list_display = (
        "task",
        "preview",
        "uploaded_at",
    )

    list_filter = (
        "task__project",
        "uploaded_at",
    )

    search_fields = (
        "task__title",
        "task__project__name",
    )

    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="120" style="border-radius:6px"/>',
                obj.image.url
            )
        return "No Image"

    preview.short_description = "Image Preview"
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "project",
        "file_preview",
        "uploaded_at",
    )

    list_filter = (
        "project",
        "uploaded_at",
    )

    search_fields = (
        "name",
        "project__name",
        "project__project_code",
    )

    autocomplete_fields = ("project",)

    readonly_fields = ("file_preview",)

    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">View File</a>',
                obj.file.url
            )
        return "No File"

    file_preview.short_description = "Preview"
# @admin.register(Poster)
# class PosterAdmin(admin.ModelAdmin):

#     list_display = (
#         'title',
#         'preview_instagram',
#         'preview_whatsapp',
#         'preview_facebook',
#         'created_at'
#     )

#     search_fields = ('title',)

#     readonly_fields = (
#         'preview_instagram',
#         'preview_whatsapp',
#         'preview_facebook',
#     )

#     fields = (
#         'title',
#         'logo',
#         'content_image',
#         'preview_instagram',
#         'preview_whatsapp',
#         'preview_facebook',
#     )

#     # 🔥 Instagram Preview
#     def preview_instagram(self, obj):
#         if obj.instagram_image:
#             return format_html(
#                 '<img src="{}" width="120" style="border-radius:8px"/>',
#                 obj.instagram_image.url
#             )
#         return "No Image"

#     preview_instagram.short_description = "Instagram"

#     # 🔥 WhatsApp Preview
#     def preview_whatsapp(self, obj):
#         if obj.whatsapp_image:
#             return format_html(
#                 '<img src="{}" width="120" style="border-radius:8px"/>',
#                 obj.whatsapp_image.url
#             )
#         return "No Image"

#     preview_whatsapp.short_description = "WhatsApp"

#     # 🔥 Facebook Preview
#     def preview_facebook(self, obj):
#         if obj.facebook_image:
#             return format_html(
#                 '<img src="{}" width="120" style="border-radius:8px"/>',
#                 obj.facebook_image.url
#             )
#         return "No Image"

#     preview_facebook.short_description = "Facebook"
from django.contrib import admin
from django.utils.html import format_html
from .models import Poster


@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'type_display',
        'preview_instagram',
        'preview_thumbnail',   # ✅ NEW
        'created_at'
    )

    readonly_fields = (
        'preview_instagram',
        'preview_whatsapp',
        'preview_facebook',
        'preview_thumbnail',   # ✅ NEW
    )

    fields = (
        'title',
        'logo',
        'content_image',
        'content_video',

        # Image previews
        'preview_instagram',
        'preview_whatsapp',
        'preview_facebook',

        # ✅ Thumbnail preview
        'preview_thumbnail',
    )

    search_fields = ('title',)

    # ---------------- TYPE ---------------- #
    def type_display(self, obj):
        return "🎬 Video" if obj.content_video else "🖼 Image"
    type_display.short_description = "Type"

    # ---------------- IMAGE PREVIEWS ---------------- #

    def preview_instagram(self, obj):
        if obj.instagram_image:
            return format_html(
                '<img src="{}" width="120" style="border-radius:8px"/>',
                obj.instagram_image.url
            )
        return "No Image"
    preview_instagram.short_description = "Instagram"

    def preview_whatsapp(self, obj):
        if obj.whatsapp_image:
            return format_html(
                '<img src="{}" width="120" style="border-radius:8px"/>',
                obj.whatsapp_image.url
            )
        return "No Image"
    preview_whatsapp.short_description = "WhatsApp"

    def preview_facebook(self, obj):
        if obj.facebook_image:
            return format_html(
                '<img src="{}" width="120" style="border-radius:8px"/>',
                obj.facebook_image.url
            )
        return "No Image"
    preview_facebook.short_description = "Facebook"

    # ---------------- 🔥 VIDEO THUMBNAIL ---------------- #

    def preview_thumbnail(self, obj):
        if obj.video_thumbnail:
            return format_html(
                '''
                <div style="position:relative; display:inline-block;">
                    <img src="{}" width="120" style="border-radius:8px"/>
                    <span style="
                        position:absolute;
                        top:50%;
                        left:50%;
                        transform:translate(-50%, -50%);
                        font-size:20px;
                        color:white;
                        background:rgba(0,0,0,0.5);
                        border-radius:50%;
                        padding:6px 10px;">
                        ▶
                    </span>
                </div>
                ''',
                obj.video_thumbnail.url
            )
        return "No Thumbnail"

    preview_thumbnail.short_description = "Video Thumbnail"