from django.urls import path, re_path, include
from uauth.views import usignup, usignin, upassword, usignout, uverify

app_name = 'uauth'

urlpatterns = [
    re_path (r'^signout/$',  usignout,  name='signout'),
	re_path (r'^signup/$',   usignup,   name='signup'),
 	re_path (r'^signin/$',   usignin,   name='signin'),
    re_path (r'^password/$', upassword, name='password'),
	re_path (r'^verify/$',   uverify,   name='verify'),    	
]
