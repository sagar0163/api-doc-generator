from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.user_list),
    path("health/", views.health),
    path("admin/", admin.site.urls),
]