from django import template

register = template.Library()

@register.filter
def ui_avatar(user, size=80):
    """
    Generate UI Avatar URL using first_name initial.
    Always returns a safe string.
    """
    try:
        if not user or not hasattr(user, "first_name") or not user.first_name:
            initial = "U"
        else:
            initial = user.first_name[0].upper()

        return f"https://ui-avatars.com/api/?name={initial}&size={size}&background=blue"
    except Exception:
        # fallback if something goes wrong
        return f"https://ui-avatars.com/api/?name=U&size={size}&background=blue"

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})