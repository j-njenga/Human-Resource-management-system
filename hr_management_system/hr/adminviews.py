import json, requests
import logging
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .forms import HODForm
from django.contrib.auth import authenticate, login
from hr.models import Attendance, CustomUser, Department, HOD, FeedBackHOD, FeedBackStaff, LeaveReportHOD, LeaveReportStaff, LeaveRequest, NotificationHOD, NotificationStaff, Project, Staff, Admin, Task
from django.forms import modelform_factory


def admin_home(request):
    hod_count = HOD.objects.all().count()
    staff_count = Staff.objects.all().count()
    department_count = Department.objects.all().count()

    departments = Department.objects.all()
    department_name_list = []
    department_staff_hod_counts = []
    for department in departments:
        hods = HOD.objects.filter(department_id=department.id).count()
        staffs = Staff.objects.filter(department_id=department.id).count()
        department_name_list.append(department.department_name)
        department_staff_hod_counts.append(hods + staffs)

    staffs = Staff.objects.all()
    attendance_present_list_staff = []
    attendance_absent_list_staff = []
    staff_name_list = []
    for staff in staffs:
        attendance_present = Attendance.objects.filter(staff_id=staff.id, status=True).count()
        attendance_absent = Attendance.objects.filter(staff_id=staff.id, status=False).count()
        leaves = LeaveRequest.objects.filter(user=staff.admin, status='Approved').count()
        attendance_present_list_staff.append(attendance_present)
        attendance_absent_list_staff.append(attendance_absent + leaves)
        staff_name_list.append(staff.admin.username)

    hods = HOD.objects.all()
    attendance_present_list_hod = []
    attendance_absent_list_hod = []
    hod_name_list = []
    for hod in hods:
        attendance_present = Attendance.objects.filter(hod_id=hod.id, status=True).count()
        attendance_absent = Attendance.objects.filter(hod_id=hod.id, status=False).count()
        leaves = LeaveRequest.objects.filter(user=hod.admin, status='Approved').count()
        attendance_present_list_hod.append(attendance_present)
        attendance_absent_list_hod.append(attendance_absent + leaves)
        hod_name_list.append(hod.admin.username)

    return render(
        request,
        "admin_template/admin_home.html",
        {
            "hod_count": hod_count,
            "staff_count": staff_count,
            "department_count": department_count,
            "department_name_list": department_name_list,
            "department_staff_hod_counts": department_staff_hod_counts,
            "staff_name_list": staff_name_list,
            "attendance_present_list_staff": attendance_present_list_staff,
            "attendance_absent_list_staff": attendance_absent_list_staff,
            "hod_name_list": hod_name_list,
            "attendance_present_list_hod": attendance_present_list_hod,
            "attendance_absent_list_hod": attendance_absent_list_hod,
        },
    )



def admin_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(
        request,
        "admin_template/admin_profile.html",
        {"user": user},
    )


def admin_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        # password = request.POST.get("password")
        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            # if password!=None and password!="":
            #     customuser.set_password(password)
            customuser.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except Exception:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("admin_profile"))


def add_hod(request):
    if request.method == 'POST':
        form = HODForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new CustomUser instance from the form data
            user = CustomUser(
                email=form.cleaned_data['email'],
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                address=form.cleaned_data['address'],
                user_type=2  # Set the user type to HOD
            )
            user.set_password(form.cleaned_data['password'])  # Set the user's password
            user.save()  # Save the user to the database

            # Create an HOD instance associated with the new CustomUser
            hod = form.save(commit=False)
            hod.admin = user  # Link the HOD to the CustomUser
            hod.save()  # Save the HOD instance to the database
            
            # Optionally log in the HOD after registration
            auth_user = authenticate(username=user.username, password=form.cleaned_data['password'])
            if auth_user is not None:
                login(request, auth_user)
            
            return redirect('manage_hod')  # Redirect to the HOD management page
    else:
        form = HODForm()
    
    return render(request, 'admin_template/add_hod_template.html', {'form': form})


logger = logging.getLogger(__name__)

def edit_hod(request, hod_id):
    try:
        hod = get_object_or_404(HOD, admin__id=hod_id)
    except Exception as e:
        logger.error(f"Error retrieving HOD with ID {hod_id}: {str(e)}")
        messages.error(request, "No HOD matches the given query.")
        return redirect('manage_hod')

    departments = Department.objects.all()

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        address = request.POST.get('address')
        department_id = request.POST.get('department')
        gender = request.POST.get('gender')

        logger.debug(f"Received POST data: email={email}, password={password}, first_name={first_name}, last_name={last_name}, username={username}, address={address}, department_id={department_id}, gender={gender}")

        try:
            user = CustomUser.objects.get(id=hod.admin.id)
            logger.debug(f"Updating HOD: {hod_id}")
            
            user.email = email
            if password:
                user.password = make_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.save()

            hod.address = address
            hod.gender = gender
            hod.department_id = department_id
            hod.save()

            messages.success(request, "HOD updated successfully!")
            logger.info(f"HOD {hod_id} updated successfully.")
            return redirect('manage_hod')
        except Exception as e:
            logger.error(f"Failed to update HOD: {str(e)}")
            messages.error(request, f"Failed to update HOD: {str(e)}")
            return redirect('edit_hod', hod_id=hod_id)

    context = {
        'hod': hod,
        'departments': departments,
    }

    return render(request, 'admin_template/edit_hod_template.html', context)



def manage_hod(request):
    hods = HOD.objects.all()
    return render(request, 'admin_template/manage_hod_template.html', {'hods': hods})


def add_staff(request):
    departments = Department.objects.all()

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        position = request.POST.get('position')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        department_id = request.POST.get('department')

        # Debugging: Check what is being captured
        print(f"Department ID received: {department_id}")

        # Retrieve department
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            messages.error(request, "Selected department does not exist.")
            return redirect('add_staff')

        # Create User
        user = CustomUser.objects.create_user(
            username=username, 
            email=email, 
            password=password, 
            first_name=first_name, 
            last_name=last_name, 
            user_type=3  # Assuming 3 is for Staff
        )
        user.save()

        # Create Staff profile
        Staff.objects.create(
            admin=user, 
            address=address, 
            gender=gender, 
            position=position, 
            department=department  # Ensure department is set
        )

        messages.success(request, "Staff Added Successfully!")
        return redirect('manage_staff')

    context = {
        "title": "Add Staff",
        "departments": departments,
    }

    return render(request, 'admin_template/add_staff_template.html', context)

# def add_staff(request):
#     if request.method == "POST":
#         form = StaffForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Staff Added Successfully!")
#             return redirect('manage_staff')
#         else:
#             messages.error(request, "There was an error with your submission. Please check the form and try again.")
#     else:
#         form = StaffForm()

#     context = {
#         "title": "Add Staff",
#         "form": form,
#     }

#     return render(request, 'admin_template/add_staff_template.html', context)



def manage_staff(request):
    staff_list = Staff.objects.all()
    return render(request, 'admin_template/manage_staff_template.html', {'staff_list': staff_list})


# def add_staff(request):
#     departments = Department.objects.all()
#     return render(request, 'admin_template/add_staff_template.html', {'departments': departments})


# def add_staff_save(request):
#     if request.method == "POST":
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         username = request.POST.get('username')
#         address = request.POST.get('address')
#         department_id = request.POST.get('department')
#         position = request.POST.get('position')
#         gender = request.POST.get('gender')

#         try:
#             user = CustomUser.objects.create_user(
#                 email=email,
#                 password=password,
#                 first_name=first_name,
#                 last_name=last_name,
#                 username=username,
#                 user_type=3  # Assuming 3 is the user_type for Staff
#             )
#             user.save()

#             department = Department.objects.get(id=department_id)
#             staff = Staff(admin=user, address=address, gender=gender, position=position, department=department)
#             staff.save()

#             messages.success(request, "Staff added successfully!")
#             return redirect('add_staff')
#         except Exception as e:
#             messages.error(request, f"Failed to add Staff: {str(e)}")
#             return redirect('add_staff')
#     else:
#         return redirect('add_staff')


def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, admin__id=staff_id)
    departments = Department.objects.all()

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        address = request.POST.get('address')
        department_id = request.POST.get('department')
        position = request.POST.get('position')
        gender = request.POST.get('gender')

        try:
            user = staff.admin
            user.email = email
            if password:
                user.password = make_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.save()

            staff.address = address
            staff.gender = gender
            staff.position = position
            staff.department_id = department_id
            staff.save()

            messages.success(request, "Staff updated successfully!")
            return redirect('manage_staff')
        except Exception as e:
            messages.error(request, f"Failed to update Staff: {str(e)}")
            return redirect('edit_staff', staff_id=staff_id)
    else:
        return render(request, 'admin_template/edit_staff_template.html', {'staff': staff, 'departments': departments})

@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_obj = CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)
    

def add_department(request):
    if request.method == 'POST':
        department_name = request.POST.get('department')
        if department_name:
            try:
                department = Department(department_name=department_name)
                department.save()
                messages.success(request, "Department added successfully!")
                return redirect('manage_department')  # Adjust the redirect as needed
            except Exception as e:
                messages.error(request, f"Error adding department: {e}")
        else:
            messages.error(request, "Department name cannot be empty.")
        return redirect('add_department')

    return render(request, 'admin_template/add_department_template.html')


def manage_department(request):
    departments = Department.objects.all()
    context = {
        'departments': departments
    }
    return render(request, 'admin_template/manage_department_template.html', context)
# def add_department(request):
#     return render(request, 'admin_template/add_department_template.html')


# def add_department_save(request):
#     if request.method == 'POST':
#         department_name = request.POST.get('department')
#         if department_name:
#             try:
#                 department = Department(department_name=department_name)
#                 department.save()
#                 messages.success(request, "Department added successfully!")
#             except Exception as e:
#                 messages.error(request, f"Error adding department: {e}")
#         else:
#             messages.error(request, "Department name cannot be empty.")
#     return redirect('add_department')


# def manage_department(request):
#     departments = Department.objects.all()
#     return render(request, 'admin_template/manage_department_template.html', {'departments': departments})


def edit_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'POST':
        department_name = request.POST.get('department')
        if department_name:
            try:
                department.department_name = department_name
                department.save()
                messages.success(request, "Department updated successfully!")
                return redirect('manage_department')  # Adjust the redirect as needed
            except Exception as e:
                messages.error(request, f"Error updating department: {e}")
        else:
            messages.error(request, "Department name cannot be empty.")
    
    return render(request, 'admin_template/edit_department_template.html', {'department': department})


def staff_leave_view(request):
    leaves = LeaveReportStaff.objects.all()
    return render(
        request,
        "admin_template/staff_leave_view.html",
        {"leaves": leaves},
    )


def staff_approve_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def staff_disapprove_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def hod_leave_view(request):
    leaves = LeaveReportHOD.objects.all()
    return render(
        request,
        "admin_template/hod_leave_view.html",
        {"leaves": leaves},
    )


def hod_approve_leave(request, leave_id):
    leave = LeaveReportHOD.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("hod_leave_view"))


def hod_disapprove_leave(request, leave_id):
    leave = LeaveReportHOD.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("hod_leave_view"))



# def admin_view_hod_attendance(request):
#     hods = HOD.objects.all()
#     return render(
#         request,
#         "admin_template/admin_view_hod_attendance.html",
#         {"hods": hods},
#     )


# def admin_view_staff_attendance(request):
#     staff_members = Staff.objects.all()
#     return render(
#         request,
#         "admin_template/admin_view_staff_attendance.html",
#         {"staff_members": staff_members},
#     )


# @csrf_exempt
# def admin_get_attendance_dates(request):
#     if request.method == 'POST':
#         staff_id = request.POST.get("staff_id")
#         if staff_id:
#             attendance_records = Attendance.objects.filter(staff_id=staff_id)
#             attendance_obj = []
#             for attendance in attendance_records:
#                 data = {
#                     "id": attendance.id,
#                     "staff_name": attendance.staff.get_full_name(),
#                     "attendance_date": str(attendance.date),
#                     "status": attendance.status,
#                 }
#                 attendance_obj.append(data)
#             return JsonResponse(json.dumps(attendance_obj), safe=False)
#         else:
#             return JsonResponse({"error": "Staff ID not provided"}, status=400)
#     else:
#         return JsonResponse({"error": "Only POST method is allowed"}, status=405)

@login_required
def admin_view_hod_attendance(request):
    hod_attendance = Attendance.objects.filter(hod__isnull=False)
    context = {
        'hod_attendance': hod_attendance
    }
    return render(request, 'admin_template/admin_view_hod_attendance.html', context)


@login_required
def admin_view_staff_attendance(request):
    staff_attendance = Attendance.objects.filter(staff__isnull=False)
    context = {
        'staff_attendance': staff_attendance
    }
    return render(request, 'admin_template/admin_view_staff_attendance.html', context)


def admin_send_notification_hod(request):
    hods = HOD.objects.all()
    return render(
        request,
        "admin_template/hod_notification.html",
        {"hods": hods},
    )




def admin_send_notification_staff(request):
    staffs = Staff.objects.all()
    return render(
        request,
        "admin_template/staff_notification.html",
        {"staffs": staffs},
    )


@csrf_exempt
def send_hod_notification(request):
    id = request.POST.get("id")
    message = request.POST.get("message")
    hod = HOD.objects.get(admin=id)
    token = hod.fcm_token
    url = "https://fcm.googleapis.com/fcm/send"
    body = {
        "notification": {
            "title": "hr management system",
            "body": message,
            "click_action": "http://127.0.0.1:8000/hod_all_notification",
            "icon": "http://127.0.0.1:8000/static/dist/img/user2-160x160.jpg",
        },
        "to": token,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=SERVER_KEY_HERE",
    }
    data = requests.post(url, data=json.dumps(body), headers=headers)
    notification = NotificationHOD(hod_id=hod, message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")


@csrf_exempt
def send_staff_notification(request):
    id = request.POST.get("id")
    message = request.POST.get("message")
    staff = Staff.objects.get(admin=id)
    token = staff.fcm_token
    url = "https://fcm.googleapis.com/fcm/send"
    body = {
        "notification": {
            "title": "hr management system",
            "body": message,
            "click_action": "http://127.0.0.1:8000/staff_all_notification",
            "icon": "http://127.0.0.1:8000/static/dist/img/user2-160x160.jpg",
        },
        "to": token,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=SERVER_KEY_HERE",
    }
    data = requests.post(url, data=json.dumps(body), headers=headers)
    notification = NotificationStaff(staff_id=staff, message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")


def staff_feedback_message(request):
    feedbacks = FeedBackStaff.objects.all()
    return render(
        request,
        "admin_template/staff_feedback_template.html",
        {"feedbacks": feedbacks},
    )


def hod_feedback_message(request):
    feedbacks = FeedBackHOD.objects.all()
    return render(
        request,
        "admin_template/hod_feedback_template.html",
        {"feedbacks": feedbacks},
    )


@csrf_exempt
def hod_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        feedback = FeedBackHOD.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except Exception:
        return HttpResponse("False")
    

@csrf_exempt
def staff_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        feedback = FeedBackStaff.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except Exception:
        return HttpResponse("False")
    

# def project_list(request):
#     projects = Project.objects.all()
#     return render(request, 'admin_template/project_list.html', {'projects': projects})


def add_project(request):
    if request.method == 'POST':
        project_name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        # members = request.POST.getlist('members')  # Assuming 'members' is a multi-select field

        if project_name and description and start_date and end_date:
            try:
                project = Project(
                    name=project_name,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=request.user  # Assuming your Project model has a `created_by` field
                )
                project.save()

                # Adding many-to-many relationships (like members)
                # if members:
                #     project.members.set(members)

                messages.success(request, "Project added successfully!")
                return redirect('manage_project')  # Adjust the redirect as needed
            except Exception as e:
                messages.error(request, f"Error adding project: {e}")
        else:
            messages.error(request, "All fields are required.")
        
        return redirect('add_project')

    return render(request, 'admin_template/add_project.html')


def manage_project(request):
    projects = Project.objects.all()
    context = {
        'projects': projects
    }
    return render(request, 'admin_template/manage_project_template.html', context)


def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            project.name = name
            project.description = description
            project.start_date = start_date
            project.end_date = end_date
            project.save()
            
            messages.success(request, "Project updated successfully!")
            return redirect('manage_project')
        except Exception as e:
            messages.error(request, f"Failed to update Project: {str(e)}")
            return redirect('edit_project', project_id=project_id)
    else:
        return render(request, 'admin_template/edit_project_template.html', {'project': project})
    

def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    try:
        project.delete()
        messages.success(request, "Project deleted successfully!")
    except Exception as e:
        messages.error(request, f"Failed to delete Project: {str(e)}")
    
    return redirect('manage_project')


def add_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    hods = CustomUser.objects.filter(user_type=2)  # Filter HODs
    staff = CustomUser.objects.filter(user_type=3)  # Filter Staff

    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        assigned_hods = request.POST.getlist('hods')  # Get selected HODs
        assigned_staff = request.POST.getlist('staff')  # Get selected staff

        try:
            task = Task(
                name=name,
                description=description,
                due_date=due_date,
                priority=priority,
                status=status,
                project=project
            )
            task.save()
            task.assigned_to.set(assigned_hods + assigned_staff)
            task.save()

            messages.success(request, "Task added successfully!")
            return redirect('related_tasks', project_id=project.id)  # Redirect to related tasks
        except Exception as e:
            messages.error(request, f"Failed to add task: {str(e)}")
            return redirect('add_task', project_id=project.id)
    else:
        return render(request, 'admin_template/add_task_template.html', {'project': project, 'hods': hods, 'staff': staff})


def related_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project)

    return render(request, 'admin_template/related_tasks_template.html', {
        'project': project,
        'tasks': tasks
    })


def edit_task(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, project=project)

    if request.method == 'POST':
        # Manually retrieve form data from POST request
        task.name = request.POST.get('name')
        task.description = request.POST.get('description')
        task.due_date = request.POST.get('due_date')
        task.priority = request.POST.get('priority')
        task.status = request.POST.get('status')
        assigned_to_ids = request.POST.getlist('assigned_to')

        # Validate the form data (simple validation, you can expand this)
        if not task.name or not task.description or not task.due_date or not task.priority or not task.status:
            messages.error(request, 'Please fill in all required fields.')
        else:
            # Save the task
            task.save()
            
            # Update the many-to-many relationship
            task.assigned_to.set(assigned_to_ids)
            messages.success(request, 'Task updated successfully!')
            return redirect(reverse('tasks_for_project', args=[project.id]))  # Redirect to the task listing page

    return render(request, 'admin_template/edit_task.html', {
        'project': project,
        'task': task,
        'users': CustomUser.objects.all(),  # Assuming you want to list all users for the assigned_to field
    })


def delete_task(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, project=project)

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect(reverse('tasks_for_project', args=[project.id]))  # Redirect to the task listing page

    return render(request, 'admin_template/delete_task_confirm.html', {
        'project': project,
        'task': task,
    })


def view_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    context = {
        'project': project
    }
    return render(request, 'admin_template/view_project_template.html', context)