(() => {
    const form = document.querySelector('#citation-update-form');
    const records = JSON.parse(document.querySelector('#citation-records').textContent);
    const button = document.querySelector('#citation-update-button');
    const progressContainer = document.querySelector('#citation-progress-container');
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

    function setProgress(completed, total) {
        const percent = total ? Math.round((completed / total) * 100) : 100;
        progress.style.width = `${percent}%`;
        progressContainer.setAttribute('aria-valuenow', String(percent));
    }

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

    function sortRecords(resultsById = new Map()) {
        return [...records].sort((left, right) => {
            const leftCount = citationCount(resultsById.get(left.id)?.new_count ?? left.citations);
            const rightCount = citationCount(resultsById.get(right.id)?.new_count ?? right.citations);
            if (leftCount !== rightCount) return rightCount - leftCount;
            const leftDate = left.date ? Date.parse(left.date) : 0;
            const rightDate = right.date ? Date.parse(right.date) : 0;
            return rightDate - leftDate;
        });
    }

    function comparableCitationCount(value) {
        const text = String(value ?? '').replace(/,/g, '').trim();
        if (!text) return null;
        const count = Number(text);
        return Number.isFinite(count) ? count : text;
    }

    function addResult(record, result) {
        const row = document.createElement('tr');
        const previousCount = result.old_count ?? record.citations ?? 'N/A';
        const currentCount = result.new_count === undefined
            ? (record.citations ?? 'N/A')
            : result.new_count;
        const values = [
            record.title,
            previousCount,
            currentCount,
            formatDate(result.updated_on || record.citations_updated_on),
            result.status || 'Updated',
        ];
        values.forEach((value, index) => {
            const cell = document.createElement('td');
            if (index === 0) {
                cell.textContent = record.title;
                const containerTitle = record['venue__name'] || record.publisher;
                const year = record.date ? record.date.slice(0, 4) : '';
                [
                    containerTitle ? ['em', containerTitle] : null,
                    year ? ['strong', year] : null,
                ].filter(Boolean).forEach(([tagName, text]) => {
                    cell.append(document.createTextNode(', '));
                    const detail = document.createElement(tagName);
                    detail.textContent = text;
                    cell.append(detail);
                });
            } else {
                cell.textContent = value;
            }
            if (index === 2 && comparableCitationCount(previousCount) !== comparableCitationCount(currentCount)) {
                cell.classList.add('color-accent');
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

    function submitAdminForm(control) {
        const form = control.closest('form');
        const action = control.dataset.adminAction;
        if (action) form.querySelector('input[name="action"]').value = action;
        form.requestSubmit();
    }

    document.addEventListener('click', (event) => {
        const control = event.target.closest('[data-admin-submit]');
        if (control) submitAdminForm(control);
    });
    document.addEventListener('keydown', (event) => {
        const control = event.target.closest('[data-admin-submit]');
        if (!control || (event.key !== 'Enter' && event.key !== ' ')) return;
        event.preventDefault();
        submitAdminForm(control);
    });

    document.addEventListener('submit', async (event) => {
        const form = event.target;
        if (!form.matches('[data-crossref-preview]')) return;
        event.preventDefault();

        const recordKey = form.querySelector('[name="record_key"]').value;
        const preview = document.getElementById(`crossref-preview-${recordKey}`);
        const control = form.querySelector('[data-admin-submit]');
        control.setAttribute('aria-disabled', 'true');
        try {
            const response = await fetch(form.getAttribute('action'), {
                method: 'POST',
                body: new FormData(form),
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) throw new Error(`HTTP ${response.status} from ${response.url}`);
            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch {
                throw new Error('The server returned an unexpected response.');
            }
            document.querySelectorAll('[id^="crossref-preview-"]').forEach((container) => {
                if (container !== preview) container.replaceChildren();
            });
            preview.innerHTML = data.html;
        } catch (error) {
            const message = document.createElement('p');
            message.className = 'server-message-minimal';
            message.textContent = `Could not load the Crossref preview: ${error.message}`;
            preview.replaceChildren(message);
        } finally {
            control.setAttribute('aria-disabled', 'false');
        }
    });

    button.addEventListener('click', () => {
        if (button.getAttribute('aria-disabled') !== 'true') form.requestSubmit();
    });
    button.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        if (button.getAttribute('aria-disabled') !== 'true') form.requestSubmit();
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        button.setAttribute('aria-disabled', 'true');
        progressContainer.hidden = false;
        setProgress(0, records.length);
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

            for (const [index, record] of sortRecords(resultsById).entries()) {
                const result = resultsById.get(record.id) || {
                    old_count: record.citations,
                    new_count: record.citations,
                    updated_on: record.citations_updated_on,
                    status: data.error || 'No result returned',
                };
                addResult(record, result);
                setProgress(index + 1, records.length);
            }

            updateProfile(data.google_scholar || {});
            currentTotal.textContent = Number(data.database_total ?? previousTotalCount).toLocaleString();
            current.textContent = data.message || `Processed ${records.length} publications.`;
        } catch {
            for (const [index, record] of sortRecords().entries()) {
                addResult(record, {
                    old_count: record.citations,
                    new_count: record.citations,
                    updated_on: record.citations_updated_on,
                    status: 'Request failed; database counts were left unchanged.',
                });
                setProgress(index + 1, records.length);
            }
            current.textContent = 'The profile request failed; database counts were left unchanged.';
        }

        setProgress(records.length, records.length);
        button.setAttribute('aria-disabled', 'false');
    });
})();