const csrfToken = document.querySelector('#task-csrf [name="csrfmiddlewaretoken"]').value;
const titleTimers = new WeakMap();
const undoStorageKey = 'tasks-pending-undo';
const reopenDetailsStorageKey = 'tasks-reopen-details';

function setStatus(element, message, isError = false) {
    if (!element) return;
    element.textContent = message;
    element.classList.toggle('hidden', !message);
    element.classList.toggle('text-rust', isError);
}

function updateOpenSubtaskBadge(taskRow) {
    const toggle = taskRow.querySelector('.task-details-toggle');
    if (!toggle) return;

    const count = [...taskRow.querySelectorAll('.subtask-row input[data-field="completed"]')]
        .filter((input) => !input.checked).length;
    let badge = toggle.querySelector('.subtask-count-badge');
    if (count > 0) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'subtask-count-badge absolute -right-1 -top-1 min-w-4 rounded-full bg-task-accent px-1 text-center font-mono text-[0.58rem] leading-4 text-accent-ink';
            toggle.append(badge);
        }
        badge.textContent = String(count);
        toggle.setAttribute('aria-label', `Edit notes and steps, ${count} open ${count === 1 ? 'step' : 'steps'}`);
    } else {
        badge?.remove();
        toggle.setAttribute('aria-label', 'Edit notes and steps');
    }
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
        if (['cancelled', 'archived'].includes(field)) {
            if (value === 'true') {
                const actionName = { cancelled: 'cancelled', archived: 'archived' }[field];
                try {
                    window.sessionStorage.setItem(undoStorageKey, JSON.stringify({
                        url: row.dataset.updateUrl,
                        field: field,
                        value: 'false',
                        message: `Task ${actionName}`,
                        expiresAt: Date.now() + 15000,
                    }));
                } catch {}
            }
            window.location.reload();
        } else if (field === 'completed') {
            // Subtask complete: update DOM in place, no reload
            const subtaskRow = input.closest('.subtask-row');
            if (subtaskRow) {
                const title = subtaskRow.querySelector('.subtask-title');
                if (title) title.classList.toggle('line-through', value === 'true');
                if (title) title.classList.toggle('text-ink-muted', value === 'true');
                const parentTask = subtaskRow.closest('.task-row');
                if (parentTask) updateOpenSubtaskBadge(parentTask);
            } else {
                // Task-level complete: set undo + reload
                if (value === 'true') {
                    try {
                        window.sessionStorage.setItem(undoStorageKey, JSON.stringify({
                            url: row.dataset.updateUrl,
                            field: result.next_task_id ? 'undo_completion' : 'completed',
                            value: 'false',
                            successorId: result.next_task_id,
                            message: 'Task completed',
                            expiresAt: Date.now() + 15000,
                        }));
                    } catch {}
                }
                window.location.reload();
            }
        } else if (field === 'delete') {
            // Subtask delete: remove from DOM without full reload
            const subtaskRow = input.closest('.subtask-row');
            if (subtaskRow) {
                const parentTask = subtaskRow.closest('.task-row');
                subtaskRow.remove();
                if (parentTask) {
                    updateOpenSubtaskBadge(parentTask);
                }
                const remaining = parentTask?.querySelectorAll('.subtask-row') || [];
                if (parentTask && remaining.length === 0) {
                    const subtaskList = parentTask.querySelector('[aria-label="Subtasks"]');
                    if (subtaskList) subtaskList.classList.add('hidden');
                }
            } else {
                window.location.reload();
            }
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
            input.classList.toggle('icon-themed', enabled);
            input.classList.toggle('icon-sky', enabled);
        }
    }
}

// ---- Shared quick-capture token helpers (used by BOTH the live highlighter
//      and the form parser, so detection and coloring always agree) ---------
// Token delimiters in the quick-capture field are: space, comma, or `/` (date anchor).
// A "date token" is a single slash-delimited token (no spaces inside); multi-word
// dates must be hyphenated, e.g. /Dec-15 or /next-Mon.

const DATE_BODY = (
    '(?:' +
    'today|tomorrow|weekend' +
    '|(?:next-)?(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day)?' +
    '|next-?(?:week|month|year)' +
    '|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*-\\d{1,2}(?:-\\d{2,4})?' +
    '|\\d{4}-\\d{1,2}-\\d{1,2}' +
    '|\\d{1,2}-\\d{1,2}(?:-\\d{2,4})?' +
    ')'
);
const DATE_TOKEN_PATTERN = '/' + DATE_BODY;
const RECURRENCE_TOKEN_PATTERN = '(?:daily|weekly|monthly|yearly)';
const RECURRENCE_VALUES = { daily: 'daily', weekly: 'weekly', monthly: 'monthly', yearly: 'yearly' };

const WEEKDAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
const MONTH_NAMES = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
const WEEKDAY_PREFIXES = WEEKDAYS.map((w) => w.slice(0, 3));

function getCaptureToday() {
    const el = document.querySelector('#quick-capture-tags');
    if (el && el.dataset.today) {
        const [y, m, d] = el.dataset.today.split('-').map(Number);
        return new Date(Date.UTC(y, m - 1, d));
    }
    return new Date();
}

// `raw` is the text AFTER the leading '/'; it must not contain spaces.
function resolveCaptureDate(raw, today) {
    const text = raw.toLowerCase();
    const year = today.getUTCFullYear();
    const month = today.getUTCMonth();
    const day = today.getUTCDate();
    const at = (y, m, d) => new Date(Date.UTC(y, m, d));

    if (text === 'today') return at(year, month, day);
    if (text === 'tomorrow') return at(year, month, day + 1);
    if (text === 'weekend') return at(year, month, day + ((((5 - today.getUTCDay()) + 7) % 7) || 7));
    if (text === 'next-weekend') return at(year, month, day + 7 + ((((5 - today.getUTCDay()) + 7) % 7) || 7));
    if (text === 'next-week') return at(year, month, day + 7);
    if (text === 'next-month') return at(year, month + 1, 1);
    if (text === 'next-year') return at(year + 1, 1, 1);

    let m = text.match(/^(?:next-)?(mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day)?$/);
    if (m) {
        const isNext = text.startsWith('next-');
        const idx = WEEKDAY_PREFIXES.findIndex((w) => w === m[1].slice(0, 3));
        if (idx !== -1) {
            let offset = (idx - today.getUTCDay() + 7) % 7;
            if (isNext) offset += 7; // next-<weekday> always lands on the same weekday of NEXT week
            return at(year, month, day + offset);
        }
    }

    m = text.match(/^(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*-(\d{1,2})(?:-(\d{2,4}))?$/);
    if (m) {
        const mi = MONTH_NAMES.findIndex((n) => n === m[1].slice(0, 3));
        const y = m[3] ? (parseInt(m[3], 10) < 100 ? parseInt(m[3], 10) + 2000 : parseInt(m[3], 10)) : year;
        return at(y, mi, parseInt(m[2], 10));
    }

    m = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (m) return at(+m[1], +m[2] - 1, +m[3]);

    m = text.match(/^(\d{1,2})-(\d{1,2})(?:-(\d{2,4}))?$/);
    if (m) {
        const y = m[3] ? (parseInt(m[3], 10) < 100 ? parseInt(m[3], 10) + 2000 : parseInt(m[3], 10)) : year;
        return at(y, +m[1] - 1, +m[2]);
    }

    return null;
}

function parseQuickCapture(rawValue) {
    let title = rawValue.trim();
    const categories = [];
    let priority = '';
    let dueAt = '';
    let recurrence = '';

    const today = getCaptureToday();
    const dateRegex = new RegExp(DATE_TOKEN_PATTERN, 'i');
    const dateMatch = title.match(dateRegex);
    if (dateMatch) {
        const raw = dateMatch[0].slice(1);
        const resolved = resolveCaptureDate(raw, today);
        if (resolved) {
            const pad = (part) => String(part).padStart(2, '0');
            dueAt = `${resolved.getUTCFullYear()}-${pad(resolved.getUTCMonth() + 1)}-${pad(resolved.getUTCDate())}T09:00`;
            title = title.replace(dateRegex, ' ');
        }
    }

    const priorityPattern = /(^|\s)p([1-5])(?=$|[\s,])/i;
    const priorityMatch = title.match(priorityPattern);
    if (priorityMatch) {
        priority = String(6 - Number(priorityMatch[2]));
        title = title.replace(priorityPattern, '$1 ');
    }

    const recurrencePattern = new RegExp(`(^|\\s)${RECURRENCE_TOKEN_PATTERN}(?=$|[\\s,])`, 'i');
    const recurrenceMatch = title.match(recurrencePattern);
    if (recurrenceMatch) {
        recurrence = RECURRENCE_VALUES[recurrenceMatch[0].trim().toLowerCase()];
        title = title.replace(recurrencePattern, '$1 ');
    }

    const availableCategories = [...document.querySelectorAll('#quick-capture-tags [data-category-id]')]
        .sort((left, right) => right.dataset.categoryName.length - left.dataset.categoryName.length);
    for (const category of availableCategories) {
        const tagPattern = new RegExp(`(^|\\s)[#@]${category.dataset.categoryName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?=$|[\\s,])`, 'i');
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

    const matches = [];
    const seen = [];
    const collect = (pattern, className) => {
        for (const match of value.matchAll(pattern)) {
            const start = match.index;
            if (seen.some((existing) => start < existing.end && match.index + match[0].length > existing.start)) continue;
            matches.push({ start, end: start + match[0].length, text: match[0], className });
            seen.push({ start, end: start + match[0].length });
        }
    };
    collect(/\bp[1-5]\b/gi, 'capture-token-priority');
    collect(new RegExp(`(^|\\s)${DATE_TOKEN_PATTERN}(?=\\s|,|$)`, 'gi'), 'capture-token-date');
    collect(new RegExp(`(^|\\s)${RECURRENCE_TOKEN_PATTERN}(?=$|[\\s,])`, 'gi'), 'capture-token-repeat');

    const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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

function resizeTaskTitle(title) {
    title.style.height = 'auto';
    title.style.height = `${title.scrollHeight}px`;
}

document.querySelectorAll('.task-title').forEach(resizeTaskTitle);

try {
    const taskId = window.sessionStorage.getItem(reopenDetailsStorageKey);
    window.sessionStorage.removeItem(reopenDetailsStorageKey);
    const row = [...document.querySelectorAll('.task-row')].find((item) => item.dataset.taskId === taskId);
    const panel = row?.querySelector('.task-details-panel');
    const toggle = row?.querySelector('.task-details-toggle');
    if (panel && toggle) {
        panel.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
        toggle.classList.add('icon-themed', 'icon-periwinkle');
    }
} catch {}

function updateCategoryChips(row) {
    const container = row.querySelector('.task-category-chips');
    const chips = [...row.querySelectorAll('.category-choice:checked')].map((choice) => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip inline-flex min-h-7 items-center gap-0.5 rounded-full py-0.5 pl-2.5 pr-0.5 text-xs';
        chip.style.setProperty('--tag-color', choice.dataset.color);
        chip.style.setProperty('--tag-dark-color', choice.dataset.darkColor);

        const name = document.createElement('span');
        name.textContent = choice.dataset.name;

        const remove = document.createElement('button');
        remove.className = 'category-remove inline-grid h-6 w-6 place-items-center rounded-full opacity-65 transition-colors hover:bg-black/10 hover:opacity-100';
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

function updateDatePickerLabel(input) {
    const wrapper = input.closest('[data-date-picker-wrapper]');
    const label = wrapper.querySelector('.date-picker-label');
    const button = wrapper.querySelector('.date-picker-button');
    if (!input.value) {
        label.textContent = wrapper.dataset.emptyLabel;
        if (wrapper.dataset.dueAction === 'true') {
            button.classList.remove('icon-themed', 'icon-mustard');
        }
        return;
    }
    const format = wrapper.dataset.compact === 'true'
        ? { month: 'short', day: 'numeric' }
        : { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' };
    label.textContent = new Intl.DateTimeFormat(undefined, format).format(new Date(input.value));
    if (wrapper.dataset.dueAction === 'true') {
        button.classList.add('icon-themed', 'icon-mustard');
    }
}

function renderDateCalendar(picker) {
    const [year, month] = picker.dataset.month.split('-').map(Number);
    const firstWeekday = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const input = picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-input');
    const selectedDate = input.value.slice(0, 10);
    const monthStart = new Date(year, month - 1, 1);
    const monthLabel = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(monthStart);
    const grid = picker.querySelector('[data-calendar-grid]');
    const pad = (value) => String(value).padStart(2, '0');
    const isoDate = (day) => `${year}-${pad(month)}-${pad(day)}`;
    const today = new Date();
    const todayValue = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;

    picker.querySelector('[data-calendar-month-label]').textContent = monthLabel;
    picker.querySelector('.date-picker-time').value = picker.dataset.time || '09:00';
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

function positionDatePicker(picker, button) {
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

function savePickerDate(input, value) {
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
        try {
            window.sessionStorage.setItem(reopenDetailsStorageKey, form.elements.parent_id.value);
        } catch {}
        window.location.reload();
    } catch (error) {
        setStatus(document.querySelector('#page-status'), error.message, true);
        button.disabled = false;
    }
});

document.addEventListener('input', (event) => {
    const input = event.target;
    if (!input.matches('.task-title, .subtask-title')) return;
    if (input.matches('.task-title')) resizeTaskTitle(input);
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
        detailsToggle.classList.toggle('icon-themed', !panel.hidden);
        detailsToggle.classList.toggle('icon-periwinkle', !panel.hidden);
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
        document.querySelectorAll('.category-add').forEach((item) => {
            item.setAttribute('aria-expanded', 'false');
            item.classList.remove('icon-themed', 'icon-sage');
        });
        menu.hidden = !opening;
        categoryAdd.setAttribute('aria-expanded', String(opening));
        categoryAdd.classList.toggle('icon-themed', opening);
        categoryAdd.classList.toggle('icon-sage', opening);
        return;
    }
    if (event.target.closest('.category-menu')) return;
    document.querySelectorAll('.category-menu').forEach((menu) => { menu.hidden = true; });
    document.querySelectorAll('.category-add').forEach((item) => {
        item.setAttribute('aria-expanded', 'false');
        item.classList.remove('icon-themed', 'icon-sage');
    });

    document.querySelectorAll('.date-time-picker:not([hidden])').forEach((picker) => {
        const wrapper = picker.closest('[data-date-picker-wrapper]');
        if (!wrapper.contains(event.target)) {
            picker.hidden = true;
            wrapper.querySelector('.date-picker-button').setAttribute('aria-expanded', 'false');
        }
    });

    const datePickerButton = event.target.closest('.date-picker-button');
    if (datePickerButton) {
        const wrapper = datePickerButton.closest('[data-date-picker-wrapper]');
        const picker = wrapper.querySelector('.date-time-picker');
        const input = wrapper.querySelector('.date-picker-input');
        const opening = picker.hidden;
        document.querySelectorAll('.date-time-picker').forEach((item) => { item.hidden = true; });
        document.querySelectorAll('.date-picker-button').forEach((item) => item.setAttribute('aria-expanded', 'false'));
        picker.hidden = !opening;
        datePickerButton.setAttribute('aria-expanded', String(opening));
        if (opening) {
            const today = new Date();
            const dateValue = input.value.slice(0, 10) || `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
            picker.dataset.month = dateValue.slice(0, 7);
            picker.dataset.time = input.value.split('T')[1] || '09:00';
            renderDateCalendar(picker);
            positionDatePicker(picker, datePickerButton);
            picker.querySelector('.calendar-day[aria-pressed="true"]')?.focus();
        }
        return;
    }

    const monthButton = event.target.closest('[data-calendar-month]');
    if (monthButton) {
        const picker = monthButton.closest('.date-time-picker');
        const monthStart = new Date(`${picker.dataset.month}-01T00:00:00`);
        monthStart.setMonth(monthStart.getMonth() + Number(monthButton.dataset.calendarMonth));
        picker.dataset.month = `${monthStart.getFullYear()}-${String(monthStart.getMonth() + 1).padStart(2, '0')}`;
        renderDateCalendar(picker);
        return;
    }

    const calendarDay = event.target.closest('.calendar-day');
    if (calendarDay) {
        const picker = calendarDay.closest('.date-time-picker');
        const input = picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-input');
        savePickerDate(input, `${calendarDay.dataset.date}T${picker.dataset.time || '09:00'}`);
        picker.dataset.month = calendarDay.dataset.date.slice(0, 7);
        renderDateCalendar(picker);
        picker.querySelector('.calendar-day[aria-pressed="true"]')?.focus();
        return;
    }

    const todayButton = event.target.closest('.date-picker-today');
    if (todayButton) {
        const picker = todayButton.closest('.date-time-picker');
        const input = picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-input');
        const today = new Date();
        const todayValue = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        savePickerDate(input, `${todayValue}T${picker.dataset.time || '09:00'}`);
        picker.dataset.month = todayValue.slice(0, 7);
        renderDateCalendar(picker);
        picker.querySelector('.calendar-day[aria-pressed="true"]')?.focus();
        return;
    }

    const clearDateButton = event.target.closest('.date-picker-clear');
    if (clearDateButton) {
        const picker = clearDateButton.closest('.date-time-picker');
        const wrapper = picker.closest('[data-date-picker-wrapper]');
        savePickerDate(wrapper.querySelector('.date-picker-input'), '');
        picker.hidden = true;
        const datePickerButton = wrapper.querySelector('.date-picker-button');
        datePickerButton.setAttribute('aria-expanded', 'false');
        datePickerButton.focus();
    }

    const reminderButton = event.target.closest('.reminder-toggle');
    if (reminderButton) {
        const enabled = reminderButton.getAttribute('aria-pressed') !== 'true';
        reminderButton.setAttribute('aria-pressed', String(enabled));
        reminderButton.classList.toggle('icon-themed', enabled);
        reminderButton.classList.toggle('icon-sky', enabled);
        saveField(reminderButton.closest('.task-row'), 'reminder_enabled', String(enabled), reminderButton);
    }
});

window.addEventListener('resize', () => {
    const picker = document.querySelector('.date-time-picker:not([hidden])');
    if (picker) positionDatePicker(picker, picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-button'));
});

window.addEventListener('scroll', () => {
    const picker = document.querySelector('.date-time-picker:not([hidden])');
    if (!picker) return;
    picker.hidden = true;
    picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-button').setAttribute('aria-expanded', 'false');
}, true);

document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const picker = document.querySelector('.date-time-picker:not([hidden])');
    if (picker) {
        picker.hidden = true;
        picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-button').focus();
        picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-button').setAttribute('aria-expanded', 'false');
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
    if (input.matches('.date-picker-time')) {
        const picker = input.closest('.date-time-picker');
        const dateInput = picker.closest('[data-date-picker-wrapper]').querySelector('.date-picker-input');
        picker.dataset.time = input.value;
        if (dateInput.value) savePickerDate(dateInput, `${dateInput.value.slice(0, 10)}T${input.value}`);
    } else if (input.matches('.category-choice')) {
        const selected = [...row.querySelectorAll('.category-choice:checked')].map((item) => item.value);
        updateCategoryChips(row);
        saveField(row, 'categories', selected, input);
    } else if (input.matches('.date-picker-input')) {
        const field = input.dataset.field;
        updateDatePickerLabel(input);
        if (field === 'due_at') {
            const reminder = row.querySelector('.reminder-toggle');
            if (reminder) {
                reminder.disabled = !input.value;
                if (!input.value) {
                    reminder.setAttribute('aria-pressed', 'false');
                    reminder.classList.remove('icon-themed', 'icon-sky');
                }
            }
        }
        saveField(row, field, input.value, input);
    } else if (input.matches('.task-complete')) {
        saveField(row, 'completed', String(input.checked), input);
    } else if (input.matches('.priority-select')) {
        const priorityControl = input.closest('.priority-control');
        const selectedOption = input.selectedOptions[0];
        const priorityLevel = priorityControl.querySelector('.priority-level');
        if (priorityLevel) priorityLevel.textContent = selectedOption.textContent;
        priorityControl.title = `Priority ${input.selectedOptions[0].textContent}`;
        const icon = priorityControl.querySelector('svg') || priorityControl.querySelector('i');
        if (icon) {
            const replacement = document.createElement('i');
            replacement.dataset.lucide = selectedOption.dataset.icon;
            replacement.className = 'priority-icon';
            replacement.setAttribute('aria-hidden', 'true');
            icon.replaceWith(replacement);
            priorityControl.style.setProperty('--priority-light-color', selectedOption.dataset.lightColor);
            priorityControl.style.setProperty('--priority-dark-color', selectedOption.dataset.darkColor);
            window.lucide?.createIcons();
        }
        saveField(row, 'priority', input.value, input);
    } else if (input.matches('[data-field="recurrence"]')) {
        const repeatSummary = row.querySelector('.repeat-control summary');
        if (repeatSummary) {
            const repeats = input.value !== 'none';
            repeatSummary.title = repeats ? `Repeats ${input.selectedOptions[0].textContent}` : 'Set repeat interval';
            repeatSummary.classList.toggle('icon-themed', repeats);
            repeatSummary.classList.toggle('icon-mint', repeats);
        }
        saveField(row, 'recurrence', input.value, input);
    } else if (input.matches('.task-notes-input')) {
        resizeTaskTitle(input);
        saveField(row, 'notes', input.value, input);
    } else if (input.matches('.subtask-title')) {
        resizeTaskTitle(input);
        saveField(row, 'title', input.value, input);
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

// Auto-size detail textareas before registering the HTMX state handlers below.
document.querySelectorAll('.subtask-title, .task-notes-input').forEach(resizeTaskTitle);

// Preserve "Sort and Filter" open state across HTMX swaps
document.body.addEventListener('htmx:beforeRequest', (e) => {
    const filter = document.querySelector('#sort-filter-panel');
    if (filter && filter.open) {
        window.sessionStorage.setItem('tasks-filter-open', '1');
    }
});
document.body.addEventListener('htmx:afterSwap', () => {
    if (window.sessionStorage.getItem('tasks-filter-open') === '1') {
        const filter = document.querySelector('#sort-filter-panel');
        if (filter) filter.open = true;
        window.sessionStorage.removeItem('tasks-filter-open');
    }
});