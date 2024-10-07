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
    path('logout/', views.logoutView, name='logout'),
    path('problem/', views.problem, name='problem'),
    path('problem/<int:id>/', views.problemView, name='problemId'),
    path('topic/<int:id>/', views.topicView, name='topicView'), 
    path('sujectsList/', views.subjectsView, name='subjectsList'),
               ]