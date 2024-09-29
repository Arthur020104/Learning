#Urls for aprendeer app
from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.loginView, name='login'),
    path('register/', views.register, name='register'),
    path('subject/', views.subject, name='subject'),
    path('topic/', views.topic, name='topic'),
    path('logout/', views.logout, name='logout'),
               ]