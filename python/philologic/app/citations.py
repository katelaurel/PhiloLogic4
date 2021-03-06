#!/usr/bin/env python

from link import *


def citation_links(db, config, i):
    """ Returns a representation of a PhiloLogic object and all its ancestors
        suitable for a precise concordance citation. """
    doc_href = make_absolute_object_link(config, i.philo_id[:1]) + '/table-of-contents'
    div1_href = make_absolute_object_link(config, i.philo_id[:2], i.bytes)
    div2_href = make_absolute_object_link(config, i.philo_id[:3], i.bytes)
    div3_href = make_absolute_object_link(config, i.philo_id[:4], i.bytes)
    page_href = make_absolute_object_link(config, i.page.philo_id, i.bytes)

    links = {"doc": doc_href, "div1": div1_href, "div2": div2_href, "div3": div3_href, "page": page_href}

    try:
        speaker_name = i.para.who
        if speaker_name:
            links['para'] = make_absolute_object_link(config, i.philo_id[:5], i.bytes)
    except AttributeError:
        links["para"] = ""
    return links


def citations(hit, citation_hrefs, config, report="concordance"):
    """ Returns a representation of a PhiloLogic object and all its ancestors
        suitable for a precise citation. """

    citation_type = config[report + "_citation"]
    citation = []

    for pos, citation_object in enumerate(citation_type):
        cite = {}
        cite["label"] = hit[citation_object["field"]].strip()
        if cite["label"]:
            if report != "concordance" and pos != 0:
                cite["separator"] = True
            else:
                cite["separator"] = False
            if citation_object["link"]:
                if citation_object["field"] == "title" or citation_object["field"] == "filename":
                    cite["href"] = citation_hrefs['doc']
                else:
                    params = [("report", "bibliography"), (citation_object["field"], '"%s"' % hit[citation_object["field"]])]
                    cite["href"] = make_absolute_query_link(config, params)
            else:
                cite["href"] = None
            if citation_object["style"] == "normal":
                cite["style"] = None
            else:
                style_list = [i.strip() for i in citation_object["style"].split(',') if i and i != "normal"]
                cite["style"] = {}
                for style in style_list:
                    if style == "brackets":
                        cite["label"] = "[%s]" % cite["label"]
                    elif style == "italic":
                        cite["style"]["font-style"] = "italic"
                    elif style == "bold":
                        cite["style"]["font-weight"] = 700
                    elif style == "small-caps":
                        cite["style"]["font-variant"] = "small-caps"
            citation.append(cite)

    if report == "concordance":
        # We want to display div, para and page metadata as well
        div1_name = hit.div1.head
        if not div1_name:
            if hit.div1.philo_name == "__philo_virtual":
                div1_name = "Section"
            else:
                if hit.div1["type"] and hit.div1["n"]:
                    div1_name = hit.div1['type'] + " " + hit.div1["n"]
                else:
                    div1_name = hit.div1["head"] or hit.div1['type'] or hit.div1['philo_name'] or hit.div1['philo_type']
        div1_name = div1_name[0].upper() + div1_name[1:]

        # Remove leading/trailing spaces
        div1_name = div1_name.strip()
        div2_name = hit.div2.head.strip()
        div3_name = hit.div3.head.strip()
        if div3_name == div2_name and hit.div3.philo_id[-1] == 0:
            div3_name = ''
        if div2_name == div1_name and hit.div2.philo_id[-1] == 0:
            div2_name = ''
        if div1_name:
            citation.append({"href": citation_hrefs['div1'], "label": div1_name, "style": None, "separator": True})
        if div2_name:
            citation.append({"href": citation_hrefs['div2'], "label": div2_name, "style": None, "separator": True})
        if div3_name:
            citation.append({"href": citation_hrefs['div3'], "label": div3_name, "style": None, "separator": True})

        # Paragraph level metadata
        if "para" in citation_hrefs:
            try:
                citation.append({"href": citation_hrefs['para'], "label": hit.who.strip(), "style": None, "separator": True})
            except KeyError:  ## no who keyword
                pass

        # Page level metadata
        page_obj = hit.page
        if page_obj['n']:
            page_n = "page %s" % str(page_obj['n'])
            if page_n:
                citation.append({"href": citation_hrefs["page"], "label": page_n, "style": None, "separator": True})

    return citation
