from django.test import TestCase, Client
from django.urls import reverse
from apps.matches.models import Match, Innings, Venue, PlayerMatchInnings, BowlerMatchInnings
from apps.teams.models import Team
from apps.players.models import Player
from django.utils import timezone
from datetime import timedelta

class CricketMatchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.venue = Venue.objects.create(
            name='Eden Gardens',
            city='Kolkata',
            country='India',
            capacity=66000
        )
        self.team1 = Team.objects.create(name='India', short_name='IND', country='India')
        self.team2 = Team.objects.create(name='Australia', short_name='AUS', country='Australia')
        
        self.match = Match.objects.create(
            title='India vs Australia Final',
            slug='ind-vs-aus-final',
            team1=self.team1,
            team2=self.team2,
            venue=self.venue,
            match_type=Match.MatchType.ODI,
            status=Match.Status.LIVE,
            start_datetime=timezone.now() - timedelta(hours=2)
        )
        self.innings = Innings.objects.create(
            match=self.match,
            innings_number=1,
            batting_team=self.team1,
            bowling_team=self.team2,
            runs=150,
            wickets=2,
            overs=25,
            balls=0
        )
        self.match.current_innings_number = 1
        self.match.save()

    def test_home_page_status(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

    def test_match_list_status(self):
        resp = self.client.get(reverse('matches:match_list'))
        self.assertEqual(resp.status_code, 200)

    def test_match_detail_status(self):
        resp = self.client.get(reverse('matches:match_detail', kwargs={'slug': self.match.slug}))
        self.assertEqual(resp.status_code, 200)

    def test_match_live_json_status(self):
        resp = self.client.get(reverse('matches:match_live_json', kwargs={'slug': self.match.slug}))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['is_live'])
        self.assertEqual(data['current_innings']['team'], 'IND')
        self.assertEqual(data['current_innings']['runs'], 150)

    def test_match_graphs_json_status(self):
        resp = self.client.get(reverse('matches:match_graphs_json', kwargs={'slug': self.match.slug}))
        self.assertEqual(resp.status_code, 200)

    def test_search_view(self):
        resp = self.client.get(reverse('matches:global_search') + '?q=India')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'India')

    def test_search_suggest_view(self):
        resp = self.client.get(reverse('matches:search_suggest') + '?q=Ind')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('suggestions', data)
        self.assertIn('trending', data)

    def test_sitemap_xml(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/xml')

    def test_custom_404_error_page(self):
        resp = self.client.get('/this-path-definitely-does-not-exist-12345/')
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, 'Ball Delivered Outside the Pitch', status_code=404)
