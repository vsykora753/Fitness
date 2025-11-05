from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css):
    """
    Přidá CSS třídu ke widgetu pole ve formuláři: {{ field|add_class:"form-control" }}
    Bezpečně sloučí existující class s novou.
    """
    attrs = field.field.widget.attrs.copy()
    existing = attrs.get('class', '')
    if existing:
        attrs['class'] = f"{existing} {css}"
    else:
        attrs['class'] = css
    return field.as_widget(attrs=attrs)
