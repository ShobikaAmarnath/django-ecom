from django import forms
from .models import Account, UserProfile

class RegistrationForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'password', 'phone_number']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': f'Enter {field.replace("_", " ").title()}'
            })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Create Password'
        })
        self.fields['confirm_password'] = forms.CharField(
            widget=forms.PasswordInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Repeat Password'
            }),
            label='Confirm Password'
        )

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["first_name", "last_name", "phone_number"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "last_name": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "phone_number": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
        }
        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "phone_number": "Phone Number",
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["address_line_1", "address_line_2", "city", "state", "country", "profile_picture"]
        widgets = {
            "address_line_1": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "address_line_2": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "city": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "state": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "country": forms.TextInput(attrs={"class": "border rounded p-2 w-full"}),
            "profile_picture": forms.ClearableFileInput(attrs={"class": "border rounded p-2 w-full"}),
        }
        labels = {
            "address_line_1": "Address Line 1",
            "address_line_2": "Address Line 2",
            "city": "City",
            "state": "State",
            "country": "Country",
            "profile_picture": "Profile Picture",
        }