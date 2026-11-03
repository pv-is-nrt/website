const preferencesFormToken = document.querySelector('#new-category-form [name="csrfmiddlewaretoken"]').value;
const wideColorPalette = window.matchMedia('(min-width: 900px)');

function syncColorPalette(row) {
    const panel = row.querySelector('.category-colors');
    const toggle = row.querySelector('.color-picker-toggle');
    panel.hidden = !wideColorPalette.matches;
    toggle.hidden = wideColorPalette.matches;
    toggle.setAttribute('aria-expanded', 'false');
}

function syncColorPalettes() {
    document.querySelectorAll('.managed-category').forEach(syncColorPalette);
}

syncColorPalettes();
wideColorPalette.addEventListener('change', syncColorPalettes);

function preferenceStatus(message, isError = false) {
    const status = document.querySelector('#page-status');
    status.textContent = message;
    status.classList.toggle('hidden', !message);
    status.classList.toggle('text-rust', isError);
}

function setThemePalette(palette) {
    Object.entries(palette).forEach(([name, value]) => {
        document.documentElement.style.setProperty(`--tasks-${name}`, value);
    });
}

function setThemeSeed(seed) {
    document.querySelector('#new-theme-color-picker').value = seed;
    document.querySelector('#new-theme-color-hex').value = seed;
}

function setColorSelected(option, selected) {
    const swatch = option.querySelector('.color-swatch');
    ['ring-2', 'ring-offset-2', 'ring-offset-paper', 'ring-forest'].forEach((name) => {
        swatch.classList.toggle(name, selected);
    });
    option.setAttribute('aria-checked', String(selected));
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
    row.querySelector('.delete-category').setAttribute('aria-label', `Delete tag ${category.name}`);
    const colorPicker = row.querySelector('.color-picker-toggle');
    colorPicker.style.setProperty('--swatch-color', category.color);
    row.querySelectorAll('.color-option').forEach((option) => {
        setColorSelected(option, option.dataset.color === category.color);
        if (option.dataset.color === category.color) {
            colorPicker.setAttribute('aria-label', `Choose tag color, ${option.getAttribute('aria-label')}`);
        }
    });
    syncColorPalette(row);
    return row;
}

document.querySelectorAll('.preference-control').forEach((control) => control.addEventListener('change', async (event) => {
    const input = event.currentTarget;
    try {
        const result = await preferencePost(input.dataset.saveUrl, {
            [input.name]: input.type === 'checkbox' ? String(input.checked) : input.value,
        });
        if (input.name === 'theme') document.documentElement.dataset.theme = input.value;
        if (input.name === 'background_pattern') document.body.dataset.pattern = input.value;
        if (input.name === 'active_theme') {
            setThemePalette(result.palette);
            setThemeSeed(result.seed_color);
            document.querySelector('#delete-custom-theme').disabled = !input.value;
        }
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
}));

document.querySelectorAll('[data-hex-target]').forEach((picker) => picker.addEventListener('input', () => {
    document.getElementById(picker.dataset.hexTarget).value = picker.value;
}));

document.querySelectorAll('.color-hex').forEach((input) => {
    input.addEventListener('input', () => {
        if (input.checkValidity()) {
            document.getElementById(input.id.replace('-hex', '-picker')).value = input.value.toLowerCase();
        }
    });
    input.addEventListener('change', () => {
        if (!input.checkValidity()) {
            input.reportValidity();
            return;
        }
        const picker = document.getElementById(input.id.replace('-hex', '-picker'));
        picker.value = input.value.toLowerCase();
        picker.dispatchEvent(new Event('change', { bubbles: true }));
    });
});

document.querySelector('#new-theme-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const name = form.elements.name.value.trim();
    const color = form.elements.color.value.trim();
    form.elements.name.setCustomValidity(!name ? 'Enter a theme name.' : name.length > 40 ? 'Use 40 characters or fewer.' : '');
    if (!name || name.length > 40 || !/^#[0-9a-f]{6}$/i.test(color)) {
        form.reportValidity();
        return;
    }
    try {
        const result = await preferencePost(form.action, { name, color });
        const select = document.querySelector('#active-custom-theme');
        const option = new Option(result.theme.name, String(result.theme.id));
        option.dataset.deleteUrl = result.theme.delete_url;
        option.dataset.seedColor = result.theme.seed_color;
        select.append(option);
        select.value = String(result.theme.id);
        document.querySelector('#delete-custom-theme').disabled = false;
        setThemePalette(result.palette);
        setThemeSeed(result.seed_color);
        form.elements.name.value = '';
        preferenceStatus('Theme saved.');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

document.querySelector('#delete-custom-theme').addEventListener('click', async () => {
    const select = document.querySelector('#active-custom-theme');
    const option = select.selectedOptions[0];
    if (!select.value || !option.dataset.deleteUrl) return;
    try {
        const result = await preferencePost(option.dataset.deleteUrl, {});
        option.remove();
        select.value = '';
        document.querySelector('#delete-custom-theme').disabled = true;
        if (result.was_active) {
            setThemePalette(result.palette);
            setThemeSeed(result.seed_color);
        }
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
        row.querySelector('.delete-category').setAttribute('aria-label', `Delete tag ${category.name}`);
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

document.querySelector('#category-list').addEventListener('click', async (event) => {
    const pickerToggle = event.target.closest('.color-picker-toggle');
    if (pickerToggle) {
        const panel = pickerToggle.nextElementSibling;
        const opening = panel.hidden;
        document.querySelectorAll('.category-colors').forEach((item) => { item.hidden = true; });
        document.querySelectorAll('.color-picker-toggle').forEach((item) => item.setAttribute('aria-expanded', 'false'));
        panel.hidden = !opening;
        pickerToggle.setAttribute('aria-expanded', String(opening));
        return;
    }

    const colorOption = event.target.closest('.color-option');
    if (colorOption) {
        const row = colorOption.closest('.managed-category');
        try {
            await preferencePost(row.dataset.updateUrl, { color: colorOption.dataset.color });
            row.querySelectorAll('.color-option').forEach((option) => {
                setColorSelected(option, option === colorOption);
            });
            const pickerToggle = row.querySelector('.color-picker-toggle');
            pickerToggle.style.setProperty('--swatch-color', colorOption.dataset.color);
            pickerToggle.setAttribute('aria-label', `Choose tag color, ${colorOption.getAttribute('aria-label')}`);
            pickerToggle.setAttribute('aria-expanded', 'false');
            row.querySelector('.category-colors').hidden = !wideColorPalette.matches;
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
            empty.className = 'm-0 px-1 py-4 text-sm text-ink-muted';
            empty.id = 'empty-categories';
            empty.textContent = 'No tags yet.';
            document.querySelector('#category-list').append(empty);
        }
        preferenceStatus('');
    } catch (error) {
        preferenceStatus(error.message, true);
    }
});

window.lucide?.createIcons();