from a2a.qa.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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
		(None, {'fields': ['short_name', 'question', 'tip', 'type']}),
		('Media', {'fields': ['video_url', 'logo', 'badge_small', 'badge_large']}),
		('Advanced Question', {'fields': ['advanced_question', 'advanced_tip']})
	]
	inlines = [ ResponseInline ]

admin.site.register( Question, QuestionAdmin )

admin.site.register( Answer )

class LevelInline( admin.TabularInline ):
	model = Level
	fk_name = 'user'
	max_num = 1

class CustomUserAdmin( UserAdmin ):
	inlines = [ LevelInline ]
	
admin.site.unregister( User )
admin.site.register( User, CustomUserAdmin )
