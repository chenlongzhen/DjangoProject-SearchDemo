"""djangoProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf.urls import url
from django.contrib import admin
from app01 import views

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^list/', views.db_list),
    url(r'^add/', views.db_add),

    # haystack 全文检索
    # url(r'^search/', include('haystack.urls')),
    # autocomplete jquery调用此路由返回complete
    url(r'^search/search/', views.search),

    # cxbc 搜索
    url(r'search_cxbc/', views.search_cxbc),
    #url(r'auto_complete/', views.search),
    url(r'^$', views.search_cxbc),

    #url(r'^index/$', views.index),
    #url(r'index/search/', views.search),
    path(r'upload/<slug:mode>/', views.upload),
]
