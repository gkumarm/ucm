from django.urls import path, re_path
from . import views

app_name='ucm'

urlpatterns = [
    re_path (r"^$",     views.home, name="home"),
    re_path (r"^home/", views.home, name="home"),

	re_path (r'^review/$',         views.review, name='review'),
	path ('review/<int:pk>/', views.review, name='review'),
	re_path (r"^more/",            views.more,   name='more'),
	path ('subscribe/<int:pk>/', views.subscribe, name='subscribe'),

	re_path (r"^rest/",            views.YourView.as_view(),   name='rest'),	
]
