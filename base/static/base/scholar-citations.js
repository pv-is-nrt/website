(() => {
    const form = document.querySelector('#citation-update-form');
    const records = JSON.parse(document.querySelector('#citation-records').textContent);
    const button = form.querySelector('button');
    const progress = document.querySelector('#citation-progress');
    const current = document.querySelector('#citation-current');
    const results = document.querySelector('#citation-results');
    const resultsBody = document.querySelector('#citation-results-body');
    const previousTotal = document.querySelector('#citation-previous-total');
    const currentTotal = document.querySelector('#citation-current-total');
    const scholarCitations = document.querySelector('#scholar-citations');
    const scholarHIndex = document.querySelector('#scholar-h-index');
    const scholarI10Index = document.querySelector('#scholar-i10-index');
    const scholarUpdatedOn = document.querySelector('#scholar-updated-on');
    let previousTotalCount = 0;

    function formatDate(value) {
        if (!value) return 'N/A';
        const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
        const date = dateOnly
            ? new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
            : new Date(value);
        return Number.isNaN(date.getTime()) ? 'N/A' : new Intl.DateTimeFormat('en-US', {
            year: 'numeric', month: 'short', day: 'numeric',
        }).format(date);
    }

    function citationCount(value) {
        const count = Number.parseInt(String(value || '').replace(/,/g, ''), 10);
        return Number.isFinite(count) ? count : 0;
    }

    function addResult(record, result) {
        const row = document.createElement('tr');
        const values = [
            record.title,
            result.old_count ?? record.citations ?? 'N/A',
            result.new_count === undefined ? (record.citations || 'N/A') : result.new_count,
            formatDate(result.updated_on || record.citations_updated_on),
            result.status || 'Updated',
        ];
        values.forEach((value, index) => {
            const cell = document.createElement('td');
            cell.textContent = value;
            if (index === 4 && result.status !== 'Updated' && !result.status.startsWith('Skipped')) {
                cell.className = 'citation-error';
            }
            row.append(cell);
        });
        resultsBody.append(row);
    }

    function updateProfile(profile) {
        scholarCitations.textContent = profile.citations ?? 'Not yet available';
        scholarHIndex.textContent = profile.h_index ?? 'Not yet available';
        scholarI10Index.textContent = profile.i10_index ?? 'Not yet available';
        scholarUpdatedOn.textContent = profile.updated_at
            ? `Last updated ${formatDate(profile.updated_at)}`
            : 'No cached Google Scholar data yet.';
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        button.disabled = true;
        progress.hidden = false;
        progress.removeAttribute('value');
        current.hidden = false;
        results.hidden = false;
        previousTotalCount = records.reduce((total, record) => total + citationCount(record.citations), 0);
        previousTotal.textContent = previousTotalCount.toLocaleString();
        currentTotal.textContent = previousTotalCount.toLocaleString();
        resultsBody.replaceChildren();
        current.textContent = 'Checking the Scholar profile cache...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: { 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value },
            });
            const data = await response.json();
            const resultsById = new Map((data.results || []).map((result) => [result.id, result]));

            for (const record of records) {
                const result = resultsById.get(record.id) || {
                    old_count: record.citations,
                    new_count: record.citations,
                    updated_on: record.citations_updated_on,
                    status: data.error || 'No result returned',
                };
                addResult(record, result);
            }

            updateProfile(data.google_scholar || {});
            currentTotal.textContent = Number(data.database_total ?? previousTotalCount).toLocaleString();
            current.textContent = data.message || `Processed ${records.length} publications.`;
        } catch {
            for (const record of records) {
                addResult(record, {
                    old_count: record.citations,
                    new_count: record.citations,
                    updated_on: record.citations_updated_on,
                    status: 'Request failed; database counts were left unchanged.',
                });
            }
            current.textContent = 'The profile request failed; database counts were left unchanged.';
        }

        progress.max = Math.max(records.length, 1);
        progress.value = Math.max(records.length, 1);
        button.disabled = false;
    });
})();