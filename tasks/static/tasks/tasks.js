const csrfToken = document.querySelector('#quick-entry [name="csrfmiddlewaretoken"]').value;
const openTasks = document.querySelector('#open-tasks');
const completedTasks = document.querySelector('#completed-tasks');
const titleTimers = new WeakMap();

function setStatus(element, message, isError = false) {
    element.textContent = message;
    element.classList.toggle('status-error', isError);
}

async function postForm(url, values) {
    const body = new URLSearchParams({ csrfmiddlewaretoken: csrfToken });
    for (const [key, value] of Object.entries(values)) {
        if (Array.isArray(value)) value.forEach((item) => body.append(`${key}[]`, item));
        else body.append(key, value);
    }
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not save this change.');
    return result;
}

function updateCount() {
    document.querySelector('#active-count').textContent = openTasks.querySelectorAll('.task-row').length;
    const empty = document.querySelector('#empty-open');
    if (empty) empty.remove();
    if (!openTasks.querySelector('.task-row')) {
        const message = document.createElement('p');
        message.className = 'empty-state';
        message.id = 'empty-open';
        message.textContent = 'Nothing on the list yet.';
        openTasks.append(message);
    }
}

async function saveField(row, field, value, input) {
    const status = row.querySelector('.row-status');
    try {
        const result = await postForm(row.dataset.updateUrl, { field, value });
        setStatus(status, '');
        if (field === 'completed') {
            row.classList.toggle('is-complete', result.completed);
            (result.completed ? completedTasks : openTasks).prepend(row);
            updateCount();
        }
    } catch (error) {
        setStatus(status, error.message, true);
        if (input.type === 'checkbox') input.checked = !input.checked;
        if (input.matches('.category-choice')) updateCategoryChips(row);
        if (input.matches('.reminder-toggle')) {
            const enabled = input.getAttribute('aria-pressed') !== 'true';
            input.setAttribute('aria-pressed', String(enabled));
            input.classList.toggle('is-enabled', enabled);
        }
    }
}

function updateCategoryChips(row) {
    const container = row.querySelector('.task-category-chips');
    const addButton = container.querySelector('.category-add');
    const menu = container.querySelector('.category-menu');
    const chips = [...container.querySelectorAll('.category-choice:checked')].map((choice) => {
        const chip = document.createElement('span');
        chip.className = 'category-chip';
        chip.style.setProperty('--category-color', choice.dataset.color);

        const name = document.createElement('span');
        name.textContent = choice.dataset.name;

        const remove = document.createElement('button');
        remove.className = 'category-remove';
        remove.type = 'button';
        remove.dataset.categoryId = choice.value;
        remove.setAttribute('aria-label', `Remove ${choice.dataset.name}`);
        remove.innerHTML = '<i data-lucide="x"></i>';

        chip.append(name, remove);
        return chip;
    });
    container.replaceChildren(...chips, addButton, menu);
    window.lucide?.createIcons();
}

function updateDueLabel(row, value) {
    const label = row.querySelector('.due-label');
    if (!value) {
        label.textContent = '';
        return;
    }
    label.textContent = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(value));
}

function makeTaskRow(task) {
    const row = document.querySelector('#task-row-template').content.firstElementChild.cloneNode(true);
    row.dataset.taskId = task.id;
    row.dataset.updateUrl = task.update_url;
    row.querySelector('.task-title').value = task.title;
    row.querySelector('.priority-select').value = task.priority;
    row.querySelector('.reminder-toggle').setAttribute('aria-pressed', String(task.reminder_enabled));
    return row;
}

document.querySelector('#quick-entry').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const titleInput = form.elements.title;
    const status = document.querySelector('#page-status');
    const button = form.querySelector('button');
    button.disabled = true;
    try {
        const task = await postForm(form.action, { title: titleInput.value.trim() });
        document.querySelector('#empty-open')?.remove();
        const row = makeTaskRow(task);
        openTasks.prepend(row);
        window.lucide?.createIcons();
        titleInput.value = '';
        titleInput.focus();
        setStatus(status, '');
        updateCount();
    } catch (error) {
        setStatus(status, error.message, true);
    } finally {
        button.disabled = false;
    }
});

document.addEventListener('input', (event) => {
    const input = event.target;
    if (!input.matches('.task-title')) return;
    clearTimeout(titleTimers.get(input));
    titleTimers.set(input, setTimeout(() => saveField(input.closest('.task-row'), 'title', input.value, input), 500));
});

document.addEventListener('focusout', (event) => {
    const input = event.target;
    if (!input.matches('.task-title')) return;
    clearTimeout(titleTimers.get(input));
    saveField(input.closest('.task-row'), 'title', input.value, input);
});

document.addEventListener('click', (event) => {
    const categoryRemove = event.target.closest('.category-remove');
    if (categoryRemove) {
        const row = categoryRemove.closest('.task-row');
        const choice = [...row.querySelectorAll('.category-choice')].find((item) => item.value === categoryRemove.dataset.categoryId);
        choice.checked = false;
        choice.dispatchEvent(new Event('change', { bubbles: true }));
        return;
    }

    const categoryAdd = event.target.closest('.category-add');
    if (categoryAdd) {
        const menu = categoryAdd.nextElementSibling;
        const opening = menu.hidden;
        document.querySelectorAll('.category-menu').forEach((item) => { item.hidden = true; });
        document.querySelectorAll('.category-add').forEach((item) => item.setAttribute('aria-expanded', 'false'));
        menu.hidden = !opening;
        categoryAdd.setAttribute('aria-expanded', String(opening));
        return;
    }
    if (event.target.closest('.category-menu')) return;
    document.querySelectorAll('.category-menu').forEach((menu) => { menu.hidden = true; });
    document.querySelectorAll('.category-add').forEach((item) => item.setAttribute('aria-expanded', 'false'));

    const dueButton = event.target.closest('.due-button');
    if (dueButton) {
        const input = dueButton.nextElementSibling;
        if (typeof input.showPicker === 'function') input.showPicker();
        else input.focus();
    }

    const reminderButton = event.target.closest('.reminder-toggle');
    if (reminderButton) {
        const enabled = reminderButton.getAttribute('aria-pressed') !== 'true';
        reminderButton.setAttribute('aria-pressed', String(enabled));
        reminderButton.classList.toggle('is-enabled', enabled);
        saveField(reminderButton.closest('.task-row'), 'reminder_enabled', String(enabled), reminderButton);
    }
});

document.addEventListener('change', (event) => {
    const input = event.target;
    const row = input.closest('.task-row');
    if (!row) return;
    if (input.matches('.category-choice')) {
        const selected = [...row.querySelectorAll('.category-choice:checked')].map((item) => item.value);
        updateCategoryChips(row);
        saveField(row, 'categories', selected, input);
    } else if (input.matches('.due-input')) {
        updateDueLabel(row, input.value);
        saveField(row, 'due_at', input.value, input);
    } else if (input.matches('.task-complete')) {
        saveField(row, 'completed', String(input.checked), input);
    } else if (input.matches('.priority-select')) {
        saveField(row, 'priority', input.value, input);
    }
});

window.lucide?.createIcons();