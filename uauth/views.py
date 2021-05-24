from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
from django.utils.http import is_safe_url

from base.settings import LOGIN_REDIRECT_URL
from .forms import UserForm
from .models import Profile
from . import util as util

@login_required
def usignout(request):
	logout(request)
	messages.success(request, 'You are logged out!')	
	return HttpResponseRedirect(reverse('uauth:signin'))

def usignup(request):
	context = {'ptitle': "Sign Up"}
	registered = False
	if request.method == 'POST':
		print (request.POST)
		post = request.POST.copy() # to make it mutable
		post ['email'] = post ['username']
		post ['password2'] = post ['password1']
		userForm = UserForm(data=post)
		if userForm.is_valid():
			hash_string = util.encrypt_sha256 (post ['username'] )
			user = userForm.save()
			user.profile.notificationflag = True if post.get ('notificationflag', 'off') == 'on' else False
			user.profile.validatehash = hash_string
			user.is_active = False
			print ("Hash String is ====>", hash_string)
#			user.set_password(user.password)
			user.save()
			registered = True

			util.send_user_verification_mail (post ['username'],
				hash_string, request)

			context = {
				'ptitle': "Message",
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
			context ['userForm'] = userForm			
			messages.error (request, userForm.errors)
			print(userForm.errors)

	elif request.method == 'GET':
		return render(request, 'uauth/signup.html', {'context':context})
	else:
		userForm = UserForm()

	return render(request,'uauth/signup.html',{'context':context})

def uverify (request):
	if request.method == 'GET':
		hash_string = request.GET.get ('upn', None)
		if hash_string:
			profile = Profile.objects.filter (validatehash=hash_string).first()
			if profile:
				if profile.validatedflag == True:
					context = {
						'ptitle': "Message",
						'message': [
							'Your account is already verified.',
							], 
						'first_name': profile.user.first_name,
						'action': 'Sign In to UCMem',
						'actionurl': reverse('uauth:signin'),
					}
				else:
					context = {
						'ptitle': "Message",
						'message': [
							'Your account verified.',
							'Enjoy the UCMem unique experience',
							],
						'first_name': profile.user.first_name,
						'action': 'Sign In to UCMem',
						'actionurl': reverse('uauth:signin'),
					}
					profile.validatedflag = True
					profile.save()
					profile.user.is_active = True
					profile.user.save ()
			else:
				context = {
					'ptitle': "Message",
					'message': [
						'We received an invalid account verification request.',
						'Please try again the Sign Up option.',
						],
					'action': 'Sign Up',
					'actionurl': reverse('uauth:signup'),
				}
		else:
			context = {
				'ptitle': "Message",
				'message': [
					'We received an incomplete verification request',
					'Please try again the Sign Up option.',
					], 
				'action': 'Sign Up',
				'actionurl': reverse('uauth:signup'),
			}
	else:
		context = {
			'ptitle': "Message",
			'message': [
				'We received an unsupported verification action',
				'Please try again the Sign Up option.',
				], 
			'action': 'Sign Up',
			'actionurl': reverse('uauth:signup'),
		}

	return render(request, 'uauth/message_box.html', {'context':context})

def usignin(request):
	context = {'ptitle': "Sign In"}
	if request.method == "GET":
		cache.set ('next', request.GET.get ('next', None))
	elif request.method == 'POST':
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

				next_url = cache.get('next')
				if next_url:
					cache.delete ('next')
					print ("next url from cache ==>", next_url)
					if not is_safe_url (url=next_url,
						allowed_hosts = {request.get_host()},
						require_https = request.is_secure()):
						next_url = LOGIN_REDIRECT_URL
						print ("is_safe_url failed")
				else:
					next_url = LOGIN_REDIRECT_URL

				return HttpResponseRedirect(next_url)
			else:
				return HttpResponse("Your account was inactive.")
		else:
			print("Someone tried to Sign In and failed.")
			print("They used username: [{}] and password: [{}]".format(username,password))
			messages.error(request, 'Invalid Sign In details given!')
			return render(request, 'uauth/signin.html', {'errmsg':'Invalid Sign In details given'})

	return render(request, 'uauth/signin.html', {'context':context})

@login_required
def upassword(request):
	if request.method == 'POST':
		form = PasswordChangeForm (request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Important!
			messages.success(request, 'Your password updated successfully! Sign In again with new credentials.')
			logout(request)
			return HttpResponseRedirect(reverse('uauth:signin'))
		else:
			messages.error(request, 'Please correct the error below.')
	else:
		form = PasswordChangeForm(request.user)

	return render(request, 'uauth/password.html', {'form': form})

# def error_404 (request, exception):
# 	return render(request, 'uauth/404.html')

# def error_500 (request):
# 	return render(request, 'uauth/500.html')
