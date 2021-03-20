import hashlib
import string_utils
from django.core.mail import send_mail
from pathlib import Path
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site

def encrypt_sha256 (hash_string):
	sha_signature = hashlib.sha256 (hash_string.encode()).hexdigest()

	# print ("Original>>>>:", hash_string)
	# print ("SH256>>>>>>>:", sha_signature)
	sha_signature = string_utils.shuffle(sha_signature)
	# print ("Suffled>>>>>:", sha_signature)

	return sha_signature

def send_user_verification_mail (recipient, hash_string, request):
	currsite = get_current_site(request)

	sender = "UCMem <gk.malattiri@gmail.com>"
	subject = "Welcome to UCMem! Confirm Your Email"

	text_message = f"""You are one step away from confirming 
		 your new UCMem account by clicking the following link
		 http://{currsite.domain}/verify?upn={hash_string}
		 """
	context = {
		'first_name': 'Gireesh Kumar', 
		'last_name':'Malattiri',
		'hash_string': hash_string,
		'site_root': "http://" + currsite.domain,
	}

	html_template = 'uauth/registration_verification.html'
	html_message = render_to_string(html_template, { 'context': context, })

	# print ('HTML:-------------', html_message)
	# print ('Context <-------->', context)
	
	print ("Response of email send --> ", 
		send_mail (subject, text_message, 
					sender, [recipient,], fail_silently=True,
					html_message=html_message))

	return 1
#	return render(request,'uauth/registration_verification.html',{'context': context,})