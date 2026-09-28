import html
import re
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
import json


def normalize_doi(value):
    """Return a DOI suitable for the Crossref API, or an empty string."""
    doi = (value or '').strip()
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi, flags=re.IGNORECASE)
    return doi.rstrip(' .,;')


def _abstract_to_text(value):
    if not value:
        return ''
    text = re.sub(r'<[^>]+>', ' ', html.unescape(value))
    return re.sub(r'\s+', ' ', text).strip()


def _publisher_url(item):
    candidates = [
        item.get('resource', {}).get('primary', {}).get('URL'),
        *(link.get('URL') for link in item.get('link', [])),
        item.get('URL', ''),
    ]
    for candidate in candidates:
        if candidate and not re.match(r'^https?://(dx\.)?doi\.org/', candidate, re.IGNORECASE):
            return candidate
    return next((candidate for candidate in candidates if candidate), '')


def _date_to_iso(date_parts):
    if not date_parts or len(date_parts) < 3:
        return ''
    return '{:04d}-{:02d}-{:02d}'.format(*[int(part) for part in date_parts[:3]])


def _select_publication_date(item):
    candidates = []
    for source in ('published-online', 'published-print'):
        date_parts = item.get(source, {}).get('date-parts', [[]])[0]
        date_value = _date_to_iso(date_parts)
        if date_value:
            candidates.append((date_value, source))
    if candidates:
        return min(candidates)

    issued_parts = item.get('issued', {}).get('date-parts', [[]])[0]
    issued_value = _date_to_iso(issued_parts)
    return (issued_value, 'issued') if issued_value else ('', '')


def _fetch_json(url, mailto, timeout):
    request = Request(
        url,
        headers={
            'Accept': 'application/json',
            'User-Agent': 'Prateek-Verma-Website/1.0 (mailto:{})'.format(mailto),
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def _openalex_abstract(item):
    inverted_index = item.get('abstract_inverted_index') or {}
    if not inverted_index:
        return ''
    ordered_words = [''] * (max(position for positions in inverted_index.values() for position in positions) + 1)
    for word, positions in inverted_index.items():
        for position in positions:
            ordered_words[position] = word
    return ' '.join(word for word in ordered_words if word)


def _fetch_abstract_fallback(doi, mailto, timeout):
    encoded_doi = quote('https://doi.org/{}'.format(doi), safe=':/')
    try:
        item = _fetch_json('https://api.openalex.org/works/{}?mailto={}'.format(encoded_doi, quote(mailto, safe='')), mailto, timeout)
        abstract = _openalex_abstract(item)
        if abstract:
            return abstract
    except Exception:
        pass
    try:
        item = _fetch_json('https://api.semanticscholar.org/graph/v1/paper/DOI:{}?fields=abstract'.format(quote(doi, safe='')), mailto, timeout)
        return _abstract_to_text(item.get('abstract', ''))
    except Exception:
        return ''


def fetch_metadata(doi, mailto, timeout=15):
    normalized_doi = normalize_doi(doi)
    url = 'https://api.crossref.org/works/' + quote(normalized_doi, safe='')
    request = Request(
        url,
        headers={
            'Accept': 'application/json',
            'User-Agent': 'Prateek-Verma-Website/1.0 (mailto:{})'.format(mailto),
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode('utf-8'))
    item = payload['message']
    date_value, date_source = _select_publication_date(item)
    abstract = _abstract_to_text(item.get('abstract', ''))
    if len(abstract.split()) < 50:
        fallback_abstract = _fetch_abstract_fallback(normalized_doi, mailto, timeout)
        if len(fallback_abstract.split()) > len(abstract.split()):
            abstract = fallback_abstract
    return {
        'doi': normalize_doi(item.get('DOI', normalized_doi)),
        'title': html.unescape((item.get('title') or [''])[0]),
        'authors': ', '.join(
            html.unescape('{} {}'.format(author.get('given', ''), author.get('family', '')).strip())
            for author in item.get('author', [])
        ),
        'publisher': html.unescape(item.get('publisher', '')),
        'container_title': html.unescape((item.get('container-title') or [''])[0]),
        'volume': item.get('volume', ''),
        'issue': item.get('issue', ''),
        'pages': item.get('page', ''),
        'article_number': item.get('article-number', ''),
        'publication_type': item.get('type', ''),
        'keywords': ', '.join(html.unescape(keyword) for keyword in item.get('subject', [])),
        'date': date_value,
        'date_source': date_source,
        'abstract': abstract,
        'link': _publisher_url(item),
        'citations': str(item.get('is-referenced-by-count', '')),
    }


def fetch_many(records, mailto):
    results = []
    for index, record in enumerate(records):
        if index:
            time.sleep(1)
        try:
            metadata = fetch_metadata(record['doi'], mailto)
            results.append({
                'record_key': record['key'],
                'record_type': record['type'],
                'record_id': record['id'],
                'ok': True,
                'metadata': metadata,
            })
        except Exception as error:
            results.append({
                'record_key': record['key'],
                'record_type': record['type'],
                'record_id': record['id'],
                'ok': False,
                'error': str(error),
            })
    return results