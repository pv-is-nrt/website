from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminDashboardTests(TestCase):
	def test_dashboard_redirects_non_staff_users_to_admin_login(self):
		response = self.client.get(reverse('admin-dashboard'))

		self.assertRedirects(
			response,
			'/admin/models/login/?next=/admin/',
			fetch_redirect_response=False,
		)

	def test_dashboard_is_available_to_staff_users(self):
		user = get_user_model().objects.create_user(
			username='admin-dashboard-test',
			password='test-password',
			is_staff=True,
		)
		self.client.force_login(user)

		response = self.client.get(reverse('admin-dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Custom admin tasks')

	def test_django_admin_is_available_at_models_path(self):
		response = self.client.get('/admin/models/login/')

		self.assertEqual(response.status_code, 200)
