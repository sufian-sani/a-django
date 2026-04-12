from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django import forms


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        }


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )
