"""Template jinja filters."""

from datetime import datetime
import json as json_lib
import random
import re
import jinja2
import markdown
from babel import dates as babel_dates
from babel import numbers as babel_numbers
from grow.common import json_encoder
from grow.pods import urls
from grow.templates.tags import _gettext_alias

SLUG_REGEX = re.compile(r'[^A-Za-z0-9-._~]+')


def _deep_gettext(ctx, fields):
    if isinstance(fields, dict):
        new_dct = {}
        for key, val in fields.iteritems():
            if isinstance(val, (dict, list, set)):
                new_dct[key] = _deep_gettext(ctx, val)
            elif isinstance(val, basestring):
                new_dct[key] = _gettext_alias(ctx, val)
            else:
                new_dct[key] = val
        return new_dct
    elif isinstance(fields, (list, set)):
        for i, val in enumerate(fields):
            if isinstance(val, (dict, list, set)):
                fields[i] = _deep_gettext(ctx, val)
            elif isinstance(val, basestring):
                fields[i] = _gettext_alias(ctx, val)
            else:
                fields[i] = val
    return fields


@jinja2.contextfilter
def deeptrans(ctx, obj):
    """Deep translate an object."""
    return _deep_gettext(ctx, obj)


@jinja2.contextfilter
def jsonify(_ctx, obj, *args, **kwargs):
    """Filter for JSON dumping an object."""
    return json_lib.dumps(obj, cls=json_encoder.GrowJSONEncoder, *args, **kwargs)


def markdown_filter(value):
    """Filters content through a markdown processor."""
    try:
        if isinstance(value, unicode):
            value = value.decode('utf-8')
        value = value or ''
        return markdown.markdown(value)
    except UnicodeEncodeError:
        return markdown.markdown(value)


@jinja2.contextfilter
def parsedatetime_filter(_ctx, date_string, string_format):
    """Filter dor parsing a datetime."""
    return datetime.strptime(date_string, string_format)


@jinja2.contextfilter
def relative_filter(ctx, path):
    """Calculates the relative path from the current url to the given url."""
    doc = ctx['doc']
    return urls.Url.create_relative_path(
        path, relative_to=doc.url.path)


@jinja2.contextfilter
def render_filter(ctx, template):
    """Creates jinja template from string and renders."""
    if isinstance(template, basestring):
        template = ctx.environment.from_string(template)
    return template.render(ctx)


@jinja2.contextfilter
def shuffle_filter(_ctx, seq):
    """Shuffles the list into a random order."""
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except TypeError:
        return seq


def slug_filter(value):
    """Filters string to remove url unfriendly characters."""
    return unicode(u'-'.join(SLUG_REGEX.split(value.lower())).strip(u'-'))


def wrap_locale_context(func):
    """Wraps the func with the current locale."""
    @jinja2.contextfilter
    def _locale_filter(ctx, value, *args, **kwargs):
        doc = ctx['doc']
        if not kwargs.get('locale', None):
            kwargs['locale'] = str(doc.locale)
        return func(value, *args, **kwargs)
    return _locale_filter


def create_builtin_filters():
    """Filters standard for the template rendering."""
    return (
        ('currency', wrap_locale_context(babel_numbers.format_currency)),
        ('date', wrap_locale_context(babel_dates.format_date)),
        ('datetime', wrap_locale_context(babel_dates.format_datetime)),
        ('decimal', wrap_locale_context(babel_numbers.format_decimal)),
        ('deeptrans', deeptrans),
        ('jsonify', jsonify),
        ('markdown', markdown_filter),
        ('number', wrap_locale_context(babel_numbers.format_number)),
        ('percent', wrap_locale_context(babel_numbers.format_percent)),
        ('relative', relative_filter),
        ('render', render_filter),
        ('shuffle', shuffle_filter),
        ('slug', slug_filter),
        ('time', wrap_locale_context(babel_dates.format_time)),
    )
