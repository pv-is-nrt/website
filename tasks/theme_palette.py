from colorsys import hls_to_rgb, rgb_to_hls


DEFAULT_THEME_SEED = '#a9d85d'

_LIGHT_BASE = {
    'ink': '#17241d',
    'ink-muted': '#637168',
    'ink-faint': '#91a096',
    'rust': '#d65b42',
    'paper': '#f0f3ed',
    'paper-line': '#d5ded5',
    'paper-faint': '#e4eae2',
    'surface': '#ffffff',
}
_DARK_BASE = {
    'ink': '#e5eee7',
    'ink-muted': '#a4b2a8',
    'ink-faint': '#77877c',
    'rust': '#f08a73',
    'paper': '#141c17',
    'paper-line': '#35443a',
    'paper-faint': '#222e26',
    'surface': '#1d2821',
}


def _rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _hex(value):
    return '#{:02x}{:02x}{:02x}'.format(*value)


def _mix(seed, base, amount):
    seed_rgb = _rgb(seed)
    base_rgb = _rgb(base)
    return _hex(tuple(round(seed_channel * amount + base_channel * (1 - amount))
                      for seed_channel, base_channel in zip(seed_rgb, base_rgb)))


def _luminance(value):
    channels = [channel / 255 for channel in _rgb(value)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
              for channel in channels]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))


def _contrast(first, second):
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _text_for(background):
    dark_text = '#17241d'
    light_text = '#ffffff'
    return max((dark_text, light_text), key=lambda color: _contrast(color, background))


def _tone_for_contrast(seed, background, minimum, prefer_light, hue_shift=0):
    red, green, blue = (channel / 255 for channel in _rgb(seed))
    hue, lightness, saturation = rgb_to_hls(red, green, blue)
    hue = (hue + hue_shift / 360) % 1
    if hue_shift:
        saturation = max(saturation, 0.48)
    candidates = []
    for step in range(101):
        candidate_lightness = step / 100
        if prefer_light and candidate_lightness < lightness:
            continue
        if not prefer_light and candidate_lightness > lightness:
            continue
        channels = hls_to_rgb(hue, candidate_lightness, saturation)
        candidate = _hex(tuple(round(channel * 255) for channel in channels))
        if _contrast(candidate, background) >= minimum:
            candidates.append(candidate)
    if not candidates:
        for step in range(101):
            channels = hls_to_rgb(hue, step / 100, saturation)
            candidate = _hex(tuple(round(channel * 255) for channel in channels))
            if _contrast(candidate, background) >= minimum:
                candidates.append(candidate)
    return min(candidates, key=lambda color: abs(rgb_to_hls(*(channel / 255 for channel in _rgb(color)))[1] - lightness))


def _surface_tone(seed, base, light_surface=False):
    hue, _, seed_saturation = rgb_to_hls(*(channel / 255 for channel in _rgb(seed)))
    if seed_saturation < 0.08:
        return base
    _, lightness, _ = rgb_to_hls(*(channel / 255 for channel in _rgb(base)))
    if light_surface:
        lightness = 0.965
    saturation = min(max(seed_saturation * 0.65, 0.22), 0.36)
    channels = hls_to_rgb(hue, lightness, saturation)
    return _hex(tuple(round(channel * 255) for channel in channels))


def _build_mode(seed, dark):
    base = _DARK_BASE if dark else _LIGHT_BASE
    paper = _surface_tone(seed, base['paper'])
    surface = _surface_tone(seed, base['surface'], light_surface=not dark)
    accent = _tone_for_contrast(seed, paper, 3, True) if dark else seed
    forest = _tone_for_contrast(seed, paper, 4.5, dark)
    seed_rgb = _rgb(seed)

    return {
        'ink': _mix(seed, base['ink'], 0.015),
        'ink-muted': _mix(seed, base['ink-muted'], 0.025),
        'ink-faint': _mix(seed, base['ink-faint'], 0.02),
        'rust': base['rust'],
        'chartreuse': accent,
        'accent-ink': _text_for(accent),
        'forest': forest,
        'forest-ink': _text_for(forest),
        'capture-tag': _tone_for_contrast(seed, paper, 4.5, dark, 38),
        'capture-repeat': _tone_for_contrast(seed, paper, 4.5, dark, 172),
        'paper': paper,
        'paper-line': _mix(seed, base['paper-line'], 0.20),
        'paper-faint': _surface_tone(seed, base['paper-faint']),
        'surface': surface,
        'page-grid-line': 'rgba({}, {}, {}, 0.045)'.format(*seed_rgb),
        'calendar-selected-text': _text_for(accent),
    }


def build_theme_palette(seed):
    seed = seed.lower()
    return {
        **{'light-' + name: value for name, value in _build_mode(seed, False).items()},
        **{'dark-' + name: value for name, value in _build_mode(seed, True).items()},
    }