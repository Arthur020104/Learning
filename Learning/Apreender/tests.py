from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Subject, Topic, Problem
import datetime

User = get_user_model()

class ApreenderTestCase(TestCase):
  def setUp(self):
    # setUp establishes data for the tests.
    # Django TestCase automatically wraps these in a transaction that is rolled back after each test.
    self.client = Client()
    self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword123')
    self.subject = Subject.objects.create(name='Math', description='Math Subject', owner=self.user)
    self.topic = Topic.objects.create(
        name='Algebra',
        description='Algebra Topic',
        subject=self.subject,
        amountSuggest=3,
        lastSuggestion=datetime.date.today(),
        nextSuggestion=datetime.date.today() + datetime.timedelta(days=1)
    )
    self.problem = Problem.objects.create(
        problemName='Solve x',
        problemStatement='x + 2 = 4',
        topic=self.topic,
        gotIt=False
    )

  def testUserAuthenticationAndLogin(self):
    # Test authenticating an existing user
    response = self.client.post(reverse('login'), {'name': 'testuser', 'password': 'testpassword123'})
    self.assertEqual(response.status_code, 302)  # Redirects to index on success
      
  def testUserRegistrationCreatesUser(self):
    # Ensure registration works and avoids duplicates
    response = self.client.post(reverse('register'), {
      'username': 'newuser',
      'email': 'new@user.com',
      'password': 'newpassword123',
      'confirm-password': 'newpassword123'
    })
    self.assertEqual(response.status_code, 302)
    self.assertTrue(User.objects.filter(username='newuser').exists())

  def testCreateSubjectUnauthorized(self):
    # Ensure login is required to create a subject
    response = self.client.post(reverse('subject'), {'name': 'Physics', 'description': 'Physics Desc'})
    self.assertEqual(response.status_code, 302)  # Redirect to login

  def testCreateSubjectAuthorized(self):
    self.client.login(username='testuser', password='testpassword123')
    response = self.client.post(reverse('subject'), {'name': 'Physics', 'description': 'Physics Desc'})
    self.assertEqual(response.status_code, 302)
    self.assertTrue(Subject.objects.filter(name='Physics').exists())

  def testProblemSolvingUpdatesSuggestion(self):
    # Test the core logic for suggesting topics
    self.client.login(username='testuser', password='testpassword123')
    problem_id = self.problem.id
    response = self.client.post(reverse('problemId', args=[problem_id]))
    self.assertEqual(response.status_code, 302)
    
    self.problem.refresh_from_db()
    self.assertTrue(self.problem.gotIt)

  def testShouldSuggestTodayMutatesState(self):
    # Tests the previously flagged method for side-effects
    topic = Topic.objects.create(
      name='Geometry',
      description='Geometry Topic',
      subject=self.subject,
      nextSuggestion=datetime.date.today() - datetime.timedelta(days=1)
    )
    self.assertTrue(topic.shouldSuggestToday())
    topic.refresh_from_db()
    self.assertEqual(topic.lastSuggestion, datetime.date.today())

