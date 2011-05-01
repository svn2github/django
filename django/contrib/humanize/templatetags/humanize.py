from django.utils.translation import ungettext, ugettext as _
from django.utils.encoding import force_unicode
from django import template
from django.template import defaultfilters
from datetime import date, datetime
import re

register = template.Library()

def ordinal(value):
    """
    Converts an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any integer.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    t = (_('th'), _('st'), _('nd'), _('rd'), _('th'), _('th'), _('th'), _('th'), _('th'), _('th'))
    if value % 100 in (11, 12, 13): # special case
        return u"%d%s" % (value, t[0])
    return u'%d%s' % (value, t[value % 10])
ordinal.is_safe = True
register.filter(ordinal)

def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    orig = force_unicode(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', orig)
    if orig == new:
        return new
    else:
        return intcomma(new)
intcomma.is_safe = True
register.filter(intcomma)

def intword(value):
    """
    Converts a large integer to a friendly text representation. Works best for
    numbers over 1 million. For example, 1000000 becomes '1.0 million', 1200000
    becomes '1.2 million' and '1200000000' becomes '1.2 billion'.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    if value < 1000000:
        return value
    if value < 1000000000:
        new_value = value / 1000000.0
        return ungettext('%(value).1f million', '%(value).1f million', new_value) % {'value': new_value}
    if value < 1000000000000:
        new_value = value / 1000000000.0
        return ungettext('%(value).1f billion', '%(value).1f billion', new_value) % {'value': new_value}
    if value < 1000000000000000:
        new_value = value / 1000000000000.0
        return ungettext('%(value).1f trillion', '%(value).1f trillion', new_value) % {'value': new_value}
    return value
intword.is_safe = False
register.filter(intword)

def apnumber(value):
    """
    For numbers 1-9, returns the number spelled out. Otherwise, returns the
    number. This follows Associated Press style.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    if not 0 < value < 10:
        return value
    return (_('one'), _('two'), _('three'), _('four'), _('five'), _('six'), _('seven'), _('eight'), _('nine'))[value-1]
apnumber.is_safe = True
register.filter(apnumber)

@register.filter
def naturalday(value, arg=None):
    """
    For date values that are tomorrow, today or yesterday compared to
    present day returns representing string. Otherwise, returns a string
    formatted according to settings.DATE_FORMAT.
    """
    try:
        tzinfo = getattr(value, 'tzinfo', None)
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    today = datetime.now(tzinfo).replace(microsecond=0, second=0, minute=0, hour=0)
    delta = value - today.date()
    if delta.days == 0:
        return _(u'today')
    elif delta.days == 1:
        return _(u'tomorrow')
    elif delta.days == -1:
        return _(u'yesterday')
    return defaultfilters.date(value, arg)

@register.filter
def naturaltime(value, arg=None):
    """
    For date and time values shows how many seconds, minutes or hours ago compared to
    current timestamp returns representing string. Otherwise, returns a string
    formatted according to settings.DATE_FORMAT
    """
    try:
        value = datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)
    except AttributeError:
        return value
    except ValueError:
        return value

    delta = datetime.now() - value
    if delta.days != 0:
        value = date(value.year, value.month, value.day)
        return naturalday(value, arg)
    elif delta.seconds == 0:
        return _(u'now')
    elif delta.seconds < 60:
        return _(u'%s seconds ago' % (delta.seconds))
    elif delta.seconds / 60 < 2:
        return _(r'a minute ago')
    elif delta.seconds / 60 < 60:
        return _(u'%s minutes ago' % (delta.seconds/60))
    elif delta.seconds / 60 / 60 < 2:
        return _(u'an hour ago')
    elif delta.seconds / 60 / 60 < 24:
        return _(u'%s hours ago' % (delta.seconds/60/60))
    return naturalday(value, arg)
