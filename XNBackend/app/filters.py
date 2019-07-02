# -*- encoding: utf-8 -*-
from flask import Flask, url_for


def _callable(obj):
    return callable(obj)


def maybe_none(s, occupier='-'):
    return occupier if s is None else s


def page_href(endpoint, page, per_page, disabled=False):
    return url_for(
        endpoint,
        page=page,
        per_page=per_page
    ) if not disabled else 'javascript:void(0)'


def add_filters(app: Flask):
    app.add_template_filter(_callable, name='callable')
    app.add_template_filter(maybe_none)
    app.add_template_filter(page_href)
