from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime
from django.utils import timezone  # Better to use timezone if USE_TZ is enabled

class User(AbstractUser):
    class Meta:
        app_label = 'Apreender'
    
    # Customizing ManyToMany relationships to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customUserSet',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    userPermissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customUserPermissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.username} - ID: {self.id}"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - Description: {self.description} - Owner: {self.owner}"

class Topic(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    lastSuggestion = models.DateField(null=True)  # Correct to use DateField if only dates are needed
    nextSuggestion = models.DateField(null=True)  # Ensure you don't need DateTimeField
    learningLevel = models.IntegerField(default=0)
    amountSuggest = models.IntegerField(default=3)
    lastSuggestedProblems = models.TextField(max_length=200, default="")

    def setDefaultSuggestion(self):
        # Update the next suggestion based on the learning level
        self.lastSuggestion = datetime.date.today() - datetime.timedelta(days=1)
        # The +1 in (days=self.getLearningLevelInDays()+1) compensates for the -1 default in lastSuggestion.
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays() + 1)
        self.learningLevel += 1
        self.save()

    def suggestNext(self):
        problemIds = self.lastSuggestedProblems.split(",")
        if len(problemIds) > 0 and problemIds[0] != "":
            problemIds = [id.strip() for id in problemIds if id]  # Clean unwanted spaces
        else:
            problemIds = None

        # Check if the last suggestion was made today
        if self.lastSuggestion == datetime.date.today() and problemIds:
            problems = Problem.objects.filter(id__in=problemIds).values()
            if problems.exists():
                return False, problems
            return False, []

        # Check if it's too early to suggest new problems
        if self.getDaysLeftToSuggest() > 0:
            return False, []

        # Fetch new problems and suggest
        problems = list(Problem.objects.filter(topic=self, gotIt=False).order_by('?'))
        if len(problems) <= self.amountSuggest:
            self.storeLastSuggestedProblems(problems)
            return True, problems
        else:
            self.storeLastSuggestedProblems(problems[:self.amountSuggest])
            return True, problems[:self.amountSuggest]

    def storeLastSuggestedProblems(self, problems):
        # Store the IDs of the suggested problems
        self.lastSuggestedProblems = ",".join(str(problem.id) for problem in problems)
        self.lastSuggestion = datetime.date.today()
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays())
        self.learningLevel += 1
        self.save()

    def getLearningLevelInDays(self):
        # Define learning intervals
        learningDays = [1, 3, 7, 14, 30] 
        if self.learningLevel < len(learningDays):
            return learningDays[self.learningLevel]
        return int(60 ** (self.learningLevel/5) - (( (self.learningLevel - 5)/5)**2))

    def getDaysLeftToSuggest(self):
        if self.nextSuggestion:
            return (self.nextSuggestion - datetime.date.today()).days
        return 0
    
    def __str__(self):
        return f"{self.name} - Description: {self.description} - Subject: {self.subject}"

class TopicImages(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    
    def __str__(self):
        return f"Image URL: {self.image.url} - Topic: {self.topic}"

class TopicHtml(models.Model):
    # This is for each piece of HTML in the topic, can have many HTML entries
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    html = models.TextField(max_length=15000)
    order = models.IntegerField(null=False)
    isImage = models.BooleanField()
    
    def __str__(self):
        return f"HTML: {self.html} - Topic: {self.topic}"

class Problem(models.Model):
    problemStatement = models.TextField(max_length=1000)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    gotIt = models.BooleanField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    
    def __str__(self):
        return f"Problem: {self.problemStatement} - Topic: {self.topic}"
