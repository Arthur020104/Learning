from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Topic, Subject, User
from django.contrib.auth import authenticate, login
from django.urls import reverse


def index(request):
    # Verificar se o usuário está logado
    if str(request.user) == 'AnonymousUser':
        return render(request, 'Apreender/index.html', {'problems': None})
    
    # Obter o usuário
    user = User.objects.get(username=request.user.username)
    
    # Obter todos os assuntos do usuário
    subjects = Subject.objects.filter(owner=user)
    
    problemsSuggestForToday = []

    # Iterar sobre todos os assuntos e sugerir problemas
    for subject in subjects:
        topics = Topic.objects.filter(subject=subject)
        for topic in topics:
            askForMoreProblems, problems = topic.suggestNext()
            problemsSuggestForToday.append(problems)

    # Renderizar a página com os problemas sugeridos
    return render(request, 'Apreender/index.html', {'problems': problemsSuggestForToday})

def subject(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        owner = User.objects.get(username=request.user.username)
        
        subject = Subject(name=name, description=description, owner=owner)
        subject.save()
        #when the topic page is ready change the redirect to the topic page
        return redirect(reverse("index"))
    return render(request, 'Apreender/subject.html')

def loginView(request):
    if request.method == 'POST': 
        username = request.POST['name'] 
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "Apreender/login.html", {
                "errorMessage": "Nome de usuário e/ou senha inválidos."
            })
        
        login(request, user)
        return redirect(reverse("index"))
    
    return render(request, 'Apreender/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['confirm-password']

        if password != password2:
            return render(request, "Apreender/register.html", {
                "errorMessage": "As senhas não conferem."
            })

        if User.objects.filter(username=username).exists():
            return render(request, "Apreender/register.html", {
                "errorMessage": "Nome de usuário já existe."
            })

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        
        login(request, user)
        return redirect(reverse("index"))
    
    return render(request, 'Apreender/register.html')
