from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

# Department model
class Department(models.Model):
    department_name = models.CharField(max_length=255)

    def __str__(self):
        return self.department_name

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

# Custom User model extending AbstractUser
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Admin'),
        (2, 'HOD'),
        (3, 'Staff')
    )
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

# HOD model
class HOD(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='hod_profile')
    address = models.TextField()
    gender = models.CharField(max_length=255, default='Male')
    profile_pic = models.FileField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    fcm_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.admin.first_name} {self.admin.last_name} - {self.department.department_name}"

# Staff model
class Staff(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff_profile')
    address = models.TextField()
    gender = models.CharField(max_length=255, default='Male')
    profile_pic = models.FileField()
    position = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    fcm_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.admin.username

# Admin model
class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.admin.username

#  Project model
# class Project(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField()
#     start_date = models.DateField()
#     end_date = models.DateField()
#     status = models.CharField(max_length=50, choices=(
#         ('active', 'Active'),
#         ('completed', 'Completed'),
#         ('on_hold', 'On Hold'),
#     ), default='active')
#     department = models.ForeignKey(Department, on_delete=models.CASCADE)
#     created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_projects')
#     members = models.ManyToManyField(CustomUser, related_name='project_members')

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.name

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, choices=(
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ), default='active')
    # department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_projects')
    members = models.ManyToManyField(CustomUser, related_name='project_members', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure the project initiator is a member
        if self.created_by not in self.members.all():
            self.members.add(self.created_by)


# Task model
# class Task(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField()
#     due_date = models.DateField()
#     priority = models.CharField(max_length=50, choices=(
#         ('low', 'Low'),
#         ('medium', 'Medium'),
#         ('high', 'High'),
#     ), default='medium')
#     status = models.CharField(max_length=50, choices=(
#         ('to_do', 'To Do'),
#         ('in_progress', 'In Progress'),
#         ('done', 'Done'),
#     ), default='to_do')
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
#     assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tasks')

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.name} - {self.project.name}"

class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    priority = models.CharField(max_length=50, choices=(
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ), default='medium')
    status = models.CharField(max_length=50, choices=(
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ), default='to_do')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ManyToManyField(CustomUser, related_name='tasks')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Add task members to the project members
        for user in self.assigned_to.all():
            if user not in self.project.members.all():
                self.project.members.add(user)

# Comment model
class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.task:
            return f"Comment by {self.user.username} on Task: {self.task.name}"
        else:
            return f"Comment by {self.user.username} on Project: {self.project.name}"

# Attendance model
class Attendance(models.Model):
    id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, null=True)
    hod = models.ForeignKey(HOD, on_delete=models.DO_NOTHING, null=True, blank=True)  # To track HOD attendance
    attendance_date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.staff.admin.username if self.staff else self.hod.admin.username} - {self.attendance_date}"

# Leave Request model
class LeaveRequest(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)
    leave_date = models.DateField()
    leave_message = models.TextField()
    status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.leave_date}"

# Leave Report for HOD model
class LeaveReportHOD(models.Model):
    id = models.AutoField(primary_key=True)
    hod_id = models.ForeignKey(HOD, on_delete=models.CASCADE)
    leave_date = models.DateField()
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hod_id.admin.username} - {self.leave_date}"

# Leave Report for Staff model
class LeaveReportStaff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    leave_date = models.DateField()
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff_id.admin.username} - {self.leave_date}"

# Feedback model for HOD
class FeedBackHOD(models.Model):
    id = models.AutoField(primary_key=True)
    hod_id = models.ForeignKey(HOD, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hod_id.admin.username} - {self.created_at}"

# Feedback model for Staff
class FeedBackStaff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff_id.admin.username} - {self.created_at}"

# Notification model for HOD
class NotificationHOD(models.Model):
    id = models.AutoField(primary_key=True)
    hod_id = models.ForeignKey(HOD, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hod_id.admin.username} - {self.created_at}"

# Notification model for Staff
class NotificationStaff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff_id.admin.username} - {self.created_at}"

# Signals to create user profiles
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        elif instance.user_type == 2:
            pass # Creating HOD profile
        elif instance.user_type == 3:
            pass  # Creating Staff profile

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1 and hasattr(instance, 'admin_profile'):
        instance.admin_profile.save()
    elif instance.user_type == 2 and hasattr(instance, 'hod_profile'):
        instance.hod_profile.save()
    elif instance.user_type == 3 and hasattr(instance, 'staff_profile'):
        instance.staff_profile.save()
