"""Reviewed bank control geometry shared by discovery and offline replay."""

from interface_ai.vision import Box


def controls(view, state):
    if state in ('search-ready', 'input-entered'):
        label = view.target('member-field')
        return {
            'member-input': Box(label.left + 8, label.top + 57, label.left + 520, label.top + 90),
            'search-button': Box(
                label.left + 535, label.top + 57, label.left + 640, label.top + 90
            ),
        }
    if state == 'member-ready':
        # Matching a label is narrower than its button. Include the button's
        # reviewed padding, but never the neighboring account row.
        label = view.target('savings-button')
        return {
            'savings-button': Box(
                label.left - 12, label.top - 12, label.right + 30, label.bottom + 12
            )
        }
    return {}
