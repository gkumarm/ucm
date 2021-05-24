from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

from ucm.models import ResizeImageMixin, has_changed

IMG_SIZE_H_PROFILE = 256
IMG_SIZE_W_PROFILE = 256

class Profile(models.Model, ResizeImageMixin):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	notificationflag = models.BooleanField (null=True, blank=True, default=True) 
	agreementflag    = models.BooleanField (null=True, blank=True, default=True)
	validatehash     = models.CharField (max_length=256, blank=True, null=True)
	validatedflag    = models.BooleanField (null=False, default=False)
	birth_date       = models.DateField(null=True, blank=True)
	phone_regex      = RegexValidator (regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
#	phone_number     = models.CharField(validators=[phone_regex], max_length=17, blank=True) # validators should be a list
	phone_number     = models.CharField(max_length=17, blank=True) # validators should be a list
	address_line_1   = models.CharField (max_length=60, blank=True)
	address_line_2   = models.CharField (max_length=60, blank=True)
	country          = models.CharField (max_length=4,  blank=True)
	imagefile        = models.ImageField(upload_to='images/prof_pics/', default='images/prof_pics/default.jpg')	

	def __str__(self):
		return self.user.first_name

	def save(self, *args, **kwargs):
		if has_changed(self, 'imagefile'):
			self.resize(self.imagefile, IMG_SIZE_H_PROFILE, IMG_SIZE_W_PROFILE)

		super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()

