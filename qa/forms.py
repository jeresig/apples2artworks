from django import forms
from django.db import models
from django.forms import fields, widgets

class AnswerForm( forms.ModelForm ):
	user = fields.HiddenInput()
	artwork = fields.HiddenInput()
	responses = fields.MultipleChoiceField( required = True )

	class Meta:
		model = Answer
