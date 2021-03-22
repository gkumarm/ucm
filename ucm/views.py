from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import ObjectDoesNotExist
import random
from django.db.models import Q, Count
import logging
from django.utils import timezone
from datetime import datetime

from .decorators import query_debugger
from .models import UserNotem, Noted, UserNotemLog, UserTopic, UserLearningDeck, ReviewLog, Topic
from .forms import ReviewLogForm

from . import constants
from uauth import util as util
from rest_framework import views
from rest_framework.response import Response
from .serializers import YourSerializer

# l = logging.getLogger('django.db.backends')  
# l.setLevel(logging.DEBUG)
# l.addHandler(logging.StreamHandler())   

# Create your views here.
def home(request):
	if request.user.is_authenticated:
		return buildHome (request)
#		return HttpResponseRedirect(reverse('ucm:review'))
	else:
		return render(request, "uauth/login.html")

@login_required
def buildHome (request):
	if request.method == 'GET':
		# rand_id = random.randint(1, 100)
		unmSummary = get_progress (request.user)
		userTopic = UserTopic.objects.filter (user=request.user)
		utvl = userTopic.values_list('topic_id',flat=True)
		otherTopic = Topic.objects.exclude (id__in=utvl)
#		print (userTopic)
		return render(request, "ucm/home.html", {
			'userTopic' : userTopic,
			'unmSummary': unmSummary,
			'otherTopic': otherTopic,}
		)
	else:
		raise Http404

@login_required
def subscribe (request, pk=0):
	if request.method == 'GET':
		print ("subscribe-subscribe-subscribe-subscribe:", pk)		
		t=Topic.objects.filter (pk=pk).first()
		if not t:
			messages.info (request, "Selected topic not found for subscription")
		else:
			messages.info (request, "Topic [" + t.title + "] subscribed successfully. Enjoy learning")

		util.subscribe_topic (request.user.id, pk, request)

		return HttpResponseRedirect(reverse('ucm:home'))
# 		unmSummary = get_progress (request.user)
# 		userTopic = UserTopic.objects.filter (user=request.user)
# 		utvl = userTopic.values_list('topic_id',flat=True)
# 		otherTopic = Topic.objects.exclude (id__in=utvl)
# #		print (userTopic)
# 		return render(request, "ucm/home.html", {
# 			'userTopic' : userTopic,
# 			'unmSummary': unmSummary,
# 			'otherTopic': otherTopic,}
# 		)
# 	else:
# 		raise Http404

@query_debugger
@login_required (redirect_field_name='next')
def review (request, pk=0, learn_more=False, template_name='ucm/review.html'):
	filters = Q()
	if request.method == 'POST':
		reason = CsrfViewMiddleware().process_view(request, None, (), {})
		if reason:
			# CSRF failed
			messages.error (request, "CSRF check failed")
			raise PermissionException() # do what you need to do here

		if request.POST.get('post') == 'Post':  # Block for post notes on task
			formReviewLog  = ReviewLogForm (data=request.POST)
			if formReviewLog.is_valid():
				unm=formReviewLog.cleaned_data.get ('usernotem')
				print ('Adding Notes--------------->', request.user, '->', unm.id)
				formReviewLog.save ()
				messages.success (request, 'New note added')
				return HttpResponseRedirect(reverse('ucm:review',  args=(unm.usertopic.id,)))

		print (request.POST)
		nextdeck = 0
		ritem = request.POST.get ('ritem', " Empty")
		usernoteid = request.POST.get ('usernoteid', 0)
		if 'r_0' in request.POST:	# Easy
			ueval = 0
		elif 'r_1' in request.POST: # Difficult
			ueval = 1
		elif 'r_2' in request.POST: # Very Difficult
			ueval = 2

		# Update deck details in UserNotem and create a log entry in UserNotemLog
		uld = UserLearningDeck.objects.filter (id = usernoteid).first()
		if not uld:
			errormsg = "Integrity error.  Invalid note details received for learning deck card: " + str (usernoteid)
			messages.error (request, errormsg)
			raise ObjectDoesNotExist(errormsg);

		nextdeck = calculateNextDeck (request, uld, ueval)
		if nextdeck < 0:
			return render(request, template_name, {})

		unm = UserNotem.objects.filter (id = uld.usernotem.id).first()
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

#		filters = Q(Q(usernotem__usertopic_id=userNote.usertopic.id) & Q(usernotem__currdeck=0))
		return HttpResponseRedirect(reverse('ucm:review',  args=(ut.id,)))
	elif request.method == 'GET':
		# 1. Check in the learning deck for pendng cards
		# 2. If pending found, proceed
		# 3. If no pending,
		# 3.1 If curr date is same as modified date in user topic, then ask user whether to create next learning deck
		# 3.2 If curr date is not same, create new learning deck
		print ('User---------> ', request.user)
		ut = UserTopic.objects.filter (id=pk, user=request.user).first()
		if not ut:
			messages.info (request, "Not a subscribed topic")
			return render(request, template_name, {'flag':'not_subscribed', 'topic':pk})

		filters = Q(Q(usernotem__usertopic_id=pk))# & Q(usernotem__currdeck=1))
		uld = UserLearningDeck.objects.filter (filters).first()
		if not uld:
			if datetime.strftime(timezone.now(), '%Y%m-%d') == datetime.strftime(ut.mdate, '%Y%m-%d') and learn_more == False:
				messages.success (request, "You have no cards pending to learn today")
				return render(request, template_name, {'flag':'learn_more', 'topic':pk})
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
		# else:
		# 	messages.success (request, "Resuming with previous decks")	
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
		});


	return render(request, template_name, {'userNote':uld, 'note':nd, 
		'reviewLog':reviewLog, 'formReviewLog':formReviewLog ,})

def get_progress (user):
 # 0. card_count = 10; NEXT_BOX = 0
 # 1. no_of_cards_from_NEXT_BOX = card_count : if count() > card_count ? card_count : sum ()
 # 2. Review count = card_count + (card_count - no_of_cards_from_NEXT_BOX)
 # 3. NEXT_BOX = NEXT_BOX + 1
 # 4. Calculate % of cards to be taken from next BOX
 # 5.1 % share of next BOX = round (card_count_NEXT_BOX/count (cards from all boxes starting from NEXT_BOX)*100)
 # 5.2 Repeat step 1

#	unm = UserTopic.objects.filter (user=user)
	unm = UserNotem.objects \
		.filter (usertopic__in = UserTopic.objects.filter (user=user)) \
		.values('usertopic_id', 'currdeck') \
		.annotate(total=Count('currdeck')) \
		.order_by('usertopic_id', 'currdeck')

	for x in unm:
		print (x)
		gtotal = sum (y ['total'] for y in unm if y ['usertopic_id'] == x ['usertopic_id'])
		print ('------------>', gtotal)
		x ['percentage'] = round ((x ['total']/gtotal)*100)
		print (x)

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
@login_required
def more (request):
	if request.method == 'GET':
		return review (request, learn_more=True)
#		return buildHome (request)		
	else:
		print ("------------------> POST", request.POST)
		request.method = 'GET'
		return review (request, pk=request.POST.get ('ritem', 0), learn_more=True)		
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