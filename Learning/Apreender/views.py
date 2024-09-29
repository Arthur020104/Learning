from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Topic, Subject, User
from django.contrib.auth import authenticate, login
from django.urls import reverse
import datetime

# Dicionário para armazenar cache por usuário
subjectsCache = {}

def getSubjects(user):
    global subjectsCache
    # Verificar se já existe cache para o usuário atual
    if user.username not in subjectsCache:
        subjects = Subject.objects.filter(owner=user)
        # Armazenar os dados dos assuntos em formato de lista
        subjectsCache[user.username] = list(subjects.values())
    return subjectsCache[user.username]

def index(request):
    # Verificar se o usuário está logado
    if str(request.user) == 'AnonymousUser':
        return render(request, 'Apreender/index.html', {'problems': None})
    
    # Obter o usuário
    user = User.objects.get(username=request.user.username)
    
    # Obter os assuntos do cache ou carregar
    subjects = getSubjects(user)
    
    problemsSuggestForToday = []

    # Iterar sobre todos os assuntos e sugerir problemas
    for subject in subjects:
        print(subject)
        topics = Topic.objects.filter(subject=subject['id'])
        for topic in topics:
            askForMoreProblems, problems = topic.suggestNext()
            if len(problems) > 0:
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

        # Atualizar o cache do usuário
        global subjectsCache
        if owner.username in subjectsCache:
            subjectsCache[owner.username].append({
                'id': subject.id,
                'name': subject.name,
                'description': subject.description,
                'owner_id': subject.owner_id
            })

        # Quando a página de tópico estiver pronta, mude o redirecionamento para lá
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

def topic(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        subject = Subject.objects.get(id=request.POST['subject'])
        lastSuggestion = datetime.date.today()
        amountSuggest = request.POST['amountSuggest']
        
        topic = Topic(name=name, description=description, subject=subject, lastSuggestion=lastSuggestion, amountSuggest=amountSuggest)
        topic.save()
        topic.load()
        return redirect(reverse("index"))

    # Carregar assuntos do usuário
    global subjectsCache
    subjects = getSubjects(User.objects.get(username=request.user.username))
    
    return render(request, 'Apreender/topic.html', {'subjects': subjects})

def logout(request):
    logout(request)
    return redirect(reverse("index"))