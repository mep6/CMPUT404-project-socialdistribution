#code from http://pythoncentral.io/how-to-use-python-django-forms/

from django import forms
from datetime import datetime
 
class PostForm(forms.Form):
    title = forms.CharField(max_length = 100)
    content = forms.CharField(max_length=2000)
    published = forms.DateTimeField()

    CHOICES=[('PUBLIC','Public'),
         ('FRIENDS','Friends'),
	 ('FOAF', 'Friend of A Friend'),
	 ('PRIVATE', 'Private'),
	 ('SERVERONLY', 'Members of this server only')]

    choose_Post_Visibility = forms.ChoiceField(choices=CHOICES, required=True )
class CommentForm(forms.Form):
    comment = forms.CharField(max_length=2000)
    date_created = forms.DateTimeField()
