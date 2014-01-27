#!/usr/bin/env python

import sys
sys.path.append('..')
import functions as f
from reports.concordance import fetch_concordance
import os
import re
import unicodedata
from functions.wsgi_handler import wsgi_response
from bibliography import fetch_bibliography as bibliography
from render_template import render_template
from collocation import tokenize, filter
from functions.ObjectFormatter import adjust_bytes, convert_entities
from functions.FragmentParser import strip_tags


end_highlight_match = re.compile(r'.*<span class="highlight">[^<]*?(</span>)')
token_regex = re.compile(r'(\W)', re.U)

left_truncate = re.compile (r"^\w+", re.U)
right_truncate = re.compile("\w+$", re.U)
word_identifier = re.compile("\w", re.U)
highlight_match = re.compile(r'<span class="highlight">[^<]*?</span>')
#token_regex = re.compile(r'[\W\d]+', re.U)

begin_match = re.compile(r'^[^<]*?>')
start_cutoff_match = re.compile(r'^[^ <]+')
end_match = re.compile(r'<[^>]*?\Z')
no_tag = re.compile(r'<[^>]+>')

def concordance_from_collocation(environ,start_response):
    db, dbname, path_components, q = wsgi_response(environ,start_response)
    path = os.getcwd().replace('functions/', '')
    if q['q'] == '':
        return bibliography(f,path, db, dbname,q,environ)
    else:
        hits = db.query(q["q"],q["method"],q["arg"],**q["metadata"])
        colloc_results = fetch_colloc_concordance(hits, path, q, db)
        return render_template(results=colloc_results,db=db,dbname=dbname,q=q,colloc_concordance=colloc_concordance,
                               f=f,path=path, results_per_page=q['results_per_page'],
                               report="concordance_from_collocation",template_name="concordance_from_collocation.mako")
        
def fetch_colloc_concordance(results, path, q, db, filter_words=100):
    within_x_words = q['word_num']
    direction = q['direction']
    collocate = unicodedata.normalize('NFC', q['collocate'].decode('utf-8', 'ignore'))
    collocate_num = q['collocate_num']
    
    ## set up filtering of most frequent 200 terms ##
    filter_list_path = path + '/data/frequencies/word_frequencies'
    filter_words_file = open(filter_list_path)

    line_count = 0
    filter_list = set([])

    for line in filter_words_file:
        line_count += 1
        word = line.split()[0]
        filter_list.add(word.decode('utf-8', 'ignore'))
        if line_count > filter_words:
                break
    
    new_hitlist = []
    for hit in results:
        ## get my chunk of text ##
        bytes, byte_start = adjust_bytes(hit.bytes, 400)
        conc_text = f.get_text(hit, byte_start, 400, path)
        
        ## Isolate left and right concordances
        conc_left = convert_entities(conc_text[:bytes[0]].decode('utf-8', 'ignore'))
        conc_left = begin_match.sub('', conc_left)
        conc_left = start_cutoff_match.sub('', conc_left)
        conc_right = convert_entities(conc_text[bytes[-1]:].decode('utf-8', 'ignore'))
        conc_right = end_match.sub('', conc_right)
        conc_right = left_truncate.sub('', conc_right)
        conc_left = strip_tags(conc_left)
        conc_right = strip_tags(conc_right)
        
        if direction =='left':
            words = tokenize(conc_left, filter_list, within_x_words, direction, db)
        elif direction == 'right':
            words = tokenize(conc_right, filter_list, within_x_words, direction, db)
        else:
            words = tokenize(conc_left, filter_list, within_x_words, 'left', db)
            words.extend(tokenize(conc_right, filter_list, within_x_words, 'right', db))
        if collocate in set(words):
            count = words.count(collocate)
            hit.collocate_num = count
            new_hitlist.append(hit)

        if len(new_hitlist) > (q["start"] + q["results_per_page"]):
            break
    
    h = collocation_hitlist(new_hitlist, collocate_num)
    return h

def colloc_concordance(hit, path, q, db):
    conc_text = fetch_concordance(hit, path, q)
    split_text = token_regex.split(conc_text)
    keep_text = []
    for w in split_text:
        if w:
            if w.lower() == q['collocate'].decode('utf-8', 'ignore'):
                w = '<span class="collocate">%s</span>' % w
            keep_text.append(w)
    conc_text = ''.join(keep_text)
    return conc_text  
    
class collocation_hitlist(object):
    
    def __init__(self, hitlist, collocate_num):
        self.done = True
        self.num = collocate_num
        self.hitlist = hitlist
        
    def __getitem__(self, key):
        return self.hitlist[key]
        
    def __getattr__(self, name):
        return self.hitlist[name]
        
    def __len__(self):
        return int(self.num)
        