from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm

from .forms import UserForm
from .models import Profile
from . import util as util

@login_required
def ulogout(request):
	logout(request)
	messages.success(request, 'You are logged out!')	
	return HttpResponseRedirect(reverse('uauth:login'))

def uregister(request):
	registered = False
	if request.method == 'POST':
		print (request.POST)
		post = request.POST.copy() # to make it mutable
#		post ['password2'] = post ['password1']
		post ['email'] = post ['username']
		user_form = UserForm(data=post)
		if user_form.is_valid():
			validatehash = util.encrypt_sha256 (post ['username'] )
			user = user_form.save()
			user.profile.notificationflag = True if post.get ('notificationflag', 'off') == 'on' else False
			user.profile.validatehash = validatehash
			user.is_active = False
#			user.set_password(user.password)
			user.save()
			registered = True

			util.send_user_verification_mail (post ['username'],
				validatehash, request)

			context = {
				'message': [
					'Your account is created.' ,
					'A verification email is sent to your email ' + post ['username'] ,
					'Complete the registration process by clicking the verification link in the email',
					],
				'first_name': user.first_name,
				'action': 'Return to UCMem Home',
				'actionurl': reverse('ucm:home'),
			}
			return render(request, 'uauth/message_box.html', {'context':context})
		else:
			messages.error (request, user_form.errors)
			print(user_form.errors)
	else:
		user_form = UserForm()
	
	return render(request,'uauth/registration.html',
					{
						'user_form':user_form,
						'registered':registered
					}
				)

def uverify (request):
	if request.method == 'GET':
		hash_string = request.GET.get ('upn', None)
		if hash_string:
			profile = Profile.objects.filter (validatehash=hash_string).first()
			if profile:
				if profile.validatedflag == True:
					context = {
						'message': [
							'Your account is already verified.',
							], 
						'first_name': profile.user.first_name,
						'action': 'Login to UCMem',
						'actionurl': reverse('uauth:login'),
					}
				else:
					context = {
						'message': [
							'Your account verified.',
							'Enjoy the UCMem unique experience',
							],
						'action': 'Login to UCMem',
						'actionurl': reverse('uauth:login'),
					}
					profile.validatedflag = True
					profile.save()
					profile.user.is_active = True
					profile.user.save ()
			else:
				context = {
					'message': [
						'We received an invalid account verification request.',
						'Please try again the register option.',
						],
					'action': 'Register',
					'actionurl': reverse('uauth:register'),
				}
		else:
			context = {
				'message': [
					'We received an incomplete verification request',
					'Please try again the register option.',
					], 
				'action': 'Register',
				'actionurl': reverse('uauth:register'),
			}
	else:
		context = {
			'message': [
				'We received an unsupported verification action',
				'Please try again the register option.',
				], 
			'action': 'Register',
			'actionurl': reverse('uauth:register'),
		}

	return render(request, 'uauth/message_box.html', {'context':context})

def ulogin(request):
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		print("Authenticating user: {} and password: {}".format(username,password))		
		user = authenticate(username=username, password=password)
		if user:
			if user.is_active:
				if user.last_login:
					messages.success (request, 'Welcome back ' + user.first_name + '!!!')
				else:
					messages.success (request, 'Welcome ' + user.first_name + '!!!')
				login(request,user)

				return HttpResponseRedirect(reverse('ucm:home'))
			else:
				return HttpResponse("Your account was inactive.")
		else:
			print("Someone tried to login and failed.")
			print("They used username: [{}] and password: [{}]".format(username,password))
			messages.error(request, 'Invalid login details given!')
			return render(request, 'uauth/login.html', {'errmsg':'Invalid login details given'})
	else:
		return render(request, 'uauth/login.html', {})

@login_required
def upassword(request):
	if request.method == 'POST':
		form = PasswordChangeForm (request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Important!
			messages.success(request, 'Your password updated successfully! Sign-in again with new credentials.')
			logout(request)
			return HttpResponseRedirect(reverse('uauth:login'))
		else:
			messages.error(request, 'Please correct the error below.')
	else:
		form = PasswordChangeForm(request.user)

	return render(request, 'uauth/password.html', {'form': form})

# def error_404 (request, exception):
# 	return render(request, 'uauth/404.html')

# def error_500 (request):
# 	return render(request, 'uauth/500.html')
