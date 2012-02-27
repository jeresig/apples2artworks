import random
from a2a.qa.models import *
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django import forms
from django.forms import widgets
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from a2a.settings import LEVEL_SIZE

def index( request ):
	return render_to_response( 'index.html', {}, context_instance = RequestContext(request) )

def question( request ):
	user = request.user

	# The user needs to be signed in in order to answer a question
	if not user.is_authenticated():
		return HttpResponseRedirect( '/accounts/signin/?next=%s' % request.path )

	if request.method == "POST":
		form = AnswerForm( request.POST )

		if form.is_valid():
			question = Question.objects.get( id = int(request.POST['id_question']) )
			artwork = Artwork.objects.get( id = int(request.POST['id_artwork']) )

			# We should never get to the point where this doesn't exist
			level = Level.objects.get( user = user, question = question )

			# The user just answered a good question
			if level.answered % LEVEL_SIZE == 0:
				level.adv_artwork = artwork

			level.answered += 1

			level.save()

			# Need to save the answer now
			answer = form.save( commit = False )

			# Need to populate these fields first
			answer.user = user
			answer.artwork = artwork
			answer.question = question
			answer.save()
			form.save_m2m()

			# Let the user answer another question
			return HttpResponseRedirect( '/question/' )

	# Find an artwork/question pair for the user to comment on
	( artwork, question, hard ) = find_question( user )
	responses = question.response_set.all()

	form = AnswerForm()

	# Some questions only have one selection
	if question.type == 'radio':
		form.fields["responses"].widget = widgets.RadioSelect()

	# Reduce the responses to just those on the question
	form.fields["responses"].queryset = responses

	return render_to_response( 'question.html', {
		'question': question,
		'artwork': artwork,
		'hard': hard,
		'form': form
	}, context_instance = RequestContext(request) )

def find_question( user ):
	profile = user.get_profile()
	questions = Question.objects.all()

	# Get the 3 most recent answers
	recent_answers = list( user.answer_set.order_by("-answered_date")[:3] )

	# Exclude the most recently answered question
	if len( recent_answers ):
		questions = questions.exclude( id = recent_answers[0].question.id )

	# Don't show the most recently shown question
	if profile.last_seen_question:
		questions = questions.exclude( id = profile.last_seen_question.id )

	# Shuffle the remaining questions
	questions = list( questions )

	random.shuffle( questions )

	# Make sure we don't repeat recent artworks
	recent_images = [ a.artwork.id for a in recent_answers ]

	# Prevent the most recently seen artwork from being seen again
	if profile.last_seen_artwork:
		recent_images.append( profile.last_seen_artwork.id )

	# We loop here so that if a question has been
	# exhausted we fall back to other options
	for question in questions:
		level = None

		# Get the level for the user, for this question
		try:
			level = user.level_set.get( question = question )

		# If it does not exist then the user has never answered
		# a question of this type, so we need to start logging it
		except ObjectDoesNotExist:
			level = Level( user = user, question = question )
			level.save()

		pos = level.answered % LEVEL_SIZE
		artwork = None
		hard = False

		# Show hard question
		if pos == LEVEL_SIZE - 1:
			artwork = level.adv_artwork
			hard = True

		# Pick a filler artwork
		# or a new good artwork
		else:
			# Prune out already-answered artworks
			old_answers = Answer.objects.filter( user = user, question = question )
			bad_images = [ a.artwork.id for a in old_answers ]
			bad_images.extend( recent_images )

			# Also prune out artworks that don't match this question well
			artworks = Artwork.objects.exclude( id__in = bad_images ).exclude( bad_questions = question )

			# Pick a filler artwork
			if pos != 0:
				artworks = artworks.exclude( good_questions = question )

			# Pick a good artwork
			else:
				artworks = artworks.filter( good_questions = question )

			# Grab a random artwork
			try:
				artwork = artworks.order_by( '?' )[0]

			# No artwork found
			except IndexError:
				artwork = None

		# Pick this artwork and question
		if artwork:
			profile.last_seen_artwork = artwork
			profile.last_seen_question = question
			profile.save()

			return ( artwork, question, hard )

	# No suitable artwork/question pair was found
	return ( None, None, false )
