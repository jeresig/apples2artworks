from a2a.qa.models import *
from django.contrib import admin

class ArtworkLinkInline( admin.StackedInline ):
	model = ArtworkLink
	extra = 1

class ArtworkAdmin( admin.ModelAdmin ):
	inlines = [ ArtworkLinkInline ]

admin.site.register( Artwork, ArtworkAdmin )

class ResponseInline( admin.StackedInline ):
	model = Response
	extra = 4

class QuestionAdmin( admin.ModelAdmin ):
	fieldsets = [
		(None, {'fields': ['question', 'tip', 'type', 'video_url']}),
		('Advanced Question', {'fields': ['advanced_question', 'advanced_tip']})
	]
	inlines = [ ResponseInline ]

admin.site.register( Question, QuestionAdmin )

admin.site.register( Answer )
