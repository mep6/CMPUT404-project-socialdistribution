from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
#---------------------------------------------------------------------------------------------
# PROFILE AND USER STUFF
@python_2_unicode_compatible
class Profile(models.Model):
    #userId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    displayName = models.CharField(max_length=200)
    githubUsername = models.CharField(max_length=200)
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    email = models.CharField(max_length=400)
    bio = models.CharField(max_length=2000)
    #TODO: put friends list and posts in here

#the following lines onward are from here:
#https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):  # __unicode__ for Python 2
        return self.user.username

#these two functions act as signals so a profile is created/updated and saved when a new user is created/updated.
@receiver(post_save,sender=User)
def create_user_profile(sender,instance, created, **kwargs):
    if created:
         Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender,instance, **kwargs):
    instance.profile.save()


#END PROFILE AND USER STUFF
#-----------------------------------------------------

#POSTS AND COMMENTS

#taking influence from http://pythoncentral.io/writing-models-for-your-first-python-django-application/
#because I have no idea what im doing

class Post(models.Model):
	#assuming links would go in as text? may have to change later
	posted_text = models.CharField(max_length =2000) 
	date_created = models.DateTimeField('DateTime created')
	post_privacy = 1


class Comment(models.Model):
	associated_post= models.ForeignKey(Post)
	comment = models.TextField()
	date_created = models.DateTimeField('DateTime created')

