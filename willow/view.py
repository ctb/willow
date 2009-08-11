import pkg_resources
pkg_resources.require('Quixote>=2.6')
pkg_resources.require('pygr-draw>=0.5')

import quixote
from quixote.directory import Directory

import pygr_draw

import os.path

import jinja2
from jinja2 import Template
from urllib import quote_plus
try:
    import json
except ImportError:
    import simplejson as json
    
from formencode import htmlfill

###

from . import bookmarks, db

###

def jinja_render(page, d):
    return Template(page).render(d).encode('latin-1', 'replace')

def parse_interval_string(db, s):
    seqname, coords = s.split(':')

    is_rc = coords.startswith('-')
    coords = coords.lstrip('-')
    
    start, stop = coords.split('-')
    start, stop = int(start), int(stop)

    ival = db[seqname][start:stop]
    if is_rc:
        ival = -ival
    return ival

###

class BasicView(Directory):
    _q_exports = ['', 'add_bookmark', 'go']

    def __init__(self, genome_name, db, nlmsa_list, wrappers=None):
        self.genome_name = genome_name
        self.db = db
        self.nlmsa_list = nlmsa_list
        self.wrappers = wrappers

    def _q_index(self):
        session = db.get_session()
        genome_name = self.genome_name
        bookmark_l = bookmarks.get_all(session, self.genome_name)

        thisdir = os.path.dirname(__file__)
        templatesdir = os.path.join(thisdir, 'templates')
        templatesdir = os.path.abspath(templatesdir)
        
        loader = jinja2.FileSystemLoader(templatesdir)
        env = jinja2.Environment(loader=loader)
        template = env.get_template('BasicView/index.html')

        return template.render(locals())

    def add_bookmark(self):
        request = quixote.get_request()
        response = quixote.get_response()
        form = request.form

        sequence = form.get('sequence')
        start = int(form.get('start'))
        stop = int(form.get('stop'))
        
        name = form.get('name', '')
        if not name:
            form = """
<form method='POST'>
Bookmark name: <input type='text' name='name'>
<p>
Sequence: <input type='text' name='sequence'>
Start: <input type='text' name='start'>
Stop: <input type='text' name='stop'>
<p>
<input type='submit' value='save'>
</form>
"""
            form = htmlfill.render(form, defaults=locals())
            page = "{{ form }}"
            return jinja_render(page, locals())

        ###

        bookmarks.add_bookmark(name, self.genome_name, sequence, start, stop,
                               +1)

        url = request.get_url(1)
        url += '/go?sequence=%s&start=%d&stop=%d' % (quote_plus(sequence),
                                                    start, stop)
        return response.redirect(url)

    def go(self):
        request = quixote.get_request()
        form = request.form
        sequence = form.get('sequence')
        start = int(form.get('start'))
        stop = int(form.get('stop'))

        response = quixote.get_response()

        url = request.get_url(1)
        url += '/%s:%s-%s/' % (quote_plus(sequence), start, stop)
        return response.redirect(url)
    
    def _q_lookup(self, component):
        interval = parse_interval_string(self.db, component)
        return IntervalView(interval, self.nlmsa_list, self.wrappers)

class IntervalView(Directory):
    _q_exports = ['', 'png', 'json']

    def __init__(self, interval, nlmsa_list, wrappers):
        self.interval = interval
        self.nlmsa_list = nlmsa_list
        self.wrappers = wrappers

    def _q_index(self):
        ival = self.interval
        l = [ (i, len(nlmsa[ival])) for (i, nlmsa) in enumerate(self.nlmsa_list) ]

        qp = quote_plus
        page = """
<a href='../'>Return to index</a>
<p>        
Interval: {{ ival.id }}[{{ ival.start }}:{{ ival.stop }}]
<a href='../add_bookmark?sequence={{ qp(ival.id) }}&start={{ ival.start }}&stop={{ ival.stop }}'>(bookmark)</a>
<p>
{% for i, n in l %}
{{ n }} features in nlmsa #{{ i }}<br>
{% endfor %}
<hr>
<image src='./png'>
"""
        return jinja_render(page, locals())

    def png(self):
        """
        Draw & return a png for the given interval / NLMSAs.
        """
        picture_class = pygr_draw.BitmapSequencePicture
        pic = pygr_draw.draw_annotation_maps(self.interval,
                                             self.nlmsa_list,
                                             picture_class=picture_class,
                                             wrappers=self.wrappers)
        image = pic.finalize()
        
        response = quixote.get_response()
        response.set_content_type('image/png')
        return image

    def json(self):
        """
        Return coordinates for blobs in JSON format.
        """
        picture_class = pygr_draw.PythonList
        pic = pygr_draw.draw_annotation_maps(self.interval,
                                             self.nlmsa_list,
                                             picture_class=picture_class,
                                             wrappers=self.wrappers)
        l = pic.finalize()
        return json.dumps(l)
