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

    def suggestNext(self):
        problems_ids = self.lastSuggestedProblems.split(",")
        if problems_ids == ['']:
            problems_ids = []
        
        # Verificar se a última sugestão foi feita hoje
        if self.lastSuggestion == datetime.date.today() and problems_ids:
            problems = Problem.objects.filter(id__in=problems_ids).values()
            if problems.exists():
                return False, problems
            return False, []
        
        # Verificar se é cedo para sugerir novos problemas
        if self.getDaysLeftToSuggest() > 0:
            return False, []
        
        # Buscar novos problemas e sugerir
        problems = list(Problem.objects.filter(topic=self).order_by('?'))
        if len(problems) <= self.amountSuggest:
            self.storeLastSuggestedProblems(problems)
            return True, problems
        else:
            self.storeLastSuggestedProblems(problems[:self.amountSuggest])
            return True, problems[:self.amountSuggest]
    
    def storeLastSuggestedProblems(self, problems):
        self.lastSuggestedProblems = ",".join(str(problem.id) for problem in problems)
        self.lastSuggestion = datetime.date.today()
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays())
        self.learningLevel += 1
        self.save()

    def getLearningLevelInDays(self):
        learning_days = [1, 7, 14, 30, 60]
        if self.learningLevel < len(learning_days):
            return learning_days[self.learningLevel]
        return 365 * (5 ** (self.learningLevel // 5))

    def getDaysLeftToSuggest(self):
        if self.nextSuggestion:
            return (self.nextSuggestion - datetime.date.today()).days
        return 0
    
    def __str__(self):
        return f"{self.name} - Description: {self.description} - Subject: {self.subject}"

class Problem(models.Model):
    problemStatement = models.TextField(max_length=1000)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    gotIt = models.BooleanField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    
    def __str__(self):
        return f"Problem: {self.problemStatement} - Topic: {self.topic}"
