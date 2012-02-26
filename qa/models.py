from django import forms
from django.db import models
from django.forms import fields, widgets
from tinymce import models as tinymce_models
from userena.models import UserenaBaseProfile
from django.contrib.auth.models import User

TYPE_CHOICES = (
	( 'radio', 'Single Select' ),
	( 'checkbox', 'Multiple Select' ),
)

class Question(models.Model):
	question = models.CharField( max_length = 255 )
	tip = tinymce_models.HTMLField( default = '', blank = True )
	type = models.CharField( max_length = 20, choices = TYPE_CHOICES, default = 'radio' )
	video_url = models.CharField( max_length = 255, blank = True )

	advanced_question = models.CharField( max_length = 255, blank = True )
	advanced_tip = tinymce_models.HTMLField( default = '', blank = True )

	def __unicode__(self):
		return self.question

class Artwork(models.Model):
	title = models.CharField( max_length = 255 )
	artist = models.CharField( max_length = 255 )
	image = models.ImageField( upload_to = 'artwork/%Y/%m/%d' )
	good_questions = models.ManyToManyField( Question, verbose_name = "good questions", related_name = "good_set", blank = True )
	bad_questions = models.ManyToManyField( Question, verbose_name = "bad questions", related_name = "bad_set", blank = True )

	def __unicode__(self):
		return self.title

class ArtworkLink(models.Model):
	artwork = models.ForeignKey( Artwork )
	url = models.CharField( "URL", max_length = 255 )

	def __unicode__(self):
		return self.url

class Response(models.Model):
	question = models.ForeignKey( Question )
	response = models.CharField( max_length = 255 )
	trigger = models.BooleanField( "Triggers Advanced Question", default = True )

	def __unicode__(self):
		return self.response

class Profile(UserenaBaseProfile):
	user = models.OneToOneField( User,
		unique = True,
		verbose_name = 'user',
		related_name = 'my_profile' )

class Answer(models.Model):
	user = models.ForeignKey( User )
	artwork = models.ForeignKey( Artwork )
	question = models.ForeignKey( Question )
	responses = models.ManyToManyField( Response )

	def __unicode__(self):
		return u'User %s response to %s' % ( self.user, self.artwork )

class AnswerForm( forms.ModelForm ):
	responses = forms.ModelMultipleChoiceField( required = True, queryset = Response.objects.all(), widget = widgets.CheckboxSelectMultiple() )

	class Meta:
		model = Answer
		exclude = [ 'user', 'artwork', 'question' ]