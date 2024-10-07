from django.contrib import admin
from .models import User, Subject, Topic, Problem, TopicHtml, TopicImages

# Register your models here
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'owner')
    search_fields = ('name', 'owner__username')
    list_filter = ('owner',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'lastSuggestion', 'nextSuggestion', 'learningLevel', 'id')
    search_fields = ('name', 'subject__name')
    list_filter = ('subject',)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('problemStatement', 'topic', 'gotIt')
    search_fields = ('problemStatement', 'topic__name')
    list_filter = ('topic', 'gotIt')
@admin.register(TopicHtml)
class TopicHtmlAdmin(admin.ModelAdmin):
    list_display = ('topic', 'order', 'isImage')
    search_fields = ('topic__name', 'order')
    list_filter = ('topic', 'isImage')
@admin.register(TopicImages)
class TopicImagesAdmin(admin.ModelAdmin):
    list_display = ('topic', 'image')
    search_fields = ('topic__name', 'image')
    list_filter = ('topic',)