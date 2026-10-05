from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Publication
from .scholar_citations import lookup_profile_citation_counts, normalize_title


class AdminDashboardTests(TestCase):
	def test_profile_lookup_fetches_only_publications(self):
		author = {'scholar_id': 'profile-id', 'filled': []}
		profile = {'publications': [{
			'bib': {'title': 'An exact publication title'},
			'num_citations': 42,
		}]}
		with patch('base.scholar_citations.scholarly.set_retries') as set_retries, \
				patch('base.scholar_citations.scholarly.set_timeout'), \
				patch('base.scholar_citations.scholarly.search_author_id', return_value=author) as search_author, \
				patch('base.scholar_citations.scholarly.fill', return_value=profile) as fill_profile:
			counts = lookup_profile_citation_counts('profile-id')

		self.assertEqual(counts[normalize_title('An exact publication title')], 42)
		set_retries.assert_called_once_with(1)
		search_author.assert_called_once_with('profile-id', filled=False)
		fill_profile.assert_called_once_with(author, sections=['publications'], publication_limit=100)

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
		self.assertContains(response, 'Update publication citation counts')

	def test_scholar_citation_task_updates_publications_from_profile(self):
		user = get_user_model().objects.create_user(
			username='citation-task-test',
			password='test-password',
			is_staff=True,
		)
		self.client.force_login(user)
		publication = Publication.objects.create(
			title='An exact publication title',
			authors='Prateek Verma',
			citations='12',
		)
		with patch('base.views.BasicInformation.objects.get', return_value=SimpleNamespace(
			scholar_url='https://scholar.google.com/citations?user=profile-id',
		)), patch('base.views.lookup_profile_citation_counts', return_value={
			normalize_title(publication.title): 42,
		}) as lookup_profile:
			response = self.client.post(reverse('admin-scholar-citations-update'))

		publication.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		result = response.json()['results'][0]
		self.assertEqual(result['title'], publication.title)
		self.assertEqual(result['old_count'], '12')
		self.assertEqual(result['new_count'], 42)
		self.assertEqual(result['updated_on'], timezone.localtime(publication.updated_at).date().isoformat())
		self.assertEqual(result['status'], 'Updated')
		self.assertEqual(response.json()['database_total'], 42)
		self.assertEqual(response.json()['scholar_total'], 42)
		self.assertEqual(publication.citations, '42')
		lookup_profile.assert_called_once_with('profile-id')

	def test_recently_updated_publication_is_refreshed_from_profile(self):
		user = get_user_model().objects.create_user(
			username='citation-refresh-test',
			password='test-password',
			is_staff=True,
		)
		self.client.force_login(user)
		publication = Publication.objects.create(
			title='Recently checked publication',
			authors='Prateek Verma',
			citations='18',
		)

		with patch('base.views.BasicInformation.objects.get', return_value=SimpleNamespace(
			scholar_url='https://scholar.google.com/citations?user=profile-id',
		)), patch('base.views.lookup_profile_citation_counts', return_value={
			normalize_title(publication.title): 27,
		}) as lookup_profile:
			response = self.client.post(reverse('admin-scholar-citations-update'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['results'][0]['status'], 'Updated')
		self.assertEqual(response.json()['results'][0]['new_count'], 27)
		lookup_profile.assert_called_once_with('profile-id')

	def test_django_admin_is_available_at_models_path(self):
		response = self.client.get('/admin/models/login/')

		self.assertEqual(response.status_code, 200)
