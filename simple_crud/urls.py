# -*- coding: utf-8 -*- 

from django.conf.urls import url

from .views import SimpleCRUD


urlpatterns = [
    url(r'^(.*)', SimpleCRUD.as_view(), name='SimpleCRUD'),         
]
