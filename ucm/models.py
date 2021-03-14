from django.db import models
from django.contrib.auth.models import User

from . import constants

NOTE_TYPES = (
	('title', 'Title'),
	('text',  'Text'),
	('image', 'Image'),
	('url',   'URL'),
	('example','Example'),
)

SR_METHODS = (
	(constants.LBOXP, 'Leitnes Box - Progressive'),
	(constants.LBOXR, 'Leitnes Box - Restart'),
)

class Topic (models.Model):
	title = models.CharField (max_length=120)
	description = models.CharField (max_length=600)
	imagename = models.CharField (max_length=60)
	cuser = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate = models.DateTimeField (auto_now_add=True)
	mdate = models.DateTimeField (auto_now=True)

	def __str__(self):
		return self.title

	class Meta:
		verbose_name = "Topic"
		verbose_name_plural = "Topics"

class Notem (models.Model):
	topic = models.ForeignKey(Topic,on_delete=models.CASCADE)
	name  = models.CharField (max_length=120)
#	dease = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
#	dinterval = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
	cuser = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate = models.DateTimeField (auto_now_add=True)

	def __str__(self):
		return str (self.topic) + "::" + self.name

	class Meta:
		verbose_name = "Topic Note"
		verbose_name_plural = "Topic Notes"

class Noted (models.Model):
	notem = models.ForeignKey(Notem,on_delete=models.CASCADE)
	ntype = models.CharField (max_length=10, choices=NOTE_TYPES)
	ndata = models.CharField (max_length=612)
	audio = models.CharField (max_length=60, null=True, blank=True)
	norder= models.DecimalField (max_digits=2, decimal_places=0, null=True, blank=True)

	cuser = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate = models.DateTimeField (auto_now_add=True)

	def __str__(self):
		return str(self.notem) + ' (' + self.ntype + ')'

	class Meta:
		verbose_name = "Topic Note Detail"
		verbose_name_plural = "Topic Note Details"

class Template (models.Model):
	topic = models.ForeignKey(Topic,on_delete=models.CASCADE)
	value = models.CharField (max_length=60)
	vtype = models.CharField (max_length=10, choices=NOTE_TYPES)
	order = models.DecimalField (max_digits=2, decimal_places=0, null=True, blank=True)
	cuser = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate = models.DateTimeField (auto_now_add=True)

	def __str__(self):
		return self.topic	

class UserTopic (models.Model):
	user  = models.ForeignKey(User,on_delete=models.CASCADE)
	topic = models.ForeignKey(Topic,on_delete=models.CASCADE)
	srmethod = models.CharField (max_length=10, choices=SR_METHODS)
	maxdeck = models.PositiveSmallIntegerField (null=False, blank=False, default=3)
	dclimit = models.PositiveSmallIntegerField (null=False, blank=False, default=10)
	cdate = models.DateTimeField (auto_now_add=True)
	mdate = models.DateTimeField (auto_now=True)

	def __str__(self):
		return str (self.user) + ':' + str (self.topic)

	class Meta:
		verbose_name = "User Topic"
		verbose_name_plural = "User Topics"

class UserNotem (models.Model):
	usertopic = models.ForeignKey(UserTopic,on_delete=models.CASCADE)
	notem     = models.ForeignKey(Notem,on_delete=models.CASCADE)
	currdeck  = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
	cdate     = models.DateTimeField (auto_now_add=True)
	mdate     = models.DateTimeField (auto_now=True)

	def __str__(self):
		return str (self.usertopic) + ':' + str (self.notem) + ':' + str (self.currdeck)

class UserLearningDeck (models.Model):
	cuser     = models.ForeignKey(User,on_delete=models.CASCADE)
	usernotem = models.ForeignKey(UserNotem,on_delete=models.CASCADE)
	cdate     = models.DateTimeField (auto_now_add=True)
	def __str__(self):
		return str (self.usernotem) + ':->' + str (self.cdate)

class UserNotemLog (models.Model):
	usernotem = models.ForeignKey(UserNotem,on_delete=models.CASCADE)
	currdeck  = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
	ueval     = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
	nextdeck  = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
	cdate     = models.DateTimeField (auto_now_add=True)

	def __str__(self):
		return str (self.usernotem) + ':' + str (self.id)

class ReviewLog (models.Model):
	usernotem = models.ForeignKey(UserNotem,on_delete=models.CASCADE)
	notes     = models.CharField (max_length=300, help_text='User log inforation ...', blank=False)
	cuser     = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate     = models.DateTimeField (auto_now_add=True)

	def __str__(self):
		return self.notes + ' (' + self.cuser + ')'
		