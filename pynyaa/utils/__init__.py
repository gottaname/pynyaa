
import math
import random
import string

from flask import request, url_for, current_app, g
from markupsafe import Markup

from . import torrent


def pretty_size(size):
    if not size:
        return '0 B'
    exp = min(4, int(math.log(size, 1024)))
    suffix = ['B', 'KiB', 'MiB', 'GiB', 'TiB'][exp]
    size = size / 1024**exp
    return f'{size:.1f} {suffix}'


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def cdatasafe(text):
    text = text.replace(']]>', '')
    return Markup(text)


def bootstrap_alert(flash_category):
    return {
        'error': 'danger',
        'message': 'success',
    }.get(flash_category, flash_category)


def random_string(length):
    chars = string.digits + string.ascii_letters
    return ''.join(random.choice(chars) for _ in range(length))


def inject_search_data():
    """before_request hook"""
    map_long_names = dict(
        c='category',
        s='status',
        q='query',
    )
    search = dict(
        category='',
        status='',
        sort='',
        order='',
        max='',
        query='',
    )
    for key in request.args:
        if key in ('c', 'category', 's', 'status', 'sort', 'order', 'max', 'q', 'query'):
            search[map_long_names.get(key, key)] = request.args.get(key)

    if 'max' not in search:
        search['max'] = 50

    try:
        search['max'] = int(search['max'])
    except ValueError:
        search['max'] = 50

    search['max'] = min(300, max(5, search['max']))

    current_app.jinja_env.globals['search'] = search
    g.search = search
