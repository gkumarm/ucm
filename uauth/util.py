import hashlib
import string_utils
from django.core.mail import send_mail
from pathlib import Path
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.db import connection, transaction

from ucm.models import UserTopic
def encrypt_sha256 (hash_string):
	sha_signature = hashlib.sha256 (hash_string.encode()).hexdigest()

	# print ("Original>>>>:", hash_string)
	# print ("SH256>>>>>>>:", sha_signature)
	sha_signature = string_utils.shuffle(sha_signature)
	# print ("Suffled>>>>>:", sha_signature)

	return sha_signature

def subscribe_topic (user_id, topic_id, request):

	ut = UserTopic (
		user_id=user_id, topic_id=topic_id, 
		srmethod='LBOXP', maxdeck=5, dclimit=5)
	ut.save ()

	# SQLLite
	# sqlUserNote = """
	# 	insert into ucm_usernotem (
	# 		currdeck, notem_id, usertopic_id, cdate, mdate) 
	# 		select 0, id,%s, datetime ('now'), datetime ('now') from ucm_notem where topic_id=%s
	# """

	# Postgres
	sqlUserNote = """
		insert into ucm_usernotem (
			currdeck, notem_id, usertopic_id, cdate, mdate) 
			select 0, id,%s, now(), now() from ucm_notem where topic_id=%s
	"""	
	cursor = connection.cursor()
	cursor.execute(sqlUserNote, [ut.id, topic_id])
#	transaction.commit_unless_managed()

def send_invitation_email (to_name, to_email, hash_string, request):
	currsite = get_current_site(request)

	sender = "UCMem <gk.malattiri@gmail.com>"
	subject = request.user.first_name + " is Inviting to join UCMem!"

	text_message = f"""You are invited to join UCMem by clicking the following link
		 http://{currsite.domain}/register
		 """

	context = {
		'to_name': to_name,
		'message': [
			'I invite you to join UCMem, the endless possibilities of reinforced learning.',
			'UCMem has a unique community of tousands of people who collobrate together.  \
				Whether you\'re new to the concept of reinforced learning or a seasoned veteran, \
				it has everything to get your back!',
			],
		'first_name': request.user.first_name,
		'site_root': "http://" + currsite.domain,
		'hash_string': hash_string,
	}	

	html_template = 'uauth/invite_mail_template.html'
	html_message = render_to_string(html_template, { 'context': context, })

	# print ('HTML:-------------', html_message)
	# print ('Context <-------->', context)
	
	print ("Response of email send --> ", 
		send_mail (subject, text_message, 
					sender, [to_email,], fail_silently=True,
					html_message=html_message))

	return 1

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