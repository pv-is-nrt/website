const preferencesFormToken = document.querySelector('#new-category-form [name="csrfmiddlewaretoken"]').value;

function preferenceStatus(message, isError = false) {
    const status = document.querySelector('#page-status');
    status.textContent = message;
    status.classList.toggle('status-error', isError);
}

async function preferencePost(url, values) {
    const body = new URLSearchParams({ csrfmiddlewaretoken: preferencesFormToken, ...values });
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not save this change.');
    return result;
}

function categoryRow(category) {
    const row = document.querySelector('#category-row-template').content.firstElementChild.cloneNode(true);
    row.dataset.updateUrl = category.update_url;
    row.dataset.deleteUrl = category.delete_url;
    const input = row.querySelector('.category-name');
    input.value = category.name;
    row.querySelector('.delete-category').setAttribute('aria-label', `Delete ${category.name}`);
    row.querySelectorAll('.color-option').forEach((option) => {
        const selected = option.dataset.color === category.color;
        option.classList.toggle('is-selected', selected);
        option.setAttribute('aria-checked', String(selected));
    });
    return row;
}

document.querySelector('#default-reminder').addEventListener('change', async (event) => {
    try {
        await preferencePost(event.currentTarget.dataset.saveUrl, {
            default_reminder_minutes: event.currentTarget.value,
        });
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

document.querySelector('#new-category-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.elements.name;
    try {
        const category = await preferencePost(form.action, { name: input.value.trim() });
        document.querySelector('#empty-categories')?.remove();
        const row = categoryRow(category);
        document.querySelector('#category-list').append(row);
        window.lucide?.createIcons();
        input.value = '';
        input.focus();
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

document.querySelector('#category-list').addEventListener('focusout', async (event) => {
    if (!event.target.matches('.category-name')) return;
    const input = event.target;
    const row = input.closest('.managed-category');
    try {
        const category = await preferencePost(row.dataset.updateUrl, { name: input.value.trim() });
        input.value = category.name;
        row.querySelector('.delete-category').setAttribute('aria-label', `Delete ${category.name}`);
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

document.querySelector('#category-list').addEventListener('click', async (event) => {
    const colorOption = event.target.closest('.color-option');
    if (colorOption) {
        const row = colorOption.closest('.managed-category');
        try {
            await preferencePost(row.dataset.updateUrl, { color: colorOption.dataset.color });
            row.querySelectorAll('.color-option').forEach((option) => {
                const selected = option === colorOption;
                option.classList.toggle('is-selected', selected);
                option.setAttribute('aria-checked', String(selected));
            });
            preferenceStatus('');
        } catch (error) {
            preferenceStatus(error.message, true);
        }
        return;
    }

    const button = event.target.closest('.delete-category');
    if (!button) return;
    const row = button.closest('.managed-category');
    try {
        await preferencePost(row.dataset.deleteUrl, {});
        row.remove();
        if (!document.querySelector('.managed-category')) {
            const empty = document.createElement('p');
            empty.className = 'empty-state';
            empty.id = 'empty-categories';
            empty.textContent = 'No categories yet.';
            document.querySelector('#category-list').append(empty);
        }
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

window.lucide?.createIcons();