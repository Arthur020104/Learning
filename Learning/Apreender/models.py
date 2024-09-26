from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime

class User(AbstractUser):
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
    lastSuggestion = models.DateTimeField()
    nextSuggestion = models.DateTimeField()
    learningLevel = models.IntegerField()
    amountSuggest = models.IntegerField()
    lastSuggestedProblems = models.TextField(max_length=200)

    def suggestNext(self):  # Return a boolean and a list of problems
        # Check if it is between the last and next suggestion
        if self.getHoursLeftToSuggest() > 0:
            if (datetime.datetime.now() - self.lastSuggestion).total_seconds() / 3600 < 12:
                problemsIds = self.lastSuggestedProblems.split(",")
                problems = Problem.objects.filter(id__in=problemsIds)
                return False, problems
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
        self.lastSuggestion = datetime.datetime.now()
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(hours=self.getLearningLevelInHours())
        self.save()

    def getLearningLevelInHours(self):
        if self.learningLevel == 0:
            return 24
        elif self.learningLevel == 1:
            return 24 * 7
        elif self.learningLevel == 2:
            return 24 * 30
        elif self.learningLevel == 3:
            return 24 * 60
        elif self.learningLevel == 4:
            return 24 * 120
        else:
            return 24 * 70 * (5 ** (self.learningLevel / 5))

    def getHoursLeftToSuggest(self):
        diferenca = self.nextSuggestion - datetime.datetime.now()
        horas = diferenca.total_seconds() / 3600
        return horas
    
    def __str__(self):
        return f"{self.name} - Description: {self.description} - Subject: {self.subject}"

class Problem(models.Model):
    problemStatement = models.TextField(max_length=1000)  # Can be HTML code
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    gotIt = models.BooleanField()
    
    def __str__(self):
        return f"Problem: {self.problemStatement} - Topic: {self.topic}"
