from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import ObjectDoesNotExist
import random
from django.db.models import Q, Count
from django.db import transaction
import logging
from django.utils import timezone
from datetime import datetime
from django.views.generic import (
    CreateView, DetailView, FormView, ListView, TemplateView
)
from django.views.generic.detail import SingleObjectMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .decorators import query_debugger
from django.contrib.auth.models import User
from .models import UserNotem, Noted, UserNotemLog, UserTopic, UserLearningDeck, ReviewLog, Notem, Topic, Invitation
from .forms import ReviewLogForm, TopicForm, NotedFormSet, NotemFormSet
from uauth.forms import UserForm, ProfileForm

from . import constants
from uauth import util as util
from rest_framework import views
from rest_framework.response import Response
from .serializers import YourSerializer
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator

# l = logging.getLogger('django.db.backends')  
# l.setLevel(logging.DEBUG)
# l.addHandler(logging.StreamHandler())   

# Create your views here.
def home(request):
	if request.user.is_authenticated:
		return feed (request)
	else:
		context = {'ptitle': "Home"}
		return render(request, "ucm/index-non-signed-in.html", {'context': context})

@query_debugger
@login_required (redirect_field_name='next')
def topic_review (request, pk=0, learn_more=False, template_name='ucm/topic_review.html'):
	context = {'ptitle': "Review"}	
	filters = Q()
	if request.method == 'GET':
		# 1. Check in the learning deck for pendng cards
		# 2. If pending found, proceed
		# 3. If no pending,
		# 3.1 If curr date is same as modified date in user topic, then ask user whether to create next learning deck
		# 3.2 If curr date is not same, create new learning deck
		print ('User---------> ', request.user)
		ut = UserTopic.objects.filter (id=pk, user=request.user).first()
		if not ut:
			messages.info (request, "Not a subscribed topic")
			return render(request, template_name, {'flag':'not_subscribed', 'topic':pk, 'context':context})

		filters = Q(Q(usernotem__usertopic_id=pk))# & Q(usernotem__currdeck=1))
		uld = UserLearningDeck.objects.filter (filters).first()
		if not uld:
			if datetime.strftime(timezone.now(), '%Y%m-%d') == datetime.strftime(ut.mdate, '%Y%m-%d') and learn_more == False:
				messages.success (request, "You have no cards pending to learn today")
				return render(request, template_name, {'flag':'learn_more', 'topic':pk, 'context':context})
			else:
				if not learn_more:
					messages.success (request, "Creating new learning deck for today")
				decksToLearn = do_calc (ut)
				i = 0
				for deck in decksToLearn:
					unm = UserNotem.objects.filter (
						usertopic_id=pk, 
						currdeck=deck ['currdeck'])[:deck ['newCount']]
					print ("Adding from deck [", deck ['currdeck'], "] ", deck ['newCount'], "cards")
					for un in unm:
						i+=1
						UserLearningDeck.objects.create (usernotem=un, cuser=request.user)

				if i == 0:
					messages.info (request, "Your topic has no more cards left to learn")
					return render(request, template_name, {'flag':'no_more', 'topic':pk})
				else:
					messages.success (request, 'Added ' + str (i) + ' cards to your learning deck')
	else:
		raise Http404

	# rand_id = random.randint(1, 100)
	ob = ['usernotem__mdate']
	uld = UserLearningDeck.objects.filter (filters).order_by (*ob).first()
	# print (userNote)
	# print ('ULD ID:', userNote.usernotem.id, 'usernotem.notem:', userNote.usernotem.notem.id)
	note = None
	formReviewLog =''
	if not uld:
		print ('Qeury returned 0 rows')
#		messages.error (request, 'Not found [notem_id=' + str (pk) + '] [currdeck=0]')
	else:
		ob = ['norder']
		nd = Noted.objects.filter (notem__id = uld.usernotem.notem.id).order_by (*ob).prefetch_related('notem')
		if nd:
			print (nd)
		else:
			print ('no such note')

		ob = ['-cdate',]
		reviewLog = ReviewLog.objects.filter(usernotem=uld.usernotem.id).order_by (*ob)
		formReviewLog = ReviewLogForm (initial={
			'usernotem': uld.usernotem,
			'cuser': request.user
		})

	return render(request, template_name, {'userNote':uld, 'note':nd, 'topic':pk,
		'reviewLog':reviewLog, 'formReviewLog':formReviewLog ,'context':context})

@login_required (redirect_field_name='next')
@require_GET
def topic_pause (request, pk):

	ut = UserTopic.objects.filter (pk=pk).first()
	if not ut:
		raise ValidationError(r"Topic [{}] is not a valid topic".format (ut.topic.title))
	ut.status = 1 #1-> Paused
	ut.save ()
	messages.success (request, r"Topic '{}' set to Pause status".format (ut.topic.title))

	next = request.GET.get('next', '/')
	return HttpResponseRedirect (next)

@login_required (redirect_field_name='next')
@require_GET
def topic_resume (request, pk):

	ut = UserTopic.objects.filter (pk=pk).first()
	if not ut:
		raise ValidationError(r"Topic [{}] is not a valid topic".format (ut.topic.title))
	ut.status = 0 #1-> enabled
	ut.save ()
	messages.success (request, r"Topic '{}' set to Resume status".format (ut.topic.title))

	next = request.GET.get('next', '/')
	return HttpResponseRedirect (next)

@login_required (redirect_field_name='next')
def topic_share (request, pk, template_name="ucm/topic-share.html"):
	context = {'ptitle': "Share Topic"}
	topic = Topic.objects.filter (pk=pk).first()
	if not topic:
		raise ValidationError(r"Topic [{}] is not a valid topic".format (pk))

	context ['topic'] = topic
	print ("TOPIC: ", topic)

	if request.method == 'POST':
		print (request.POST)
		to_name  = request.POST.get ('first_name', None)
		to_email = request.POST.get ('email', None)
		if to_name != None and to_email != None:
#			TODO:// Validate user inputs and keep an invite log with hash
			hash_string = util.encrypt_sha256 (to_email)
			inv = Invitation (cuser=request.user,hash_string=hash_string, 
					to_name=to_name, to_email=to_email)
			util.send_invitation_email (to_name,to_email, hash_string, request)
			inv.save ()

			context = {
				'message': [
					'Invitation sent to ' + to_name,
					'Email is addressed to ' + to_email,
					],
				'first_name': request.user.first_name,
				'action': 'Return to UCMem Home',
				'actionurl': request.POST.get('next', reverse ('ucm:home')),
				'hash_string': hash_string,
			}
			return render(request, 'uauth/message_box.html', {'context':context})

	return render(request, template_name, {'context':context})

@login_required (redirect_field_name='next')
def topic_subscribe (request, pk=0):
	if request.method == 'GET':
		print ("subscribe-subscribe-subscribe-subscribe:", pk)		
		t=Topic.objects.filter (pk=pk).first()
		if not t:
			messages.info (request, "Selected topic not found for subscription")
		else:
			messages.info (request, "Topic [" + t.title + "] subscribed successfully. Enjoy learning")

		util.subscribe_topic (request.user.id, pk, request)

	return HttpResponseRedirect(reverse('ucm:home'))

@login_required (redirect_field_name='next')
def invite(request):
	if request.method == 'POST':
		print (request.POST)
		to_name  = request.POST.get ('first_name', None)
		to_email = request.POST.get ('username', None)
		if to_name != None and to_email != None:
#			TODO:// Validate user inputs and keep an invite log with hash
			hash_string = util.encrypt_sha256 (to_email)
			inv = Invitation (cuser=request.user,hash_string=hash_string, 
					to_name=to_name, to_email=to_email)
			util.send_invitation_email (to_name,to_email, hash_string, request)
			inv.save ()

			context = {
				'message': [
					'Invitation sent to ' + to_name,
					'Email is addressed to ' + to_email,
					],
				'first_name': request.user.first_name,
				'action': 'Return to UCMem Home',
				'actionurl': reverse('ucm:home'),
				'hash_string': hash_string,
			}
			return render(request, 'uauth/message_box.html', {'context':context})

	user_form = UserForm()
	return render(request,'uauth/invite.html',{'user_form':user_form,})

def get_progress (user_id):
 # 0. card_count = 10; NEXT_BOX = 0
 # 1. no_of_cards_from_NEXT_BOX = card_count : if count() > card_count ? card_count : sum ()
 # 2. Review count = card_count + (card_count - no_of_cards_from_NEXT_BOX)
 # 3. NEXT_BOX = NEXT_BOX + 1
 # 4. Calculate % of cards to be taken from next BOX
 # 5.1 % share of next BOX = round (card_count_NEXT_BOX/count (cards from all boxes starting from NEXT_BOX)*100)
 # 5.2 Repeat step 1

	unm = UserNotem.objects \
		.filter (usertopic__in = UserTopic.objects.filter (user_id=user_id)) \
		.values('usertopic_id', 'currdeck') \
		.annotate(total=Count('currdeck')) \
		.order_by('usertopic_id', 'currdeck')

	for x in unm:
#		print (x)
		gtotal = sum (y ['total'] for y in unm if y ['usertopic_id'] == x ['usertopic_id'])
#		print ('------------>', gtotal)
		x ['percentage'] = round ((x ['total']/gtotal)*100)
#		print (x)
	return unm

def do_calc (ut):
 # 0. card_count = 10; NEXT_BOX = 0
 # 1. no_of_cards_from_NEXT_BOX = card_count : if count() > card_count ? card_count : sum ()
 # 2. Review count = card_count + (card_count - no_of_cards_from_NEXT_BOX)
 # 3. NEXT_BOX = NEXT_BOX + 1
 # 4. Calculate % of cards to be taken from next BOX
 # 5.1 % share of next BOX = round (card_count_NEXT_BOX/count (cards from all boxes starting from NEXT_BOX)*100)
 # 5.2 Repeat step 1
	unm = UserNotem.objects \
		.filter (usertopic_id = ut.id, currdeck__lte=ut.maxdeck) \
		.values('currdeck', 'usertopic_id') \
		.annotate(total=Count('currdeck')) \
		.order_by('currdeck')

	gtotal = sum(x['total'] for x in unm)
	print("total cards for in all boxes:", gtotal)

	dclimit = ut.dclimit
	dclimitNew = ut.dclimit
	nextDeck = 0
	prevCount = 0
	for x in unm:
		print (x)
		if nextDeck == 0:
			nextDeck = x ['currdeck']
			gtotal = gtotal - x ['total']
			if x ['total'] > dclimitNew:
				x ['newCount'] = dclimitNew
			else:
				x ['newCount'] = x ['total']
		else:
			dclimitNew = round((x ['total']/gtotal) * dclimit)
			if x ['total'] > dclimitNew:
				x ['newCount'] = dclimitNew
			else:
				x ['newCount'] = x ['total']

	for x in unm:
		print (x)

	return unm

@query_debugger
@login_required (redirect_field_name='next')
def more (request):
	if request.method == 'GET':
		return topic_review (request, learn_more=True)
#		return buildHome (request)		
	else:
		print (r"------------------> MORE::POST::TOPIC {}".format (request.POST.get ('ritem', 0)), request.POST)
		request.method = 'GET'
		return topic_review (request, pk=request.POST.get ('ritem', 0), learn_more=True)		
# 	else:
# 		raise Http404
# #		raise Exception('Unsupported method')
# #		return HttpResponseForbidden("Unsupported method")

# 		elif 'learn_more' in request.POST: # User wants to learn more



#           <input type="hidden" value="{{ topic }}" name="ritem"/>
#           <button type="submit" class="btn btn-primary" name="learn_more">Yes</button>

def calculateNextDeck (request, uld, ueval):

	currdeck = uld.usernotem.currdeck
	if uld.usernotem.usertopic.srmethod == constants.LBOXP:
		if ueval == constants.UEVAL_REPEAT:
			currdeck = currdeck + 0
		elif ueval == constants.UEVAL_GOOD:
			currdeck = currdeck + 1
		elif ueval == constants.UEVAL_EASY:
			currdeck = currdeck + 2
	elif uld.usernotem.usertopic.srmethod == constants.LBOXR:
		if ueval == constants.UEVAL_REPEAT:
			currdeck = 1
		elif ueval == constants.UEVAL_GOOD:
			currdeck = currdeck + 1
		elif ueval == constants.UEVAL_EASY:
			currdeck = currdeck + 2
	else:
		messages.error (request, "Unsupported SR Method [" + uld.usernotem.usertopic.srmethod + "]")
		return -1

	if currdeck > uld.usernotem.usertopic.maxdeck:
		currdeck = uld.usernotem.usertopic.maxdeck+1 # Matured Deck
	elif currdeck < 0:
		currdeck = 0

	return currdeck


class YourView(views.APIView):
	def get(self, request):
		yourdata= [{"likes": 10, "comments": 0}, {"likes": 4, "comments": 23}]
		results = YourSerializer(yourdata, many=True).data
		return Response(results)

@login_required (redirect_field_name='next')
def member_topic (request, pk=0, template_name='ucm/member-topics.html'):
	topics = Topic.objects.filter (cuser=request.user).select_related('cuser')
	context = {
		'ptitle': "Member Topics",
		'topics': topics,
	}

	return render(request, template_name, {'context':context})

@login_required (redirect_field_name='next')
def member_dashboard (request, template_name='ucm/member-db-main.html'):
	context = {'ptitle': "Topics"}

	if request.method == 'GET':
		unmSummary = get_progress (request.user.id)
		userTopic = UserTopic.objects.filter (
			user_id=request.user.id).select_related(
				'topic', 'topic__cuser', 'topic__cuser__profile'
			)
		utvl = userTopic.values_list('topic_id',flat=True)
		suggestedTopic = Topic.objects.exclude (
			id__in=utvl).select_related(
				'cuser','cuser__profile')

		return render(request, "ucm/member-db-main.html", {
				'context':context,
				'userTopic':userTopic,
				'unmSummary':unmSummary,
				'suggestedTopic': suggestedTopic,			
			}
		)
	else:
		raise Http404

@login_required (redirect_field_name='next')
@transaction.atomic
def member_profile (request, pk=0, template_name='ucm/member-profile.html'):
	if request.method == 'POST':
		post = request.POST.copy() # to make it mutable
		# post ['email'] = request.user.email
		# post ['username']= request.user.username
		# post ['password2'] = request.user.password
		# post ['password1'] = request.user.password
		userForm = UserForm(data=post, instance=request.user)
		profileForm = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
	
#		if userForm.is_valid() and profileForm.is_valid():
#			userForm.save()
		if profileForm.is_valid():
			profileForm.save()
			messages.success (request, 'Your profile updated successfully!')
			return redirect('ucm:member_profile')
		else:
			# for e in userForm.errors:
			# 	messages.error (request, e)
			for e in profileForm.errors:
				messages.error (request, e)				
			messages.error(request, 'Please correct the error below.')
	else:
		userForm = UserForm (instance=request.user)
		profileForm = ProfileForm (instance=request.user.profile)

	context = {
		'ptitle': "Member Profile",
		'userForm': userForm,
		'profileForm': profileForm,
	}
	return render (request, template_name, {'context':context})

@login_required (redirect_field_name='next')
def member_network (request, template_name='ucm/coming-soon.html'):
	context = {
		"ptitle":'My Network'
	}
	return render(request, template_name, {'context':context})

@login_required (redirect_field_name='next')
def member_messaging (request, template_name='ucm/coming-soon.html'):
	context = {
		"ptitle":'Messaging'
	}
	return render(request, template_name, {'context':context})

@login_required (redirect_field_name='next')
def compose_topic (request, pk, template_name='ucm/compose-topic.html'):
	context = {'ptitle': "Manage Topic"}
	print ("Topic: ", pk)
	topic = None
	if (pk != 0):
		topic = get_object_or_404(Topic, pk=pk)
	else:
		topic = Topic ()
	if request.method == 'POST':
		print ('POST User---------> ', request.user)		
		print (request.POST)
		imagefile = request.FILES.get('imagefile', None)

		if imagefile is not None:
			print (request.FILES['imagefile'])
#		topic = get_object_or_404(Topic, pk=pk)			
		form = TopicForm (request.POST, request.FILES, instance=topic)
		context ['topicForm'] = form
		if form.is_valid():
			print ("111 -> IsValid passed")
			instance = form.save (commit=False)
			instance.cuser = request.user
			instance.muser = request.user
			instance.save ()
			pk = instance.id

			msg = "New topic {} ({}) saved succesfully".format (instance.title, instance.id)
			print (msg)
			messages.success (request, msg)
		else:
			print ("111 -> IsValid failed")
			messages.error (request, form.errors)
			print ("Form Error", form.errors)

		return redirect('ucm:compose_topic', pk=pk)
	elif request.method == 'GET':
		topicForm = TopicForm (instance=topic)

		context ['topicForm'] = topicForm
	else:
		raise Http404

	return render(request, template_name, {'context':context})

@login_required (redirect_field_name='next')
def compose_note (request, pk, npk=0, template_name='ucm/compose-note.html'):
	context = {
		'ptitle': "Manage Topic",
		'topic_id': pk,
	}

	topic = Topic.objects.filter (pk=pk)
	if not topic:
		errormsg = "TOPIC [" + str (pk) + "] not found"
		messages.error (request, errormsg)
		raise ObjectDoesNotExist (errormsg)

	notem_all = Notem.objects.filter(topic__id=pk)	# TODO:// Handle no object found
	context ['notem']  = notem_all

	if not notem_all:	# No notes, so create new instance
		notem = Notem.objects.none()
		noted = Noted.objects.none()
	else:
		# Decide the current NoteM to be processed
		if npk == 0:
			npk = notem_all.first().id

		notem = Notem.objects.filter (topic__id=pk, pk=npk)		
		if not notem:
			errormsg = "TOPIC [" + str (pk) + "] NOTE [" +  str (npk) + "] not found"
			messages.error (request, errormsg)
			return redirect('ucm:note', pk=pk)

		noted = Noted.objects.only ('ntype', 'ndata', 'norder').filter(notem__id = npk).order_by ('norder')

	print ("PK Here ", pk, npk)
	if request.method == 'POST':
		# if (npk== -1): # POST without Note Primary Key
		# 	raise Http404
		print ('POST User---------> ', request.user)
#		print (request.POST)
		# imagefile = request.FILES.get('imagefile', None)
		# if imagefile is not None:
		# 	print (request.FILES['imagefile'])
		# # else:
    	# # 	return redirect('/nofile/' {'foo': bar})			
		# form = TopicForm (request.POST, request.FILES)
		# if form.is_valid():
		# 	instance = form.save (commit=False)
		# 	instance.cuser = request.user
		# 	instance.muser = request.user
		# 	instance.save ()
		# else:
		# 	messages.error (request, form.errors)
		formsetNotem = NotemFormSet(request.POST, queryset=notem, prefix='notem')
		formsetNoted = NotedFormSet(request.POST, instance=notem.first(), prefix='noted')			
#		print ("FormSet=========>: ", formset)	
#		print ("formsetNotem====>: ", formsetNotem)
		print ('---------> 1.1')
		notem_deleteFlag = False
		notem_insertFlag = False
		if formsetNotem.is_valid():
			print ('---------> 1.2')			
			instanceNotem = formsetNotem.save(commit=False)

			for obj in formsetNotem.deleted_objects:
				notem_deleteFlag = True
				obj.delete()

			for i in instanceNotem:
				print ('---------> 1.3')
				if not i.id:
					notem_insertFlag = True
					i.cuser = request.user
					i.topic = topic.first()
					i.save()
					print ("New NoteM Created ==>", npk)
					npk = i.id
				else:
					i.save()
		else:
			print ('---------> 1.4')
			print ("formsetNotem.errors =>", formsetNotem.errors)

			messages.error (request, "Note Master Errors:")
			for e in formsetNotem.errors:
				messages.error (request, e)
			
			return redirect('ucm:noted', pk=pk, npk=(0 if notem_deleteFlag else formsetNoted.instance.id))

		print ('---------> 1.4.1')
		if not notem_deleteFlag:
			if formsetNoted.is_valid():
				print ('---------> 1.5')
				formsetNotem.save (commit=True)
	#			print ("formset:", formset.instance.id)
				instances = formsetNoted.save(commit=False)

				for obj in formsetNoted.deleted_objects:
					obj.delete()

				for instance in instances:
					print ('---------> 1.6')
					if not instance.id:
						instance.cuser = request.user
						print ("New Noted Instance: >>", instance)
						
					print ("Old Noted Instance: >>", instance.notem,
						"<>", instance.ntype, "<>", instance.ndata, "<>", instance.audio,
						"<>", instance.norder, "<>", instance.cuser, "<>", instance.cdate,
						"<>", instance.id)						
					instance.save()
				messages.success (request, "Changes saved successfully")
				return redirect('ucm:compose_noted', pk=pk, npk=(0 if notem_deleteFlag else npk))
			else:
				print ('---------> 1.7')
				print ("formsetNotem.errors =>", formsetNoted.errors)
				messages.error (request, "Note Details Errors:")
				for e in formsetNoted.errors:
					messages.error (request, e)
				return redirect('ucm:compose_noted', pk=pk, npk=(0 if notem_deleteFlag else npk))
		else:
			messages.success (request, "Changes saved successfully")
			return redirect('ucm:compose_noted', pk=pk, npk=(0 if notem_deleteFlag else formsetNoted.instance.id))
	elif request.method == 'GET':
		print ('---------> 1.8')
		formsetNotem = NotemFormSet (queryset=notem, prefix='notem')
		formsetNoted = NotedFormSet (instance=notem.first() if notem_all else None, 
			queryset=noted if notem_all else None, prefix='noted')
		# formsetNotem = NotemFormSet (queryset=notem, prefix='notem')
		# formsetNoted = NotedFormSet (prefix='noted')

		context ['formsetNotem'] = formsetNotem
		context ['formsetNoted'] = formsetNoted		
	else:
		raise Http404

	return render(request, template_name, {'context':context})

def is_ajax(request):
    """
    This utility function is used, as `request.is_ajax()` is deprecated.
    This implements the previous functionality. Note that you need to
    attach this header manually if using fetch.
    """
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

@login_required ()
@require_GET
def feed (request):
	context = {
		'ptitle': "Feed",
		'member_info': False,
	}
	all_feeds =  UserLearningDeck.objects.order_by('-cdate').filter (
		usernotem__usertopic__user=request.user, 
		usernotem__usertopic__status=0).select_related (
	 		'usernotem', 'usernotem__notem', 'usernotem__notem__topic',
			 'usernotem__notem__topic__cuser', 'usernotem__notem__topic__cuser__profile',
			 )
	paginator = Paginator(all_feeds, per_page=5)
	page_num = int(request.GET.get("page", 1))
	if page_num > paginator.num_pages:
		raise Http404
	feeds = paginator.page(page_num)

	context ['feeds'] = feeds
#	print (r"SQL: {}".format(feeds.object_list.query))
	if is_ajax(request):
		# R = render(request, 'ucm/index-feeds.html', {'context': context})
		# data = str(R.content)		
		# print (data)
		return render(request, 'ucm/index-feeds.html', {'context': context})
	else:
		# R = render(request, 'ucm/index.html', {'context': context})
		# data = str(R.content)		
		# print (data)
		return render(request, 'ucm/index.html', {'context': context})

@login_required (redirect_field_name='next')
@require_POST
def topic_add_note (request):
	reason = CsrfViewMiddleware().process_view(request, None, (), {})
	if reason:
		# CSRF failed
		messages.error (request, "CSRF check failed")
		raise PermissionException() # do what you need to do here

	if request.POST.get('post') == 'Post':  # Block for post notes on task
		print ("topic_review::POST:post================================>>")
		formReviewLog  = ReviewLogForm (data=request.POST)
		if formReviewLog.is_valid():
			unm=formReviewLog.cleaned_data.get ('usernotem')
			print ('Adding Notes--------------->', request.user, '->', unm.id)
			formReviewLog.save ()
			messages.success (request, 'New note added')
		else:
			messages.error (request, formReviewLog.errors)
			print ("Post::post::Form Validation failed")

	next = request.POST.get('next', '/')
	return HttpResponseRedirect (next)

@query_debugger
@login_required (redirect_field_name='next')
@require_POST
def topic_add_review (request):
	reason = CsrfViewMiddleware().process_view(request, None, (), {})
	if reason:
		# CSRF failed
		messages.error (request, "CSRF check failed")
		raise PermissionException() # do what you need to do here

	nextdeck = 0
	uldid = request.POST.get ('uldid', 0)
	if 'r_0' in request.POST:	# Easy
		ueval = 0
	elif 'r_1' in request.POST: # Difficult
		ueval = 1
	elif 'r_2' in request.POST: # Very Difficult
		ueval = 2

	# Update deck details in UserNotem and create a log entry in UserNotemLog
	uld = UserLearningDeck.objects.filter (id = uldid).first()
	if not uld:
		errormsg = "Integrity error.  Invalid note details received for learning deck card: " + str (uldid)
		messages.error (request, errormsg)
		raise ObjectDoesNotExist(errormsg)

	nextdeck = calculateNextDeck (request, uld, ueval)
	if nextdeck < 0:
		next = request.POST.get('next', '/')
		return HttpResponseRedirect (next)

	unm = UserNotem.objects.filter (id = uld.usernotem.id).first()
	if not unm:
		errormsg = "Integrity error.  Notem not found for learning deck card: " + str (uldid)
		messages.error (request, errormsg)
		raise ObjectDoesNotExist(errormsg)

	print ("Next Deck: ", nextdeck, " Current Deck: ", unm.currdeck)
	if nextdeck == unm.currdeck:
		uld.cdate = timezone.now ()
		uld.save()
	else:
		uld.delete()

	unm.currdeck = nextdeck
	unl = UserNotemLog (usernotem=unm, currdeck=unm.currdeck, ueval=ueval, nextdeck=nextdeck)
	ut = UserTopic.objects.filter (id = unm.usertopic.id).first()
		
	unm.save()
	unl.save ()
	ut.save ()

	next = request.POST.get('next', '/')
	return HttpResponseRedirect (next)