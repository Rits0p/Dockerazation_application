from django.shortcuts import render
from django.http import HttpResponse 
from .models import *
from django.contrib import messages
from django.shortcuts import redirect 
from functools import wraps
import jwt
from django.conf import settings
from datetime import datetime, timedelta, timezone

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        new_access_token = None
        user_id = None

        # 1. Try to validate the Access Token
        if access_token:
            try:
                payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                if payload.get('type') == 'access':
                    user_id = payload.get('user_id')
            except jwt.ExpiredSignatureError:
                pass # Access token expired, we will try the refresh token next
            except jwt.InvalidTokenError:
                pass # Invalid token, ignore and see if refresh token is valid

        # 2. If Access Token failed/expired, try the Refresh Token
        if not user_id and refresh_token:
            try:
                refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
                if refresh_payload.get('type') == 'refresh':
                    user_id = refresh_payload.get('user_id')
                    
                    # Success! Refresh token is valid. Generate a brand new Access Token.
                    new_payload = {
                        'user_id': user_id,
                        'type': 'access',
                        'exp': datetime.now(timezone.utc) + timedelta(minutes=15),
                        'iat': datetime.now(timezone.utc)
                    }
                    new_access_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm='HS256')
            except jwt.ExpiredSignatureError:
                messages.error(request, 'Your session has fully expired. Please log in again.')
                return redirect('login')
            except jwt.InvalidTokenError:
                messages.error(request, 'Invalid refresh mechanism. Please log in.')
                return redirect('login')

        # 3. If everything failed (no valid tokens), redirect to login
        if not user_id:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
            
        request.custom_user_id = user_id
        
        # 4. Finally, execute the View to get the HTTP Response
        response = view_func(request, *args, **kwargs)
        
        # 5. If we generated a new access token, we must inject it into the final response headers!
        if new_access_token:
            response.set_cookie('access_token', new_access_token, httponly=True, max_age=15*60)
            
        return response
    return _wrapped_view

def home(request):
    return render(request,'home.html')

@custom_login_required
def emplist(request):
    employee=  Employee.objects.all()
    context = {'employee': employee}

    return render(request,'emplist.html',context)

@custom_login_required
def edit_emp(request, emp_id):
    employee = Employee.objects.get(id=emp_id)
    if request.method == 'POST':
        employee.name = request.POST.get('name')
        employee.email = request.POST.get('email')
        employee.phone = request.POST.get('phone')
        employee.department = request.POST.get('department')
        employee.save()
        messages.success(request, 'Employee updated successfully.')
        return redirect('emplist') 
    return render(request, 'edit_emplist.html', {'employee': employee})

@custom_login_required
def delete_emp(request, emp_id):
    employee = Employee.objects.get(id=emp_id)
    employee.delete()
    messages.success(request, 'Employee deleted successfully.')
    return redirect('emplist')

@custom_login_required
def emp_form(request):
    if request.method == 'POST':
        # add emp
        email = request.POST.get('email')
        if Employee.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            Employee.objects.create(
                name=request.POST.get('name'),
                email=email,
                phone=request.POST.get('phone'),
                department=request.POST.get('department')
            )
            messages.success(request, 'Employee added successfully.')
            return redirect('emplist')  # Redirect to the employee list view after successful addition

            # return redirect('some_view_name')  # Redirect to a view that shows the employee list or details')
    return render(request, 'add_employee.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if user already exists
        if user.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            # Create new user
            user.objects.create(
                username=username,
                email=email,
                password=password
            )
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    return render(request,'register.html')
                  
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = user.objects.filter(username=username, password=password).first()
        if user_obj:
            # Create a short-lived ACCESS TOKEN (e.g., 15 minutes)
            access_payload = {
                'user_id': user_obj.id,
                'type': 'access',
                'exp': datetime.now(timezone.utc) + timedelta(minutes=15),
                'iat': datetime.now(timezone.utc)
            }
            access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

            # Create a long-lived REFRESH TOKEN (e.g., 7 days)
            refresh_payload = {
                'user_id': user_obj.id,
                'type': 'refresh',
                'exp': datetime.now(timezone.utc) + timedelta(days=7),
                'iat': datetime.now(timezone.utc)
            }
            refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
            
            messages.success(request, 'Login successful.')
            response = redirect('home')
            
            # Plant both tokens safely into the browser with proper cookie lifespans
            response.set_cookie('access_token', access_token, httponly=True, max_age=15*60) # 15 minutes
            response.set_cookie('refresh_token', refresh_token, httponly=True, max_age=7*24*60*60) # 7 days
            return response
        else:
            messages.error(request, 'Invalid username or password.')    
    return render(request,'login.html')

def logout(request):
    messages.success(request, 'Logged out successfully.')
    response = redirect('login')
    # Destroy BOTH tokens to ensure logging out wipes all credentials
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

