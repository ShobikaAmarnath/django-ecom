from django import forms
from .models import Account, UserProfile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Create Password',
        'minlength': '8',
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Repeat Password',
    }))

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Common class for all fields
        common_class = 'w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        
        # Apply the common class and placeholders to all fields
        self.fields['first_name'].widget.attrs.update({'class': common_class, 'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({'class': common_class, 'placeholder': 'Last Name'})
        self.fields['email'].widget.attrs.update({'class': common_class, 'placeholder': 'Email Address'})
        self.fields['phone_number'].widget.attrs.update({
            'class': common_class, 
            'placeholder': 'Phone Number',
            'pattern': '[0-9]{10}', # HTML5 validation for 10 digits
            'title': 'Please enter a 10-digit phone number.',
        })
        self.fields['password'].widget.attrs.update({'class': common_class})
        self.fields['confirm_password'].widget.attrs.update({'class': common_class})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
            })
        self.fields['phone_number'].widget.attrs['pattern'] = '[0-9]{10}'
        self.fields['phone_number'].widget.attrs['title'] = 'Please enter a 10-digit phone number.'

class UserProfileForm(forms.ModelForm):
    # Make profile picture not required
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput)

    class Meta:
        model = UserProfile
        fields = ['address_line_1', 'address_line_2', 'city', 'state', 'country', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name != 'profile_picture':
                self.fields[field_name].widget.attrs.update({
                    'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                })
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
        })