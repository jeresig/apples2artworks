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

def adv_question( request ):
	user = request.user

	# The user needs to be signed in in order to answer a question
	if not user.is_authenticated():
		return HttpResponseRedirect( '/accounts/signin/?next=/question/' )

	if request.method == "POST":
		form = AdvAnswerForm( request.POST )

		if form.is_valid():
			# Need to save the answer now
			answer = form.save( commit = False )

			answer.user = user
			answer.challenge = Challenge.objects.get( id = int(request.POST['id_challenge']) )
			answer.answer = Answer.objects.get( id = int(request.POST['id_answer']) )

			# For type #2 (Challenge)
			if 'id_other_answer' in request.POST:
				answer.other_answer = Answer.objects.get( id = int(request.POST['id_other_answer']) )

			# For type #3 (Comparison)
			if 'id_artwork' in request.POST and 'id_response' in request.POST:
				artwork = Artwork.objects.get( id = int(request.POST['id_artwork']) )
				response = Response.objects.get( id = int(request.POST['id_response']) )
				other_answer = Answer( user = request.user, question = challenge.question, artwork = artwork, responses = response, hidden = True )
				other_answer.save()
				answer.other_answer = other_answer

			answer.save()

			# Let the user answer another question
			return HttpResponseRedirect( '/question/' )

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
	match = find_question( user )

	if match['question'] == None or match['artwork'] == None:
		# TODO: Bail out with an error message?
		return HttpResponseRedirect( '/' )

	if match['challenge'] == None:
		match['form'] = AnswerForm()

		# Some questions only have one selection
		if match['question'].type == 'radio':
			match['form'].fields['responses'].widget = widgets.RadioSelect()

		# Reduce the responses to just those on the question
		match['form'].fields['responses'].queryset = match['question'].response_set.all()

		return render_to_response( 'question.html', match,
			context_instance = RequestContext(request) )
	else:
		match['form'] = AdvAnswerForm()

		return render_to_response( 'adv_question.html', match,
			context_instance = RequestContext(request) )

def find_question( user ):
	ret = {
		'question': None,
		'artwork': None,
		'answer': None,
		'challenge': None
	}

	profile = user.get_profile()
	questions = Question.objects.all()

	# Get the 3 most recent answers
	recent_answers = list( user.answer_set.order_by("-answered_date")[:3] )

	if len( recent_answers ):
		answer = recent_answers[0]

		# Exclude the most recently answered question
		questions = questions.exclude( id = answer.question.id )

		# Sometimes we want to show an advanced question
		if random.random() < 0.5 and answer.question == profile.last_seen_question and answer.artwork == profile.last_seen_artwork:
			# Don't do the advanced question if we've already done one for this answer
			try:
				ChallengeAnswer.objects.get( answer = answer, user = user )

			except ObjectDoesNotExist:
				# Use the same question and artwork
				challenges = Challenge.objects.filter( random = True ).order_by( '?' )

				ret['question'] = answer.question
				ret['artwork'] = answer.artwork
				ret['answer'] = answer

				for challenge in challenges:
					# If it's a challenge, pass along other answer
					if challenge.id == 2:
						diff_responses = answer.question.response_set.exclude( pk__in = answer.responses.values_list('pk', flat = True) )
						other = Answer.objects.filter( responses__in = diff_responses, question = ret['question'], artwork = ret['artwork'], hidden = False ).exclude( user = user ).order_by('?')

						if len( other ) > 0:
							ret['challenge'] = challenge
							ret['other_answer'] = other[0]
							ret['responses'] = ret['other_answer'].responses.exclude( pk__in = answer.responses.values_list('pk', flat = True) )
							return ret

					# If it's a image match, pick a specific response
					elif challenge.id == 3:
						responses = list( ret['answer'].responses.all() )
						random.shuffle( responses )

						ret['challenge'] = challenge
						ret['response'] = responses[0]
						return ret

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
		ret['question'] = question
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

		# Show hard question
		if pos == LEVEL_SIZE - 1:
			ret['artwork'] = level.adv_artwork
			ret['answer'] = Answer.objects.get( user = user, artwork = level.adv_artwork, question = question )
			ret['challenge'] = Challenge.objects.get( id = 1 )

		# Pick a filler artwork
		# or a new good artwork
		else:
			# Prune out already-answered artworks
			old_answers = Answer.objects.filter( user = user, question = question, hidden = False )
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
				ret['artwork'] = artworks.order_by( '?' )[0]

			# No artwork found
			except IndexError:
				None

		# Pick this artwork and question
		if ret['artwork'] != None:
			profile.last_seen_artwork = ret['artwork']
			profile.last_seen_question = ret['question']
			profile.save()
			break

	return ret
