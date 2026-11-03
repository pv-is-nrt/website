const csrfToken = document.querySelector('#task-csrf [name="csrfmiddlewaretoken"]').value;
const titleTimers = new WeakMap();
const undoStorageKey = 'tasks-pending-undo';

function setStatus(element, message, isError = false) {
    if (!element) return;
    element.textContent = message;
    element.classList.toggle('hidden', !message);
    element.classList.toggle('text-rust', isError);
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

async function saveField(row, field, value, input) {
    const status = row.querySelector(':scope > .row-status');
    try {
        const result = await postForm(row.dataset.updateUrl, { field, value });
        setStatus(status, '');
        if (['completed', 'cancelled', 'archived', 'delete'].includes(field)) {
            if (field !== 'delete' && value === 'true') {
                const actionName = { completed: 'completed', cancelled: 'cancelled', archived: 'archived' }[field];
                try {
                    window.sessionStorage.setItem(undoStorageKey, JSON.stringify({
                        url: row.dataset.updateUrl,
                        field: field === 'completed' && result.next_task_id ? 'undo_completion' : field,
                        value: 'false',
                        successorId: result.next_task_id,
                        message: `Task ${actionName}`,
                        expiresAt: Date.now() + 15000,
                    }));
                } catch {}
            }
            window.location.reload();
        } else if (field === 'categories' && document.querySelector('.tag-filter input:checked')) {
            window.location.reload();
        }
    } catch (error) {
        setStatus(status, error.message, true);
        if (input.matches('[data-task-action]')) input.disabled = false;
        if (input.type === 'checkbox') input.checked = !input.checked;
        if (input.matches('.category-choice')) updateCategoryChips(row);
        if (input.matches('.reminder-toggle')) {
            const enabled = input.getAttribute('aria-pressed') !== 'true';
            input.setAttribute('aria-pressed', String(enabled));
            input.classList.toggle('text-rust', enabled);
        }
    }
}

function parseQuickCapture(rawValue) {
    let title = rawValue.trim();
    const categories = [];
    let priority = '';
    let dueAt = '';
    let recurrence = '';

    const datePattern = /\b(?:(?:by|on|before|due|deadline|until)\s+)?(today|tomorrow|(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)\b/i;
    const dateMatch = title.match(datePattern);
    if (dateMatch) {
        const [year, month, day] = document.querySelector('#quick-capture-tags').dataset.today.split('-').map(Number);
        const dateToken = dateMatch[1].toLowerCase();
        let dueDate;
        if (dateToken === 'today' || dateToken === 'tomorrow') {
            dueDate = new Date(Date.UTC(year, month - 1, day + (dateToken === 'tomorrow' ? 1 : 0)));
        } else if (/^\d{4}-/.test(dateToken)) {
            const [dateYear, dateMonth, dateDay] = dateToken.split('-').map(Number);
            dueDate = new Date(Date.UTC(dateYear, dateMonth - 1, dateDay));
        } else if (dateToken.includes('/')) {
            const [dateMonth, dateDay, rawYear] = dateToken.split('/').map(Number);
            let dateYear = rawYear || year;
            if (dateYear < 100) dateYear += 2000;
            dueDate = new Date(Date.UTC(dateYear, dateMonth - 1, dateDay));
        } else {
            const weekdayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
            const weekday = dateToken.replace('next ', '');
            let dayOffset = (weekdayNames.indexOf(weekday) - new Date(Date.UTC(year, month - 1, day)).getUTCDay() + 7) % 7;
            if (dateToken.startsWith('next ') && dayOffset === 0) dayOffset = 7;
            dueDate = new Date(Date.UTC(year, month - 1, day + dayOffset));
        }
        const pad = (part) => String(part).padStart(2, '0');
        dueAt = `${dueDate.getUTCFullYear()}-${pad(dueDate.getUTCMonth() + 1)}-${pad(dueDate.getUTCDate())}T09:00`;
        title = title.replace(datePattern, ' ');
    }

    const priorityPattern = /(^|\s)p([1-5])(?=$|[\s,])/i;
    const priorityMatch = title.match(priorityPattern);
    if (priorityMatch) {
        priority = String(6 - Number(priorityMatch[2]));
        title = title.replace(priorityPattern, '$1 ');
    }

    const recurrencePattern = /(^|\s)every\s+(day|week|month|year)(?=$|[\s,])/i;
    const recurrenceMatch = title.match(recurrencePattern);
    if (recurrenceMatch) {
        recurrence = { day: 'daily', week: 'weekly', month: 'monthly', year: 'yearly' }[
            recurrenceMatch[2].toLowerCase()
        ];
        title = title.replace(recurrencePattern, '$1 ');
    }

    const availableCategories = [...document.querySelectorAll('#quick-capture-tags [data-category-id]')]
        .sort((left, right) => right.dataset.categoryName.length - left.dataset.categoryName.length);
    for (const category of availableCategories) {
        const tagPattern = new RegExp(`(^|\\s)[#@]${category.dataset.categoryName.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}(?=$|[\\s,])`, 'i');
        if (tagPattern.test(title)) {
            categories.push(category.dataset.categoryId);
            title = title.replace(tagPattern, '$1 ');
        }
    }

    return { title: title.replace(/\s+/g, ' ').trim(), priority, recurrence, due_at: dueAt, categories };
}

function renderQuickCaptureHighlight(value) {
    const highlight = document.querySelector('#quick-capture-highlight-text');
    const input = document.querySelector('#new-task-title');
    if (!highlight || !input) return;

    const dateToken = '(?:today|tomorrow|(?:next\\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\\d{4}-\\d{2}-\\d{2}|\\d{1,2}\\/\\d{1,2}(?:\\/\\d{2,4})?)';
    const matches = [];
    const collect = (pattern, className) => {
        for (const match of value.matchAll(pattern)) {
            matches.push({ start: match.index, end: match.index + match[0].length, text: match[0], className });
        }
    };
    collect(/\bp[1-5]\b/gi, 'capture-token-priority');
    collect(new RegExp(`\\b(?:by|on|before|due|deadline|until)\\s+${dateToken}\\b`, 'gi'), 'capture-token-date');
    collect(new RegExp(`\\b${dateToken}\\b`, 'gi'), 'capture-token-date');
    collect(/\bevery\s+(?:day|week|month|year)\b/gi, 'capture-token-repeat');

    const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&');
    for (const category of document.querySelectorAll('#quick-capture-tags [data-category-name]')) {
        collect(new RegExp(`[#@]${escapeRegExp(category.dataset.categoryName)}(?=$|[\\s,])`, 'gi'), 'capture-token-tag');
    }

    matches.sort((left, right) => left.start - right.start || right.end - left.end);
    highlight.replaceChildren();
    let cursor = 0;
    for (const match of matches) {
        if (match.start < cursor) continue;
        highlight.append(document.createTextNode(value.slice(cursor, match.start)));
        const token = document.createElement('span');
        token.className = match.className;
        token.textContent = match.text;
        highlight.append(token);
        cursor = match.end;
    }
    highlight.append(document.createTextNode(value.slice(cursor)));
    highlight.style.transform = `translateX(-${input.scrollLeft}px)`;
}

const quickCaptureInput = document.querySelector('#new-task-title');
quickCaptureInput?.addEventListener('input', () => renderQuickCaptureHighlight(quickCaptureInput.value));
quickCaptureInput?.addEventListener('scroll', () => renderQuickCaptureHighlight(quickCaptureInput.value));
if (quickCaptureInput) renderQuickCaptureHighlight(quickCaptureInput.value);

function updateCategoryChips(row) {
    const container = row.querySelector('.task-category-chips');
    const chips = [...row.querySelectorAll('.category-choice:checked')].map((choice) => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip inline-flex min-h-7 items-center gap-[3px] rounded-full border py-0.5 pl-2.5 pr-1 text-xs';
        chip.style.setProperty('--tag-color', choice.dataset.color);

        const name = document.createElement('span');
        name.textContent = choice.dataset.name;

        const remove = document.createElement('button');
        remove.className = 'category-remove inline-grid h-6 w-6 place-items-center rounded-sm text-inherit opacity-65 transition-colors hover:bg-black/10 hover:opacity-100';
        remove.type = 'button';
        remove.dataset.categoryId = choice.value;
        remove.setAttribute('aria-label', `Remove tag ${choice.dataset.name}`);
        remove.innerHTML = '<i data-lucide="x"></i>';

        chip.append(name, remove);
        return chip;
    });
    container.replaceChildren(...chips);
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

function renderDueCalendar(picker) {
    const [year, month] = picker.dataset.month.split('-').map(Number);
    const firstWeekday = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const input = picker.closest('[data-due-picker-wrapper]').querySelector('.due-input');
    const selectedDate = input.value.slice(0, 10);
    const monthStart = new Date(year, month - 1, 1);
    const monthLabel = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(monthStart);
    const grid = picker.querySelector('[data-calendar-grid]');
    const pad = (value) => String(value).padStart(2, '0');
    const isoDate = (day) => `${year}-${pad(month)}-${pad(day)}`;
    const today = new Date();
    const todayValue = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;

    picker.querySelector('[data-calendar-month-label]').textContent = monthLabel;
    picker.querySelector('.due-time').value = picker.dataset.time || '09:00';
    grid.replaceChildren();

    for (let index = 0; index < firstWeekday; index += 1) {
        const blank = document.createElement('span');
        blank.className = 'h-8 w-8';
        blank.setAttribute('aria-hidden', 'true');
        grid.append(blank);
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
        const dateValue = isoDate(day);
        const dayButton = document.createElement('button');
        dayButton.className = 'calendar-day grid h-8 w-8 place-items-center rounded-sm text-ink hover:bg-paper-faint focus-visible:outline-2 focus-visible:outline-forest';
        dayButton.type = 'button';
        dayButton.dataset.date = dateValue;
        dayButton.textContent = String(day);
        dayButton.setAttribute('aria-label', new Intl.DateTimeFormat(undefined, {
            weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
        }).format(new Date(year, month - 1, day)));
        dayButton.setAttribute('aria-pressed', String(dateValue === selectedDate));
        if (dateValue === selectedDate) {
            dayButton.classList.add('bg-forest', 'font-semibold', 'text-[var(--calendar-selected-text)]', 'hover:bg-forest');
        }
        if (dateValue === todayValue) {
            dayButton.classList.add('ring-1', 'ring-forest');
            dayButton.setAttribute('aria-current', 'date');
        }
        grid.append(dayButton);
    }
}

function positionDuePicker(picker, button) {
    const buttonRect = button.getBoundingClientRect();
    const pickerRect = picker.getBoundingClientRect();
    const left = Math.max(12, Math.min(buttonRect.left, window.innerWidth - pickerRect.width - 12));
    let top = buttonRect.bottom + 4;
    if (top + pickerRect.height > window.innerHeight - 12) {
        top = buttonRect.top - pickerRect.height - 4;
    }
    picker.style.left = `${left}px`;
    picker.style.top = `${Math.max(12, top)}px`;
}

function saveDueDate(input, value) {
    input.value = value;
    input.dispatchEvent(new Event('change', { bubbles: true }));
}

document.querySelector('#quick-entry')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const titleInput = form.elements.title;
    const status = document.querySelector('#page-status');
    const button = form.querySelector('button');
    button.disabled = true;
    try {
        const values = parseQuickCapture(titleInput.value);
        await postForm(form.action, values);
        window.location.reload();
    } catch (error) {
        setStatus(status, error.message, true);
    } finally {
        button.disabled = false;
    }
});

document.addEventListener('submit', async (event) => {
    const form = event.target;
    if (!form.matches('.subtask-create-form')) return;
    event.preventDefault();
    const titleInput = form.elements.title;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
        await postForm(form.action, {
            title: titleInput.value.trim(),
            parent_id: form.elements.parent_id.value,
        });
        window.location.reload();
    } catch (error) {
        setStatus(document.querySelector('#page-status'), error.message, true);
        button.disabled = false;
    }
});

document.addEventListener('input', (event) => {
    const input = event.target;
    if (!input.matches('.task-title, .subtask-title')) return;
    clearTimeout(titleTimers.get(input));
    titleTimers.set(input, setTimeout(() => saveField(input.closest('.task-row, .subtask-row'), 'title', input.value, input), 500));
});

document.addEventListener('focusout', (event) => {
    const input = event.target;
    if (!input.matches('.task-title, .subtask-title')) return;
    clearTimeout(titleTimers.get(input));
    saveField(input.closest('.task-row, .subtask-row'), 'title', input.value, input);
});

document.addEventListener('click', (event) => {
    const moreMenu = document.querySelector('#task-more-menu');
    if (moreMenu?.open && !moreMenu.contains(event.target)) moreMenu.open = false;
    document.querySelectorAll('.repeat-control[open]').forEach((control) => {
        if (!control.contains(event.target)) control.open = false;
    });

    const detailsToggle = event.target.closest('.task-details-toggle');
    if (detailsToggle) {
        const panel = detailsToggle.closest('.task-content').querySelector('.task-details-panel');
        panel.hidden = !panel.hidden;
        detailsToggle.setAttribute('aria-expanded', String(!panel.hidden));
        return;
    }

    const taskAction = event.target.closest('[data-task-action]');
    if (taskAction) {
        const row = taskAction.closest('.task-row, .subtask-row');
        if (taskAction.dataset.taskAction === 'delete') {
            const subtaskCount = row.matches('.subtask-row') ? 0 : row.querySelectorAll('.subtask-row').length;
            const message = row.matches('.subtask-row')
                ? 'Delete this step? This cannot be undone.'
                : subtaskCount
                    ? `Permanently delete this task and its ${subtaskCount} subtask${subtaskCount === 1 ? '' : 's'}? This cannot be undone.`
                    : 'Permanently delete this task? This cannot be undone.';
            if (!window.confirm(message)) return;
        }
        taskAction.disabled = true;
        saveField(row, taskAction.dataset.taskAction, taskAction.dataset.taskValue, taskAction);
        return;
    }

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

    document.querySelectorAll('.due-picker:not([hidden])').forEach((picker) => {
        const wrapper = picker.closest('[data-due-picker-wrapper]');
        if (!wrapper.contains(event.target)) {
            picker.hidden = true;
            wrapper.querySelector('.due-button').setAttribute('aria-expanded', 'false');
        }
    });

    const dueButton = event.target.closest('.due-button');
    if (dueButton) {
        const wrapper = dueButton.closest('[data-due-picker-wrapper]');
        const picker = wrapper.querySelector('.due-picker');
        const input = wrapper.querySelector('.due-input');
        const opening = picker.hidden;
        document.querySelectorAll('.due-picker').forEach((item) => { item.hidden = true; });
        document.querySelectorAll('.due-button').forEach((item) => item.setAttribute('aria-expanded', 'false'));
        picker.hidden = !opening;
        dueButton.setAttribute('aria-expanded', String(opening));
        if (opening) {
            const today = new Date();
            const dateValue = input.value.slice(0, 10) || `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
            picker.dataset.month = dateValue.slice(0, 7);
            picker.dataset.time = input.value.split('T')[1] || '09:00';
            renderDueCalendar(picker);
            positionDuePicker(picker, dueButton);
            picker.querySelector('.calendar-day[aria-pressed="true"]')?.focus();
        }
        return;
    }

    const monthButton = event.target.closest('[data-calendar-month]');
    if (monthButton) {
        const picker = monthButton.closest('.due-picker');
        const monthStart = new Date(`${picker.dataset.month}-01T00:00:00`);
        monthStart.setMonth(monthStart.getMonth() + Number(monthButton.dataset.calendarMonth));
        picker.dataset.month = `${monthStart.getFullYear()}-${String(monthStart.getMonth() + 1).padStart(2, '0')}`;
        renderDueCalendar(picker);
        return;
    }

    const calendarDay = event.target.closest('.calendar-day');
    if (calendarDay) {
        const picker = calendarDay.closest('.due-picker');
        const input = picker.closest('[data-due-picker-wrapper]').querySelector('.due-input');
        saveDueDate(input, `${calendarDay.dataset.date}T${picker.dataset.time || '09:00'}`);
        picker.dataset.month = calendarDay.dataset.date.slice(0, 7);
        renderDueCalendar(picker);
        picker.querySelector('.calendar-day[aria-pressed="true"]')?.focus();
        return;
    }

    const todayButton = event.target.closest('.due-today');
    if (todayButton) {
        const picker = todayButton.closest('.due-picker');
        const input = picker.closest('[data-due-picker-wrapper]').querySelector('.due-input');
        const today = new Date();
        const todayValue = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        saveDueDate(input, `${todayValue}T${picker.dataset.time || '09:00'}`);
        picker.dataset.month = todayValue.slice(0, 7);
        renderDueCalendar(picker);
        picker.querySelector('.calendar-day[aria-pressed="true"]')?.focus();
        return;
    }

    const clearDueButton = event.target.closest('.due-clear');
    if (clearDueButton) {
        const picker = clearDueButton.closest('.due-picker');
        const wrapper = picker.closest('[data-due-picker-wrapper]');
        saveDueDate(wrapper.querySelector('.due-input'), '');
        picker.hidden = true;
        const dueButton = wrapper.querySelector('.due-button');
        dueButton.setAttribute('aria-expanded', 'false');
        dueButton.focus();
    }

    const reminderButton = event.target.closest('.reminder-toggle');
    if (reminderButton) {
        const enabled = reminderButton.getAttribute('aria-pressed') !== 'true';
        reminderButton.setAttribute('aria-pressed', String(enabled));
            reminderButton.classList.toggle('text-rust', enabled);
        saveField(reminderButton.closest('.task-row'), 'reminder_enabled', String(enabled), reminderButton);
    }
});

window.addEventListener('resize', () => {
    const picker = document.querySelector('.due-picker:not([hidden])');
    if (picker) positionDuePicker(picker, picker.closest('[data-due-picker-wrapper]').querySelector('.due-button'));
});

window.addEventListener('scroll', () => {
    const picker = document.querySelector('.due-picker:not([hidden])');
    if (!picker) return;
    picker.hidden = true;
    picker.closest('[data-due-picker-wrapper]').querySelector('.due-button').setAttribute('aria-expanded', 'false');
}, true);

document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const duePicker = document.querySelector('.due-picker:not([hidden])');
    if (duePicker) {
        duePicker.hidden = true;
        duePicker.closest('[data-due-picker-wrapper]').querySelector('.due-button').focus();
        duePicker.closest('[data-due-picker-wrapper]').querySelector('.due-button').setAttribute('aria-expanded', 'false');
        return;
    }
    const moreMenu = document.querySelector('#task-more-menu');
    if (moreMenu?.open) {
        moreMenu.open = false;
        moreMenu.querySelector('summary').focus();
    }
});

document.addEventListener('change', (event) => {
    const input = event.target;
    const row = input.closest('.task-row, .subtask-row');
    if (!row) return;
    if (input.matches('.due-time')) {
        const picker = input.closest('.due-picker');
        const dueInput = picker.closest('[data-due-picker-wrapper]').querySelector('.due-input');
        picker.dataset.time = input.value;
        if (dueInput.value) saveDueDate(dueInput, `${dueInput.value.slice(0, 10)}T${input.value}`);
    } else if (input.matches('.category-choice')) {
        const selected = [...row.querySelectorAll('.category-choice:checked')].map((item) => item.value);
        updateCategoryChips(row);
        saveField(row, 'categories', selected, input);
    } else if (input.matches('[data-field="due_at"]')) {
        updateDueLabel(row, input.value);
        const reminder = row.querySelector('.reminder-toggle');
        if (reminder) {
            reminder.disabled = !input.value;
            if (!input.value) {
                reminder.setAttribute('aria-pressed', 'false');
                reminder.classList.remove('text-rust');
            }
        }
        saveField(row, 'due_at', input.value, input);
    } else if (input.matches('[data-field="completed_at"]')) {
        saveField(row, 'completed_at', input.value, input);
    } else if (input.matches('.task-complete')) {
        saveField(row, 'completed', String(input.checked), input);
    } else if (input.matches('.priority-select')) {
        const priorityControl = input.closest('.priority-control');
        priorityControl.querySelector('.priority-level').textContent = input.selectedOptions[0].textContent;
        priorityControl.title = `Priority ${input.selectedOptions[0].textContent}`;
        saveField(row, 'priority', input.value, input);
    } else if (input.matches('[data-field="recurrence"]')) {
        const repeatSummary = row.querySelector('.repeat-control summary');
        if (repeatSummary) {
            const repeats = input.value !== 'none';
            repeatSummary.title = repeats ? `Repeats ${input.selectedOptions[0].textContent}` : 'Set repeat interval';
            repeatSummary.classList.toggle('text-forest', repeats);
        }
        saveField(row, 'recurrence', input.value, input);
    } else if (input.matches('.task-notes-input')) {
        saveField(row, 'notes', input.value, input);
    }
});

const undoToast = document.querySelector('#undo-toast');
const undoButton = document.querySelector('#undo-action');
if (undoToast && undoButton) {
    try {
        const pendingUndo = JSON.parse(window.sessionStorage.getItem(undoStorageKey) || 'null');
        window.sessionStorage.removeItem(undoStorageKey);
        if (pendingUndo && pendingUndo.expiresAt > Date.now()) {
            document.querySelector('#undo-message').textContent = `${pendingUndo.message}.`;
            undoToast.classList.remove('hidden');
            undoToast.classList.add('flex');
            undoButton.addEventListener('click', async () => {
                undoButton.disabled = true;
                try {
                    await postForm(pendingUndo.url, {
                        field: pendingUndo.field,
                        value: pendingUndo.value,
                        successor_id: pendingUndo.successorId || '',
                    });
                    window.location.reload();
                } catch (error) {
                    document.querySelector('#undo-message').textContent = error.message;
                    undoButton.disabled = false;
                }
            });
            window.setTimeout(() => undoToast.classList.add('hidden'), pendingUndo.expiresAt - Date.now());
        }
    } catch {}
}

window.lucide?.createIcons();
document.body.addEventListener('htmx:afterSwap', () => window.lucide?.createIcons());