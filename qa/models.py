from django import forms
from django.db import models
from django.forms import fields, widgets
from tinymce import models as tinymce_models
from userena.models import UserenaBaseProfile
from django.contrib.auth.models import User
from a2a.settings import LEVEL_SIZE

TYPE_CHOICES = (
	( 'radio', 'Single Select' ),
	( 'checkbox', 'Multiple Select' ),
)

class Question(models.Model):
	short_name = models.CharField( max_length = 20 )
	question = models.CharField( max_length = 255 )
	tip = tinymce_models.HTMLField( default = '', blank = True )
	type = models.CharField( max_length = 20, choices = TYPE_CHOICES, default = 'radio' )

	video_url = models.CharField( max_length = 255, blank = True )
	logo = models.ImageField( upload_to = 'logos', null = True, blank = True )
	badge_small = models.ImageField( upload_to = 'badges', null = True, blank = True )
	badge_large = models.ImageField( upload_to = 'badges', null = True, blank = True )

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

	last_seen_artwork = models.ForeignKey( Artwork, null = True, blank = True )
	last_seen_question = models.ForeignKey( Question, null = True, blank = True )

class Answer(models.Model):
	user = models.ForeignKey( User )
	artwork = models.ForeignKey( Artwork )
	question = models.ForeignKey( Question )
	responses = models.ManyToManyField( Response )
	data = models.CharField( max_length = 255, default = '' )
	hidden = models.BooleanField( "Hidden Answer", default = False )
	answered_date = models.DateTimeField( auto_now_add = True )

	def __unicode__(self):
		return u'User %s answer to %s' % ( self.user, self.artwork )

class AnswerForm( forms.ModelForm ):
	responses = forms.ModelMultipleChoiceField(
		required = True,
		queryset = Response.objects.all(),
		widget = widgets.CheckboxSelectMultiple()
	)

	class Meta:
		model = Answer
		fields = [ 'responses' ]

class Challenge(models.Model):
	short_name = models.CharField( max_length = 20 )
	question = models.CharField( max_length = 255 )
	tip = tinymce_models.HTMLField( default = '', blank = True )
	random = models.BooleanField( "Comes up randomly", default = True )

	video_url = models.CharField( max_length = 255, blank = True )
	logo = models.ImageField( upload_to = 'logos', null = True, blank = True )
	badge_small = models.ImageField( upload_to = 'badges', null = True, blank = True )
	badge_large = models.ImageField( upload_to = 'badges', null = True, blank = True )

	class Meta:
		verbose_name = 'Advanced Question'
		verbose_name_plural = 'Advanced Questions'

	def __unicode__(self):
		return self.short_name

class ChallengeAnswer(models.Model):
	user = models.ForeignKey( User )
	challenge = models.ForeignKey( Challenge )
	answer = models.ForeignKey( Answer )
	other_answer = models.ForeignKey( Answer, null = True, blank = True, related_name = 'other_answer_set' )
	response = models.TextField()
	response_date = models.DateTimeField( auto_now_add = True )

	class Meta:
		verbose_name = 'Advanced Answer'
		verbose_name_plural = 'Advanced Answers'

	def __unicode__(self):
		return u'User %s response to %s' % ( self.user, self.answer )

class AdvAnswerForm( forms.ModelForm ):
	class Meta:
		model = ChallengeAnswer
		fields = [ 'response' ]

class Level(models.Model):
	user = models.ForeignKey( User )
	question = models.ForeignKey( Question )
	adv_artwork = models.ForeignKey( Artwork, null = True, blank = True )
	answered = models.IntegerField( default = 0 )
	last_updated = models.DateTimeField( auto_now = True )

	def level(self):
		return int( self.answered / LEVEL_SIZE ) + 1
