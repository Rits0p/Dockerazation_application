from django.shortcuts import render
from django.http import HttpResponse 
from .models import *
from django.contrib import messages
from django.shortcuts import redirect 
from functools import wraps
from django.core import signing

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        token = request.COOKIES.get('auth_token')
        if not token:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
            
        try:
            # Decode and verify the token (expires in 1 day = 86400 seconds)
            data = signing.loads(token, max_age=86400)
            request.custom_user_id = data.get('user_id')
        except signing.SignatureExpired:
            messages.error(request, 'Your token expired. Please log in again.')
            return redirect('login')
        except signing.BadSignature:
            messages.error(request, 'Invalid token. Please log in.')
            return redirect('login')
            
        return view_func(request, *args, **kwargs)
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
            # Create a stateless token containing the user's ID
            token = signing.dumps({'user_id': user_obj.id})
            
            messages.success(request, 'Login successful.')
            response = redirect('home')
            # Set the token as a cookie in the browser
            response.set_cookie('auth_token', token, httponly=True)
            return response
        else:
            messages.error(request, 'Invalid username or password.')    
    return render(request,'login.html')

def logout(request):
    messages.success(request, 'Logged out successfully.')
    response = redirect('login')
    # Destroy the token to log out
    response.delete_cookie('auth_token')
    return response

