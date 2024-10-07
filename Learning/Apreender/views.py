from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Topic, Subject, User, Problem, TopicHtml, TopicImages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import datetime
import json


# Dicionário para armazenar cache por usuário
cache = {}
WEBSITELINK = "http://127.0.0.1:8000"
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
                        continue
                    except TypeError as e:
                        print(f"Erro ao verificar se o problema {problem['id']} foi resolvido: {e}")
                        continue
                    
                    problem['topic'] = topic
                    problem['subject'] = subject
                    newProblems.append(problem)
                    ##print(f"Problema: {problem.name}, ID: {problem.id}, Tópico: {problem.topic}, Subject: {problem.subject.name}, Owner: {problem.owner.username}")
                problems_suggested_for_today.extend(newProblems) 
    # Verificar o conteúdo da lista de problemas sugeridos antes de renderizar
    if not problems_suggested_for_today:
        print("Nenhum problema sugerido para hoje.")
    # Renderizar a página com os problemas sugeridos
    return render(request, 'Apreender/index.html', {'problems': problems_suggested_for_today, 'webSiteLink': WEBSITELINK})


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
        # Verificação dos campos obrigatórios
        required_fields = ['name', 'description', 'subject', 'amountSuggest']
        for field in required_fields:
            if not request.POST.get(field):
                return HttpResponse(f"Erro: Campo '{field}' está faltando.", status=400)

        try:
            # Primeiro, registrar o tópico
            name = request.POST['name']
            description = request.POST['description']
            subject = Subject.objects.get(id=request.POST['subject'])
            amountSuggest = int(request.POST['amountSuggest'])  # Validação de tipo inteiro

            topic = Topic(name=name, description=description, subject=subject, amountSuggest=amountSuggest)
            topic.save()
            topic.setDefaultSuggestion()

            # Agora, registrar o conteúdo do tópico
            # Remover conteúdo anterior, se já existir
            TopicHtml.objects.filter(topic=topic).delete()
            TopicImages.objects.filter(topic=topic).delete()

            for key, value in request.POST.items():
                if key.startswith('paragraph'):
                    orderKey = f'order-{key}'
                    order = request.POST.get(orderKey)
                    if order is None:
                        return HttpResponse(f"Erro: Campo 'order' está faltando para o parágrafo '{key}'.", status=400)

                    # Cadastrar o parágrafo no modelo TopicHtml
                    TopicHtml.objects.create(
                        topic=topic,
                        html=value,
                        order=int(order),
                        isImage=False
                    )
                elif key.startswith('order-paragraph'):
                    continue
                elif key.startswith('order-image'):
                    orderKey = key
                    imageKey = f'image-{value}'
                    image = request.FILES.get(imageKey)
                    if image is None:
                        return HttpResponse(f"Erro: Imagem '{imageKey}' está faltando.", status=400)
                    order = value
                    if order is None:
                        return HttpResponse("Erro: Campo 'order' está faltando para a imagem.", status=400)

                    # Cadastrar a imagem no modelo TopicImages
                    imageInstance = TopicImages.objects.create(
                        topic=topic,
                        image=image
                    )
                    # Cadastrar a referência à imagem no modelo TopicHtml para preservar a ordem
                    TopicHtml.objects.create(
                        topic=topic,
                        html=imageInstance.image.url,
                        order=int(order),
                        isImage=True
                    )

            # Redirecionando para a página do tópico
            return redirect(reverse("topicView", args=[topic.id]))

        except Subject.DoesNotExist:
            return HttpResponse("Erro: Assunto não encontrado.", status=404)

        except ValueError:
            return HttpResponse("Erro: O campo 'amountSuggest' deve ser um número inteiro.", status=400)

    # Caso seja um GET, carrega o formulário
    subjects = Subject.objects.all()  # Supondo que há um modelo de Assunto
    return render(request, 'Apreender/topic.html', {
        'subjects': subjects,
    })

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
        return redirect(reverse("problem"))
    
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
    return render(request, 'Apreender/showProblem.html', {'problem': problem, 'webSiteLink': WEBSITELINK})

@login_required
def topicView(request, id):
    topic = get_object_or_404(Topic, id=id)
    
    # Buscar todos os conteúdos HTML (parágrafos e imagens) relacionados ao tópico, ordenados
    contentItems = TopicHtml.objects.filter(topic=topic).order_by('order')
    if contentItems is None:
        return redirect(reverse("registerTopicContent", args=[id]))
    
    fullHtml = ""
    for item in contentItems:
        if item.isImage:
            html = f"""
                    <div class="question-image">
                        <img src="{WEBSITELINK}{item.html}" alt="Imagem do problema">
                    </div>
                    """
            fullHtml += html
        else:
            html = f"""
                    <p>{item.html}</p>
                    """    
            fullHtml += html 
    print(f"HTML completo: {fullHtml}")
    return render(request, 'Apreender/topicView.html', {'topic': topic, 'fullHtml': fullHtml})
            