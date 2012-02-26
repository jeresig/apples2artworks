from a2a.qa.models import *
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django import forms
from django.forms import widgets
from django.template import RequestContext

def index( request ):
	return render_to_response( 'index.html', {}, context_instance = RequestContext(request) )

def question( request ):
	if not request.user.is_authenticated():
		return HttpResponseRedirect( '/accounts/signin/?next=%s' % request.path )

	if request.method == "POST":
		form = AnswerForm( request.POST )

		if form.is_valid():
			answer = form.save( commit = False )
			answer.user = request.user
			answer.artwork = Artwork.objects.get( id = int(request.POST['id_artwork']) )
			answer.question = Question.objects.get( id = int(request.POST['id_question']) )
			answer.save()
			form.save_m2m()

			return HttpResponseRedirect( '/question/' )

	artwork = Artwork.objects.order_by('?')[0]
	question = Question.objects.order_by('?')[0]
	responses = question.response_set.all()

	form = AnswerForm()

	if question.type == 'radio':
		form.fields["responses"].widget = widgets.RadioSelect()

	form.fields["responses"].queryset = responses

	return render_to_response( 'question.html', {
		'question': question,
		'artwork': artwork,
		'form': form
	}, context_instance = RequestContext(request) )
