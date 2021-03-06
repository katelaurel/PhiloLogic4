#!/usr/bin/env python

import os
from wsgiref.handlers import CGIHandler

import simplejson
from philologic.DB import DB
from philologic.Query import split_terms
from philologic.QuerySyntax import group_terms, parse_query

from philologic.app import WebConfig
from philologic.app import WSGIHandler


def term_group(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'application/json; charset=UTF-8'),
               ("Access-Control-Allow-Origin", "*")]
    start_response(status, headers)
    config = WebConfig(os.path.abspath(os.path.dirname(__file__)).replace('scripts', ''))
    db = DB(config.db_path + '/data/')
    request = WSGIHandler(environ, config)
    hits = db.query(request["q"], request["method"], request["arg"],
                    **request.metadata)
    parsed = parse_query(request.q)
    group = group_terms(parsed)
    all_groups = split_terms(group)
    term_groups = []
    for g in all_groups:
        term_group = ''
        not_started = False
        for kind, term in g:
            if kind == 'NOT':
                if not_started is False:
                    not_started = True
                    term_group += ' NOT '
            elif kind == 'OR':
                term_group += '|'
            elif kind == "TERM":
                term_group += ' %s ' % term
            elif kind == "QUOTE":
                term_group += ' %s ' % term
        term_group = term_group.strip()
        term_groups.append(term_group)
    yield simplejson.dumps(term_groups)


if __name__ == "__main__":
    CGIHandler().run(term_group)
