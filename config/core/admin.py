from django.contrib import admin
from .models import Organization, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username" ,"organization")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Organization", {"fields": ("organization",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Organization", {"fields": ("organization",)}),
    )