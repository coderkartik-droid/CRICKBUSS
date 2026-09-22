from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.urls import reverse
from django.test import TestCase


User = get_user_model()


class AccountsFlowTestCase(TestCase):
    def setUp(self):
        self.client = self.client_class()

    def test_registration_creates_active_user_and_redirects_to_login(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'localfan',
            'email': 'fan@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(email='fan@example.com')
        self.assertTrue(user.is_active)
        self.assertEqual(user.username, 'localfan')

    def test_registration_rejects_duplicate_username_and_email(self):
        User.objects.create_user(username='existing', email='existing@example.com', password='StrongPassword123!')
        response = self.client.post(reverse('accounts:register'), {
            'username': 'existing',
            'email': 'existing@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already')

    def test_login_accepts_username_or_email(self):
        user = User.objects.create_user(
            username='localfan', email='fan@example.com', password='StrongPassword123!'
        )
        for identifier in (user.username, user.email):
            self.client.logout()
            response = self.client.post(reverse('accounts:login'), {
                'username': identifier,
                'password': 'StrongPassword123!',
            })
            self.assertRedirects(response, reverse('dashboard:home'))
            self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_profile_updates_extended_fields(self):
        user = User.objects.create_user(
            username='localfan', email='fan@example.com', password='StrongPassword123!'
        )
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Local',
            'last_name': 'Fan',
            'username': 'updatedfan',
            'email': 'updated@example.com',
            'phone_number': '1234567890',
            'date_of_birth': '1995-05-10',
            'gender': 'prefer_not_to_say',
            'country': 'India',
            'state': 'Maharashtra',
            'city': 'Pune',
            'bio': 'Local cricket supporter',
            'favorite_team': 'Riverside CC',
            'favorite_player': 'A Player',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        user.refresh_from_db()
        self.assertEqual(user.email, 'updated@example.com')
        self.assertEqual(user.city, 'Pune')
