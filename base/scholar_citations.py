import re
from urllib.parse import parse_qs, urlparse

from scholarly import scholarly


class ScholarCitationLookupError(Exception):
	pass


def normalize_title(title):
	return re.sub(r'\W+', ' ', title.casefold()).strip()


def scholar_user_id(profile_url):
	user_id = parse_qs(urlparse(profile_url).query).get('user', [''])[0]
	if not user_id:
		raise ScholarCitationLookupError('The configured Google Scholar URL has no profile ID.')
	return user_id


def lookup_profile_data(user_id):
	try:
		scholarly.set_retries(1)
		scholarly.set_timeout(20)
		author = scholarly.search_author_id(user_id, filled=False)
		author = scholarly.fill(author, sections=['indices', 'publications'], publication_limit=100)
	except Exception as error:
		raise ScholarCitationLookupError(
			'Google Scholar profile request failed ({})'.format(type(error).__name__)
		) from error

	if not author:
		raise ScholarCitationLookupError('Google Scholar returned an empty profile.')

	try:
		profile_data = {
			'citations': int(author['citedby']),
			'h_index': int(author['hindex']),
			'i10_index': int(author['i10index']),
		}
	except (KeyError, TypeError, ValueError) as error:
		raise ScholarCitationLookupError('Google Scholar profile metrics were incomplete.') from error

	counts = {}
	for publication in author.get('publications', []):
		title = publication.get('bib', {}).get('title', '')
		count = publication.get('num_citations')
		if title and count is not None:
			key = normalize_title(title)
			counts[key] = max(counts.get(key, 0), int(count))
	profile_data['publication_counts'] = counts
	return profile_data