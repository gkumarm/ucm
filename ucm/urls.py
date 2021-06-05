from django.urls import path, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings

from . import constants
from . import views
app_name='ucm'

urlpatterns = [
    path ("",views.home, name="home"),	

	path ('member/profile/',                  views.member_profile,   name=constants.GUID_member_profile),
	path ('member/topic/',                    views.member_topic  ,   name=constants.GUID_member_topic),
	path ('member/dashboard/',                views.member_dashboard, name=constants.GUID_member_dashboard),
	path ('member/network/',                  views.member_network,   name=constants.GUID_member_network),
	path ('member/messaging/',                views.member_messaging, name=constants.GUID_member_messaging),

	path ('compose/topic/<int:pk>/',          views.compose_topic,    name=constants.GUID_compose_topic),
	path ('compose/note/<int:pk>/',           views.compose_note,     name=constants.GUID_compose_note),
	path ('compose/note/<int:pk>/<int:npk>/', views.compose_note,     name=constants.GUID_compose_noted),

	path ('topic/review/<int:pk>/',           views.topic_review,     name=constants.GUID_topic_review),
	path ('topic/review/addnote/',            views.topic_add_note,   name=constants.GUID_topic_add_note),	
	path ('topic/review/addreview/',          views.topic_add_review, name=constants.GUID_topic_add_review),		
	path ('topic/subscribe/<int:pk>/',        views.topic_subscribe,  name=constants.GUID_topic_subscribe),
	path ('topic/share/<int:pk>/',            views.topic_share,      name=constants.GUID_topic_share),

	re_path (r"^more/",            views.more,   name='more'),
	re_path (r'^invite/$',         views.invite,   name='invite'),	
	re_path (r"^rest/",            views.YourView.as_view(),   name='rest'),
    
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
