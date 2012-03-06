from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'a2a.qa.views.index'),

	(r'^question/', 'a2a.qa.views.question'),
	(r'^adv_question/', 'a2a.qa.views.adv_question'),

	(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	(r'^admin/', include(admin.site.urls)),
	(r'^accounts/', include('userena.urls')),

	(r'^tinymce/', include('tinymce.urls')),
	(r'^ajax_filtered_fields/', include('ajax_filtered_fields.urls')),
)
