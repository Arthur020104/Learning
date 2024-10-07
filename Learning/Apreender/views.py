from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Topic, Subject, User, Problem, TopicHtml, TopicImages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse

cache = {}
WEBSITE_LINK = "http://127.0.0.1:8000"

def getSubjects(user):
    if not user.username:
        return []

    userCache = cache.get(user.username, {'subjects': []})

    if userCache['subjects'] and len(userCache['subjects']) >= Subject.objects.filter(owner=user).count():
        return userCache['subjects']

    subjects = Subject.objects.filter(owner=user)
    userCache['subjects'] = list(subjects.values())
    cache[user.username] = userCache

    return userCache['subjects']

def index(request):
    if request.user.is_anonymous:
        return render(request, 'Apreender/index.html', {'problems': []})

    user = User.objects.get(username=request.user.username)
    subjects = getSubjects(user)
    problemsSuggestedForToday = []

    for subject in subjects:
        topics = Topic.objects.filter(subject=subject['id'])
        for topic in topics:
            askForMoreProblems, problems = topic.suggestNext()

            try:
                problems = list(problems.values())
            except AttributeError as e:
                print(f"Error converting problems to list: {e}")
                problems = None

            if problems:
                topic = topic.__dict__
                subject = Subject.objects.get(id=topic['subject_id']).__dict__
                newProblems = []
                
                for problem in problems:
                    try:
                        if problem['gotIt'] is True:
                            continue
                    except Exception as e:
                        print(f"Error checking if problem {problem['id']} is solved: {e}")
                        continue
                    
                    problem['topic'] = topic
                    problem['subject'] = subject
                    newProblems.append(problem)

                problemsSuggestedForToday.extend(newProblems)

    if not problemsSuggestedForToday:
        print("No problems suggested for today.")

    return render(request, 'Apreender/index.html', {'problems': problemsSuggestedForToday, 'webSiteLink': WEBSITE_LINK})

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

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, "Apreender/login.html", {
                "errorMessage": "Invalid username and/or password."
            })

        login(request, user)
        return redirect('index')

    return render(request, 'Apreender/login.html')


def register(request):
    if request.method == 'POST':
        usernameForm = request.POST['username']
        emailForm = request.POST['email']
        passwordForm = request.POST['password']
        password2Form = request.POST['confirm-password']

        if passwordForm != password2Form:
            return render(request, "Apreender/register.html", {
                "errorMessage": "Passwords do not match."
            })

        if User.objects.filter(username=usernameForm).exists():
            return render(request, "Apreender/register.html", {
                "errorMessage": "Username already exists."
            })

        if User.objects.filter(email=emailForm).exists():
            return render(request, "Apreender/register.html", {
                "errorMessage": "Email is already in use."
            })

        user = User.objects.create_user(username=usernameForm, email=emailForm, password=passwordForm)
        user.is_active = True
        user.save()

        user = authenticate(request, username=usernameForm, password=passwordForm)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, "Apreender/register.html", {
                "errorMessage": "Error authenticating user. Please try again."
            })

    return render(request, 'Apreender/register.html')


@login_required
def topic(request):
    if request.method == 'POST':
        requiredFields = ['name', 'description', 'subject', 'amountSuggest']
        for field in requiredFields:
            if not request.POST.get(field):
                return HttpResponse(f"Error: Field '{field}' is missing.", status=400)

        try:
            name = request.POST['name']
            description = request.POST['description']
            subject = Subject.objects.get(id=request.POST['subject'])
            amountSuggest = int(request.POST['amountSuggest'])

            topic = Topic(name=name, description=description, subject=subject, amountSuggest=amountSuggest)
            topic.save()
            topic.setDefaultSuggestion()

            TopicHtml.objects.filter(topic=topic).delete()
            TopicImages.objects.filter(topic=topic).delete()

            for key, value in request.POST.items():
                if key.startswith('paragraph'):
                    orderKey = f'order-{key}'
                    order = request.POST.get(orderKey)
                    if order is None:
                        return HttpResponse(f"Error: 'order' field is missing for paragraph '{key}'.", status=400)

                    TopicHtml.objects.create(
                        topic=topic,
                        html=value,
                        order=int(order),
                        isImage=False
                    )
                elif key.startswith('order-paragraph'):
                    continue
                elif key.startswith('order-image'):
                    imageKey = f'image-{value}'
                    image = request.FILES.get(imageKey)
                    if image is None:
                        return HttpResponse(f"Error: Image '{imageKey}' is missing.", status=400)
                    order = value
                    if order is None:
                        return HttpResponse("Error: 'order' field is missing for the image.", status=400)

                    imageInstance = TopicImages.objects.create(
                        topic=topic,
                        image=image
                    )

                    TopicHtml.objects.create(
                        topic=topic,
                        html=imageInstance.image.url,
                        order=int(order),
                        isImage=True
                    )

            return redirect(reverse("topicView", args=[topic.id]))

        except Subject.DoesNotExist:
            return HttpResponse("Error: Subject not found.", status=404)

        except ValueError:
            return HttpResponse("Error: 'amountSuggest' field must be an integer.", status=400)

    subjects = Subject.objects.all()
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
        image = request.FILES.get('image')

        problem = Problem(problemStatement=problemStatement, topic=topic, gotIt=gotIt, image=image)
        problem.save()
        return redirect(reverse("problem"))

    subjects = getSubjects(User.objects.get(username=request.user.username))
    topics = Topic.objects.filter(subject__in=[subject['id'] for subject in subjects])
    return render(request, 'Apreender/problem.html', {'topics': topics})


@login_required
def problemView(request, id):
    if request.method == 'POST':
        problem = Problem.objects.get(id=id)
        problem.gotIt = True
        problem.save()
        return redirect(reverse("index"))

    problem = Problem.objects.get(id=id).__dict__
    print(problem)
    problem['topic'] = Topic.objects.get(id=problem['topic_id'])
    problem['subject'] = Subject.objects.get(id=problem['topic'].subject_id)
    return render(request, 'Apreender/showProblem.html', {'problem': problem, 'webSiteLink': WEBSITE_LINK})


@login_required
def topicView(request, id):
    topic = get_object_or_404(Topic, id=id)
    contentItems = TopicHtml.objects.filter(topic=topic).order_by('order')
    
    if not contentItems:
        return redirect(reverse("registerTopicContent", args=[id]))

    fullHtml = ""
    for item in contentItems:
        if item.isImage:
            html = f"""
                    <div class="question-image">
                        <img src="{WEBSITE_LINK}{item.html}" alt="Problem image">
                    </div>
                    """
            fullHtml += html
        else:
            html = f"<p>{item.html}</p>"
            fullHtml += html

    print(f"Complete HTML: {fullHtml}")
    return render(request, 'Apreender/topicView.html', {'topic': topic, 'fullHtml': fullHtml})
