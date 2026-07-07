from django.shortcuts import render
from django.http import HttpResponse 
from .models import *
from django.contrib import messages
from django.shortcuts import redirect 
from functools import wraps
import jwt
from django.conf import settings
from datetime import datetime, timedelta, timezone
from .serializer import *

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



# ─────────────────────────────────────────────
#  REST API Views (DRF APIView)
# ─────────────────────────────────────────────
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from django.core.cache import cache


def jwt_required(func):
    """
    Decorator for APIView methods that validates the
    'Authorization: Bearer <access_token>' header using JWT.
    On success it attaches `request.api_user_id` to the request object.
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'Authorization header missing or malformed. Use: Bearer <token>'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'access':
                raise jwt.InvalidTokenError('Not an access token')
            request.api_user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Access token expired.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid access token.'}, status=status.HTTP_401_UNAUTHORIZED)
        return func(self, request, *args, **kwargs)
    return wrapper


# ── Auth APIs ─────────────────────────────────

from rest_framework.decorators import action

class AuthViewSet(viewsets.ViewSet):
    """
    Auth endpoints for register, login, and refresh.
    """

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            if user.objects.filter(email=email).exists():
                return Response(
                    {'error': 'A user with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(
                {'message': 'Registration successful.', 'user': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Both username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_obj = user.objects.filter(username=username, password=password).first()
        if not user_obj:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Issue a short-lived access token (15 minutes)
        access_payload = {
            'user_id': user_obj.id,
            'type': 'access',
            'exp': datetime.now(timezone.utc) + timedelta(minutes=15),
            'iat': datetime.now(timezone.utc),
        }
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

        # Issue a long-lived refresh token (7 days)
        refresh_payload = {
            'user_id': user_obj.id,
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) + timedelta(days=7),
            'iat': datetime.now(timezone.utc),
        }
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({
            'message': 'Login successful.',
            'access_token': access_token,
            'refresh_token': refresh_token,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'refresh_token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'refresh':
                raise jwt.InvalidTokenError('Not a refresh token')
            
            user_id = payload.get('user_id')
            
            # Issue a new short-lived access token (15 minutes)
            access_payload = {
                'user_id': user_id,
                'type': 'access',
                'exp': datetime.now(timezone.utc) + timedelta(minutes=15),
                'iat': datetime.now(timezone.utc),
            }
            new_access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
            
            return Response({
                'message': 'Token refreshed successfully.',
                'access_token': new_access_token
            }, status=status.HTTP_200_OK)
            
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token expired. Please log in again.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)


# ── Employee APIs ──────────────────────────────



class EmployeeViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing, retrieving, creating, updating and deleting employees.
    (JWT required for all endpoints)
    """

    def _get_employee(self, emp_id):
        try:
            return Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return None

    @jwt_required
    def list(self, request):
        # 1. Try to get data from Redis cache
        cached_employees = cache.get('all_employees_data')

        if cached_employees:
            return Response(cached_employees, status=status.HTTP_200_OK)
            
        # 2. If not in cache, fetch from database
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        
        # 3. Save the result to cache for 5 minutes (300 seconds)
        cache.set('all_employees_data', serializer.data, timeout=300)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @jwt_required
    def create(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            if Employee.objects.filter(email=email).exists():
                return Response(
                    {'error': 'An employee with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(
                {'message': 'Employee created successfully.', 'employee': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @jwt_required
    def retrieve(self, request, pk=None):
        employee = self._get_employee(pk)
        if not employee:
            return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @jwt_required
    def update(self, request, pk=None):
        employee = self._get_employee(pk)
        if not employee:
            return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Employee updated successfully.', 'employee': serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @jwt_required
    def destroy(self, request, pk=None):
        employee = self._get_employee(pk)
        if not employee:
            return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        employee.delete()
        return Response({'message': 'Employee deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
