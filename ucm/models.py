from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.core.files.base import ContentFile

from . import constants

NOTE_TYPES = (
	('title', 'Title'),
	('text',  'Text'),
	('image', 'Image'),
	('url',   'URL'),
	('html',  'HTML'),
	('example','Example'),
)

SR_METHODS = (
	(constants.LBOXP, 'Leitnes Box - Progressive'),
	(constants.LBOXR, 'Leitnes Box - Restart'),
)

IMG_SIZE_H_TOPIC = 333
IMG_SIZE_W_TOPIC = 711

class ResizeImageMixin:
	def resize(self, imageField: models.ImageField, t_height, t_width):

		height = imageField.height 
		width = imageField.width
		print (r"Max H {}, Max W {}, Image H {}, Image W {}".format (t_height, t_width, height, width))

		if width != t_width or height != t_height:
			print ("===============> Resizing Image")
			imageField.open()
			im = Image.open(imageField)  # Catch original
			im.load()
			source_image = im.convert('RGB')
			source_image = source_image.resize((t_width, t_height), Image.ANTIALIAS)  # Resize to size
			output = BytesIO()
			source_image.save(output, format='JPEG') # Save resize image to bytes
			output.seek(0)

			content_file = ContentFile(output.read())  # Read output and create ContentFile in memory
			file = File(content_file)

			random_name = f'{uuid.uuid4()}.jpg'
			imageField.save(random_name, file, save=False)

def has_changed(instance, field):
	if not instance.pk:
		return True
	
	old_value = instance.__class__._default_manager.\
		filter(pk=instance.pk).values(field).get()[field]
	return not getattr(instance, field) == old_value

def validate_image(imagefile):
	max_height = 333
	max_width = 711
	
	height = imagefile.height 
	width = imagefile.width

	print (r"Max H {}, Max W {}, Image H {}, Image W {}".format (max_height, max_width, height, width))

	if width > max_width or height > max_height:
		raise ValidationError("Height or Width is larger than what is allowed")

class Topic (models.Model, ResizeImageMixin):
	title = models.CharField (max_length=120)
	description = models.CharField (max_length=600)
	imagename = models.CharField (max_length=60)
	imagefile = models.ImageField("Topic Image", upload_to='images', default='images/topic_img_default.jpg') #, validators=[validate_image])	
	cuser = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate = models.DateTimeField (auto_now_add=True)
	mdate = models.DateTimeField (auto_now=True)

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		if has_changed(self, 'imagefile'):
			self.resize(self.imagefile, IMG_SIZE_H_TOPIC, IMG_SIZE_W_TOPIC)

		super().save(*args, **kwargs)

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

	@property
	def sorted_noted_set(self):
		return self.noted_set.order_by('norder')

class Noted (models.Model):
	notem = models.ForeignKey(Notem, related_name='noted_set', on_delete=models.CASCADE)
	ntype = models.CharField (max_length=10, choices=NOTE_TYPES)
	ndata = models.CharField (max_length=1024)
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
	status = models.PositiveSmallIntegerField (null=False, default=0) # 0- Ready, 1-Paused

	def __str__(self):
		return str (self.user) + ':' + str (self.topic)

	class Meta:
		verbose_name = "User Topic"
		verbose_name_plural = "User Topics"

class UserNotem (models.Model):
	usertopic = models.ForeignKey('UserTopic', on_delete=models.CASCADE)
	notem     = models.ForeignKey(Notem,on_delete=models.CASCADE)
	currdeck  = models.PositiveSmallIntegerField (null=False, blank=True, default=0)
	cdate     = models.DateTimeField (auto_now_add=True)
	mdate     = models.DateTimeField (auto_now=True)

	def __str__(self):
		return str (self.usertopic) + ':' + str (self.notem) + ':' + str (self.currdeck)

	@property
	def sorted_reviewlog_set (self):
		return self.reviewlog_set.order_by('-cdate')		

class UserLearningDeck (models.Model):
	cuser     = models.ForeignKey(User,on_delete=models.CASCADE)
	usernotem = models.ForeignKey(UserNotem, related_name='uld_set', on_delete=models.CASCADE)
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
	usernotem = models.ForeignKey(UserNotem, related_name='reviewlog_set', on_delete=models.CASCADE)
	notes     = models.CharField (max_length=300, help_text='User log inforation ...', blank=False)
	cuser     = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate     = models.DateTimeField (auto_now_add=True)

	def __str__(self):
		return self.notes + ' (' + self.cuser + ')'

class Invitation (models.Model):
	cuser        = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate        = models.DateTimeField (auto_now_add=True)
	mdate        = models.DateTimeField (auto_now=True)
	hash_string  = models.CharField (max_length=256,  unique=True)
	inv_type     = models.CharField (blank=False, max_length=10, default='None')
	inv_type_id  = models.IntegerField (blank=False, default=0)
	to_name      = models.CharField (max_length=60)
	to_email     = models.CharField (max_length=80)
	acceptedflag = models.BooleanField (default=False)
