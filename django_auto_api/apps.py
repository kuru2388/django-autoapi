# django_auto_api/apps.py
from django.apps import AppConfig


class DjangoAutoApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_auto_api"
    verbose_name = "Django Auto API"
