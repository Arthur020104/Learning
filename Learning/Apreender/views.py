from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Topic, Subject, User, Problem
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import datetime

# Dicionário para armazenar cache por usuário
cache = {}

def getSubjects(user):
    if not user.username:
        return []
    global  cache

    user_cache = cache.get(user.username, {'subjects': []})
    
    if user_cache['subjects'] and len(user_cache['subjects']) >= Subject.objects.filter(owner=user).count():
        return user_cache['subjects']

    subjects = Subject.objects.filter(owner=user)
    user_cache['subjects'] = list(subjects.values())
    

    cache[user.username] = user_cache

    return user_cache['subjects']

#create a getTopics function and cache it



def index(request):
    global cache
    print(cache)
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

            # Sugerir novos problemas
            ask_for_more_problems, problems = topic.suggestNext()
            try:
                problems = list(problems.values())
            except AttributeError as e:
                print(f"Erro ao converter problemas para lista: {e}")
                problems = None    
            
            #print(f"Problemas sugeridos para o tópico {topic.name}: {problems}")
            if problems:
                # Verificação de dados de cada problema antes de adicionar à lista
                topic =  topic.__dict__
                subject = Subject.objects.get(id=topic['subject_id']).__dict__
                newProblems = []
                for problem in problems:
                    try:
                        if problem['gotIt'] == True:
                            print(f"Problema {problem['id']} já foi resolvido. Removendo da lista de sugestões.")
                            continue
                    except Exception as e:
                        print(f"Erro ao verificar se o problema {problem['id']} foi resolvido: {e}")
                    except TypeError as e:
                        print(f"Erro ao verificar se o problema {problem['id']} foi resolvido: {e}")
                    try:
                        problems.remove(problem)
                    except:
                        pass
                    problem['topic'] = topic
                    problem['subject'] = subject
                    newProblems.append(problem)
                    ##print(f"Problema: {problem.name}, ID: {problem.id}, Tópico: {problem.topic}, Subject: {problem.subject.name}, Owner: {problem.owner.username}")
                problems_suggested_for_today.extend(newProblems) 
    # Verificar o conteúdo da lista de problemas sugeridos antes de renderizar
    if not problems_suggested_for_today:
        print("Nenhum problema sugerido para hoje.")
    print(len(problems_suggested_for_today))
    # Renderizar a página com os problemas sugeridos
    return render(request, 'Apreender/index.html', {'problems': problems_suggested_for_today})


@login_required
def subject(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        owner = User.objects.get(username=request.user.username)
        
        subject = Subject(name=name, description=description, owner=owner)
        subject.save()


        return redirect(reverse("topic"))
    
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


@login_required
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
        return redirect(reverse("problem"))

    subjects = getSubjects(User.objects.get(username=request.user.username))
    
    return render(request, 'Apreender/topic.html', {'subjects': subjects})
@login_required
def logoutView(request):
    logout(request)
    return redirect(reverse("login"))
@login_required
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
    
    subjects = getSubjects(User.objects.get(username=request.user.username))
    topics = Topic.objects.filter(subject__in=[subject['id'] for subject in subjects])
    return render(request, 'Apreender/problem.html', {'topics': topics})

@login_required
def problemView(request, id):
    if request.method == 'POST':
        gotIt = True
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