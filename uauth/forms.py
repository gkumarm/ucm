from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class UserForm(UserCreationForm):
	class Meta():
		model = User
		fields = ('username','password1','password2', 'email', 'first_name','last_name')

class ProfileForm(forms.ModelForm):
	# phone_number = forms.RegexField(regex=r'^\+?1?\d{9,15}$',
	# 	error_messages = (
	# 		"Phone number format: '+999999999' up to 15 digits allowed."))

	class Meta():
		model = Profile
		fields = (
			'imagefile',
			'birth_date',
			'phone_number',
			'address_line_1',
			'address_line_2',
			'country')
