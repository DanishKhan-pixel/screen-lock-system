"""Custom template tags and filters for the Aegis pages app."""
from django import template

register = template.Library()


@register.filter(name="severity_icon")
def severity_icon(severity):
    """Return a simple text icon for a severity level."""
    icons = {
        "low": "🔵",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }
    return icons.get(severity, "⚪")


@register.filter(name="status_label")
def status_label(status):
    """Return a human-readable label with an indicator for a report status."""
    labels = {
        "active": "● Active",
        "review": "◐ In Review",
        "closed": "○ Closed",
    }
    return labels.get(status, status)


@register.simple_tag
def severity_css(severity):
    """Return the CSS class to use for a severity badge."""
    css = {
        "low": "severity-low",
        "medium": "severity-medium",
        "high": "severity-high",
        "critical": "severity-critical",
    }
    return css.get(severity, "")


@register.filter(name="initials")
def initials(user):
    """Return avatar initials for a User object."""
    profile = getattr(user, "profile", None)
    if profile:
        return profile.avatar_initials
    name = (user.get_full_name() or user.username).strip()
    parts = name.split()
    return "".join(p[0] for p in parts[:2]).upper() or "?"
