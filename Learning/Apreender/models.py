from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime
from django.utils import timezone  # Melhor utilizar timezone se estiver usando USE_TZ

class User(AbstractUser):
    # Customizando os relacionamentos ManyToMany para evitar conflitos
    class Meta:
        app_label = 'Apreender'
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
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
    lastSuggestion = models.DateField(null=True)  # Está correto usar DateField se apenas datas forem necessárias
    nextSuggestion = models.DateField(null=True)  # Certifique-se de que não precisa de DateTimeField
    learningLevel = models.IntegerField(default=0)
    amountSuggest = models.IntegerField(default=3)
    lastSuggestedProblems = models.TextField(max_length=200, default="")

    def setDefaultSuggestion(self):
        # Atualiza a próxima sugestão com base no nível de aprendizado
        self.lastSuggestion = datetime.date.today() - datetime.timedelta(days=1)
        #o +1 em (days=self.getLearningLevelInDays()+1) é para compensar o -1 que é o default para o lastSuggestion entao se criamos problema no dia
        #2 ele vai sugerir no dia 3 e inicialmente o lastSuggestion é dia 1 e o nextSuggestion é dia 3
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays()+1)
        self.learningLevel += 1
        self.save()

    def suggestNext(self):
        problems_ids = self.lastSuggestedProblems.split(",")
        if len(problems_ids) > 0 and problems_ids[0] != "":
            problems_ids = [id.strip() for id in problems_ids if id]  # Limpa espaços indesejados
        else:
            problems_ids = None
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
        problems = list(Problem.objects.filter(topic=self, gotIt=False).order_by('?'))
        if len(problems) <= self.amountSuggest:
            self.storeLastSuggestedProblems(problems)
            return True, problems
        else:
            self.storeLastSuggestedProblems(problems[:self.amountSuggest])
            return True, problems[:self.amountSuggest]
    
    def storeLastSuggestedProblems(self, problems):
        # Armazena os IDs dos problemas sugeridos
        self.lastSuggestedProblems = ",".join(str(problem.id) for problem in problems)
        self.lastSuggestion = datetime.date.today()
        self.nextSuggestion = self.lastSuggestion + datetime.timedelta(days=self.getLearningLevelInDays())
        self.learningLevel += 1
        self.save()

    def getLearningLevelInDays(self):
        # Define os intervalos de aprendizado
        learning_days = [1, 1, 2, 30, 60]# fast learning will be back to [1, 3, 7, 14, 30]
        if self.learningLevel < len(learning_days):
            return learning_days[self.learningLevel]
        return 120 * (self.learningLevel - 4)

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
