#!/usr/bin/env python

import os
from wsgiref.handlers import CGIHandler

import simplejson
from philologic.app import collocation_results

from philologic.app import WebConfig
from philologic.app import WSGIHandler


def collocation(environ, start_response):
    config = WebConfig(os.path.abspath(os.path.dirname(__file__)).replace('reports', ''))
    request = WSGIHandler(environ, config)
    headers = [('Content-type', 'application/json; charset=UTF-8'), ("Access-Control-Allow-Origin", "*")]
    start_response('200 OK', headers)
    collocation_object = collocation_results(request, config)
    yield simplejson.dumps(collocation_object)


if __name__ == "__main__":
    CGIHandler().run(collocation)
