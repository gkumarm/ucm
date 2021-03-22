from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	notificationflag = models.BooleanField (null=True, blank=True, default=True) 
	agreementflag    = models.BooleanField (null=True, blank=True, default=True)
	validatehash     = models.CharField (max_length=256,  unique=True)
	validatedflag    = models.BooleanField (null=False, default=False)
#	birth_date = models.DateField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()

class Invitation (models.Model):
	cuser      = models.ForeignKey(User,on_delete=models.CASCADE)
	cdate      = models.DateTimeField (auto_now_add=True)
	mdate      = models.DateTimeField (auto_now=True)
	hash_string= models.CharField (max_length=256,  unique=True)
	to_name    = models.CharField (max_length=60)
	to_email   = models.CharField (max_length=80)
	acceptedflag = models.BooleanField (default=False)
