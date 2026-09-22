from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.teams.models import Team
from apps.matches.models import Match, Venue
from django.utils import timezone

User = get_user_model()

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        self.team1 = Team.objects.create(name='India', short_name='IND', country='India')
        self.team2 = Team.objects.create(name='England', short_name='ENG', country='England')
        self.venue = Venue.objects.create(name='Lord\'s', city='London', country='England')
        self.match = Match.objects.create(
            title='England vs India Test',
            slug='eng-vs-ind-test',
            team1=self.team2,
            team2=self.team1,
            venue=self.venue,
            match_type=Match.MatchType.TEST,
            status=Match.Status.LIVE,
            start_datetime=timezone.now()
        )

    def test_api_jwt_login(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'Password123!'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_api_live_matches(self):
        resp = self.client.get('/api/v1/matches/live/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_api_match_list(self):
        resp = self.client.get('/api/v1/matches/')
        self.assertEqual(resp.status_code, 200)

    def test_api_team_list(self):
        resp = self.client.get('/api/v1/teams/')
        self.assertEqual(resp.status_code, 200)
