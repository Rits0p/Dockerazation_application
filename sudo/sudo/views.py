from django.shortcuts import render
from django.http import HttpResponse 
from .models import Employee  
from django.contrib import messages
from django.shortcuts import redirect 

def home(request):
    return render(request,'home.html')

def emplist(request):
    employee=  Employee.objects.all()
    context = {'employee': employee}

    return render(request,'emplist.html',context)

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

def delete_emp(request, emp_id):
    employee = Employee.objects.get(id=emp_id)
    employee.delete()
    messages.success(request, 'Employee deleted successfully.')
    return redirect('emplist')

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