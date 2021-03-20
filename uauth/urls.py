from django.urls import path, re_path, include
from uauth.views import uregister, ulogin, upassword, ulogout, uverify

app_name = 'uauth'

urlpatterns = [
    re_path (r'^logout/$'  , ulogout,   name='logout'),
	re_path (r'^register/$', uregister, name='register'),
 	re_path (r'^login/$'   , ulogin,    name='login'),
    re_path (r'^password/$', upassword, name='password'),
	re_path (r'^verify/$',   uverify,    name='verify'),    
]
