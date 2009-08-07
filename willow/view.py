import pkg_resources
pkg_resources.require('Quixote>=2.6')
pkg_resources.require('pygr-draw>=0.5')

import quixote
from quixote.directory import Directory

import pygr_draw

from jinja2 import Template
from urllib import quote_plus
try:
    import json
except ImportError:
    import simplejson as json

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

class BasicView(Directory):
    _q_exports = ['']

    def __init__(self, db, nlmsa_list, wrappers=None):
        self.db = db
        self.nlmsa_list = nlmsa_list
        self.wrappers = wrappers

    def _q_index(self):
        return 'hello, world'
    
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

        page = """
Interval: {{ ival.id }}[{{ ival.start }}:{{ ival.stop }}]
<p>
{% for i, n in l %}
{{ n }} features in nlmsa #{{ i }}<br>
{% endfor %}
<hr>
Bitmap:
<p>
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
