from django.shortcuts import render
from django.http import HttpResponse
from .models import Topic


def index(request):
    #return index page
    request.session['user'] = 'user'
    problemsSuggestForToday = []
    # Get all topics for this user
    print(request.user)
    if str(request.user) == 'AnonymousUser':
        return render(request, 'Apreender/index.html', {'problems': None})
    topics = Topic.objects.filter(subject__owner=request.user)
    for topic in topics:
        askForMoreProblems, problems = topic.suggestNext()
        problemsSuggestForToday.append(problems)
    return render(request, 'Apreender/index.html', {'problems': problemsSuggestForToday})
    #return render(request, 'Apreender/index.html')
