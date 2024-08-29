from django import forms
from django.contrib.auth.hashers import make_password
from .models import CustomUser, HOD, Department

class HODForm(forms.ModelForm):
    email = forms.EmailField(
        label="Email",
        max_length=50,
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "off"})
    )
    password = forms.CharField(
        label="Password",
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    first_name = forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"})
    )
    address = forms.CharField(
        label="Address",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    gender = forms.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female')],
        widget=forms.Select(attrs={"class": "form-control"})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    profile_pic = forms.FileField(
        label="Profile Pic",
        max_length=50,
        widget=forms.FileInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = HOD
        fields = ['email', 'password', 'first_name', 'last_name', 'username', 'address', 'gender', 'department', 'profile_pic']


# class StaffForm(forms.ModelForm):
#     class Meta:
#         model = Staff
#         fields = ['address', 'gender', 'position', 'department']
    
#     username = forms.CharField(max_length=150, required=True)
#     email = forms.EmailField(max_length=254, required=True)
#     first_name = forms.CharField(max_length=30, required=True)
#     last_name = forms.CharField(max_length=30, required=True)
#     password = forms.CharField(widget=forms.PasswordInput, required=True)

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         if CustomUser.objects.filter(username=username).exists():
#             raise forms.ValidationError("This username is already taken.")
#         return username

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if CustomUser.objects.filter(email=email).exists():
#             raise forms.ValidationError("This email is already registered.")
#         return email

#     def save(self, commit=True):
#         # Save the User
#         user = CustomUser.objects.create_user(
#             username=self.cleaned_data['username'],
#             email=self.cleaned_data['email'],
#             first_name=self.cleaned_data['first_name'],
#             last_name=self.cleaned_data['last_name'],
#             password=self.cleaned_data['password'],
#             user_type=3,  # Assuming 3 is for Staff
#         )
#         user.save()

#         # Save the Staff profile
#         staff = Staff(
#             admin=user,
#             address=self.cleaned_data['address'],
#             gender=self.cleaned_data['gender'],
#             position=self.cleaned_data['position'],
#             department=self.cleaned_data['department'],
#         )
#         if commit:
#             staff.save()

#         return staff