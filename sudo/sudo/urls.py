"""
URL configuration for sudo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from sudo.views import *

urlpatterns = [
    # ── Admin ─────────────────────────────────
    path('admin/', admin.site.urls),

    # ── Template / HTML views ──────────────────
    path('', home, name='home'),
    path('home/', home, name='home'),
    path('employees/', emplist, name='emplist'),
    path('add_employee/', emp_form, name='emp_form'),
    path('edit_employee/<int:emp_id>/', edit_emp, name='edit_emp'),
    path('delete_employee/<int:emp_id>/', delete_emp, name='delete_emp'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),

    # ── REST API endpoints (DRF APIView) ────────
    path('api/register/', RegisterAPIView.as_view(), name='api_register'),
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
    path('api/refresh/', RefreshAPIView.as_view(), name='api_refresh'),
    path('api/employees/', EmployeeListCreateAPIView.as_view(), name='api_employee_list'),
    path('api/employees/<int:emp_id>/', EmployeeDetailAPIView.as_view(), name='api_employee_detail'),
]
