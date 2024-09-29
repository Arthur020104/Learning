from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime

class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Custom related_name to avoid conflict
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Custom related_name to avoid conflict
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
    lastSuggestion = models.DateField()  # Alterado para DateField
    nextSuggestion = models.DateField(null=True)  # Alterado para DateField
    learningLevel = models.IntegerField(default=0)
    amountSuggest = models.IntegerField(default=3)
    lastSuggestedProblems = models.TextField(max_length=200, default="")
    def load(self):
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays())
        self.save()
    def suggestNext(self):  # Return a boolean and a list of problems
        if self.lastSuggestion == datetime.date.today():
            problemsIds = self.lastSuggestedProblems.split(",")
            if problemsIds == ['']:
                problemsIds = []
            problems = Problem.objects.filter(id__in=problemsIds)
            problems = list(problems)
            if len(problems) == 0:
                return False, []
            return False, problems
            # Agora comparando apenas a data
        elif  self.getDaysLeftToSuggest() > 0:
            return False, []
        # Get all problems for this topic and suggest random amountSuggest problems
        problems = Problem.objects.filter(topic=self).order_by('?')
        if problems.count() < self.amountSuggest:
            self.storeLastSuggestedProblems(problems)
            return True, problems
        self.storeLastSuggestedProblems(problems[:self.amountSuggest])
        return False, problems[:self.amountSuggest]
    
    def storeLastSuggestedProblems(self, problems):
        self.lastSuggestedProblems = ",".join(str(problem.id) for problem in problems)
        self.lastSuggestion = datetime.date.today()  # Utiliza apenas a data
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays())
        self.learningLevel += 1
        self.save()

    def getLearningLevelInDays(self):
        if self.learningLevel == 0:
            return 1
        elif self.learningLevel == 1:
            return 7
        elif self.learningLevel == 2:
            return 14
        elif self.learningLevel == 3:
            return 30
        elif self.learningLevel == 4:
            return 60
        else:
            return 365 * (5 ** (self.learningLevel / 5))

    def getDaysLeftToSuggest(self):
        diferenca = self.nextSuggestion - datetime.date.today()
        dias = diferenca.days
        return dias
    
    def __str__(self):
        return f"{self.name} - Description: {self.description} - Subject: {self.subject}"

class Problem(models.Model):
    problemStatement = models.TextField(max_length=1000)  # Can be HTML code
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    gotIt = models.BooleanField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    
    def __str__(self):
        return f"Problem: {self.problemStatement} - Topic: {self.topic}"
