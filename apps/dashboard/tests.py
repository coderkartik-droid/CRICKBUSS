from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class DashboardTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regularfan',
            email='fan@example.com',
            password='Password123!',
            role='registered_user'
        )
        self.admin_user = User.objects.create_superuser(
            username='superadmin',
            email='admin@example.com',
            password='Password123!'
        )

    def test_user_dashboard_requires_login(self):
        resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp.status_code, 302)

    def test_user_dashboard_authenticated(self):
        self.client.force_login(self.regular_user)
        resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_dashboard_denied_for_regular_user(self):
        self.client.force_login(self.regular_user)
        resp = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_admin_dashboard_allowed_for_staff(self):
        self.client.force_login(self.admin_user)
        resp = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Platform Administration')
        self.assertContains(resp, 'Total Users')

    def _managed_user(self, email, role):
        user = User(
            username=email.split('@')[0],
            email=email,
            role=role,
            is_active=True,
        )
        user.set_password('Password123!')
        user.save()
        return user

    def test_public_signup_cannot_select_privileged_role(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Public',
            'last_name': 'Attempt',
            'username': 'publicattempt',
            'email': 'publicattempt@example.com',
            'role': 'admin',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='publicattempt@example.com')
        self.assertEqual(user.role, User.Role.USER)

    def test_admin_can_manage_scorers_but_not_admins(self):
        admin = self._managed_user('operator@example.com', User.Role.ADMIN)
        self.client.force_login(admin)
        response = self.client.get(reverse('dashboard:managed_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Scorer')

        response = self.client.post(reverse('dashboard:managed_users'), {
            'role': User.Role.SCORER,
            'first_name': 'Live',
            'last_name': 'Operator',
            'username': 'liveoperator',
            'email': 'liveoperator@example.com',
            'password': 'StrongPassword123!',
            'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        scorer = User.objects.get(email='liveoperator@example.com')
        self.assertEqual(scorer.role, User.Role.SCORER)
        self.assertEqual(
            self.client.post(reverse('dashboard:managed_users'), {
                'role': User.Role.ADMIN,
                'email': 'blocked@example.com',
                'password': 'StrongPassword123!',
            }).status_code,
            403,
        )

        response = self.client.get(
            reverse('dashboard:managed_users') + '?role=admin',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Scorer')

    def test_save_ground_with_existing_venue(self):
        from apps.matches.models import Ground, Venue

        self.client.force_login(self.admin_user)
        venue = Venue.objects.create(
            name='Riverside Oval',
            address='1 River Road',
            city='Melbourne',
            state='VIC',
            country='Australia',
        )
        url = reverse('dashboard:local_management', kwargs={'entity': 'ground'})
        response = self.client.post(url, {
            'name': 'Main Ground',
            'venue': str(venue.pk),
            'surface': 'Turf',
            'capacity': '12000',
            'is_active': 'on',
            'create_venue': '0',
            'venue-name': '',
        })
        self.assertEqual(response.status_code, 302)
        ground = Ground.objects.get(name='Main Ground')
        self.assertEqual(ground.venue, venue)
        self.assertEqual(ground.capacity, 12000)
        follow = self.client.get(response.url)
        self.assertContains(follow, 'saved successfully')
        self.assertContains(follow, 'Main Ground')

    def test_save_ground_creates_venue_inline(self):
        from apps.matches.models import Ground, Venue

        self.client.force_login(self.admin_user)
        url = reverse('dashboard:local_management', kwargs={'entity': 'ground'})
        response = self.client.post(url, {
            'name': 'New Local Ground',
            'venue': '',
            'surface': 'Matting',
            'capacity': '',
            'is_active': 'on',
            'create_venue': '1',
            'venue-name': 'Community Park',
            'venue-address': '10 Park Lane',
            'venue-city': 'Geelong',
            'venue-state': 'VIC',
            'venue-country': 'Australia',
            'venue-description': 'Local community oval',
        })
        self.assertEqual(response.status_code, 302)
        venue = Venue.objects.get(name='Community Park')
        ground = Ground.objects.get(name='New Local Ground')
        self.assertEqual(ground.venue, venue)
        self.assertEqual(ground.capacity, 0)

    def test_save_ground_without_venue_shows_field_errors(self):
        from apps.matches.models import Ground, Venue

        self.client.force_login(self.admin_user)
        Venue.objects.create(
            name='Existing Stadium',
            address='2 High Street',
            city='Sydney',
            state='NSW',
            country='Australia',
        )
        url = reverse('dashboard:local_management', kwargs={'entity': 'ground'})
        response = self.client.post(url, {
            'name': 'Unassigned Ground',
            'venue': '',
            'create_venue': '0',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a venue or create a new one below.')
        self.assertContains(response, 'Unassigned Ground')
        self.assertFalse(Ground.objects.filter(name='Unassigned Ground').exists())

    def test_scorer_cannot_open_management_dashboard(self):
        scorer = self._managed_user('scorer@example.com', User.Role.SCORER)
        self.client.force_login(scorer)
        self.assertEqual(
            self.client.get(reverse('dashboard:admin_dashboard')).status_code,
            403,
        )
