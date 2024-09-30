from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Topic, Subject, User, Problem
from django.contrib.auth import authenticate, login, logout
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
    if request.user.is_anonymous:
        return render(request, 'Apreender/index.html', {'problems': []})
    user = User.objects.get(username=request.user.username)
    
    # Obter os assuntos do cache ou carregar
    subjects = getSubjects(user)
    
    problems_suggested_for_today = []

    # Iterar sobre todos os assuntos e sugerir problemas
    for subject in subjects:
        topics = Topic.objects.filter(subject=subject['id'])
        for topic in topics:
            # Ajustando a próxima sugestão caso necessário
            if topic.nextSuggestion is None or topic.id == 1:
                topic.nextSuggestion = datetime.date.today()
                topic.save()

            # Sugerir novos problemas
            ask_for_more_problems, problems = topic.suggestNext()
            #print(f"Problemas sugeridos para o tópico {topic.name}: {problems}")
            problems = problems
            #print(problems)
            if problems:
                # Verificação de dados de cada problema antes de adicionar à lista
                for problem in problems:
                    try:
                        if problem['gotIt']:
                            continue
                    except Exception as e:
                        print(f"Erro ao verificar se o problema {problem['id']} foi resolvido: {e}")
                        continue
                    #print("here")
                    #print(problem)
                    problem['topic'] = Topic.objects.get(id=problem['topic_id'])
                    problem['subject'] = Subject.objects.get(id=problem['topic'].subject_id)
                    ##print(f"Problema: {problem.name}, ID: {problem.id}, Tópico: {problem.topic}, Subject: {problem.subject.name}, Owner: {problem.owner.username}")
                
                problems_suggested_for_today.extend(problems)  # Usando extend para evitar listas aninhadas

    # Verificar o conteúdo da lista de problemas sugeridos antes de renderizar
    if not problems_suggested_for_today:
        print("Nenhum problema sugerido para hoje.")

    # Renderizar a página com os problemas sugeridos
    return render(request, 'Apreender/index.html', {'problems': problems_suggested_for_today})



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
        #print(f"Usuário: {username}, Senha: {password}")
        user = authenticate(request, username=username, password=password)
        #print(f"Usuário autenticado: {user}")
        if user is None:
            return render(request, "Apreender/login.html", {
                "errorMessage": "Nome de usuário e/ou senha inválidos."
            })
        
        login(request, user)
        return redirect('index')  # Redireciona para o índice após login bem-sucedido
    
    return render(request, 'Apreender/login.html')



def register(request):
    if request.method == 'POST':
        usernameForm = request.POST['username']
        emailForm = request.POST['email']
        passwordForm = request.POST['password']
        password2Form = request.POST['confirm-password']

        # Verificar se as senhas coincidem
        if passwordForm != password2Form:
            return render(request, "Apreender/register.html", {
                "errorMessage": "As senhas não conferem."
            })

        # Verificar se o nome de usuário já existe
        if User.objects.filter(username=usernameForm).exists():
            return render(request, "Apreender/register.html", {
                "errorMessage": "Nome de usuário já existe."
            })

        # Verificar se o email já existe
        if User.objects.filter(email=emailForm).exists():
            return render(request, "Apreender/register.html", {
                "errorMessage": "Já existe um usuário com este email."
            })

        # Criar o novo usuário
        #print(f"Dados do novo usuário: {usernameForm}, {emailForm}, {passwordForm}")
        user = User.objects.create_user(username=usernameForm, email=emailForm, password=passwordForm)
        user.is_active = True  # Certificar que o usuário é ativo
        user.save()

        # Autenticar o usuário criado
        user = authenticate(request, username=usernameForm, password=passwordForm)

        if user is not None:
            #print(f"Usuário autenticado: {user}")
            login(request, user)  # Fazer login automático após registro bem-sucedido
            #print(f"Usuário {usernameForm} criado com sucesso.")
            return redirect('index')  # Redireciona para a página principal após o registro bem-sucedido
        else:
            return render(request, "Apreender/register.html", {
                "errorMessage": "Erro ao autenticar o usuário. Tente novamente."
            })

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

def logoutView(request):
    logout(request)
    return redirect(reverse("login"))

def problem(request):
    if request.method == 'POST':
        problemStatement = request.POST['problemStatement']
        topic = Topic.objects.get(id=request.POST['topic'])
        gotIt = False  
        image = None
        if request.FILES.get('image'):
            image = request.FILES['image']
        
        problem = Problem(problemStatement=problemStatement, topic=topic, gotIt=gotIt, image=image)
        problem.save()
        return redirect(reverse("index"))
    global subjectsCache
    if not request.user.username in subjectsCache.keys():
        getSubjects(User.objects.get(username=request.user.username))
    #get topics that are in the cached user subjects
    topics = Topic.objects.filter(subject__in=[subject['id'] for subject in subjectsCache[request.user.username]])
    return render(request, 'Apreender/problem.html', {'topics': topics})


def problemView(request, id):
    if request.method == 'POST':
        gotIt = request.POST['gotIt']
        problem = Problem.objects.get(id=id)
        problem.gotIt = gotIt
        problem.save()
        return redirect(reverse("index"))
    problem = Problem.objects.get(id=id)
    problem = problem.__dict__
    print(problem)
    problem['topic'] = Topic.objects.get(id=problem['topic_id'])
    problem['subject'] = Subject.objects.get(id=problem['topic'].subject_id)
    return render(request, 'Apreender/showProblem.html', {'problem': problem})