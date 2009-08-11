import os.path
from urllib import quote_plus

import pkg_resources
pkg_resources.require('Quixote>=2.6')
pkg_resources.require('pygr-draw>=0.5')

import quixote
from quixote.directory import Directory

import pygr_draw

try:
    import json
except ImportError:
    import simplejson as json
    
###

from . import bookmarks, db, blast_view

###

from .web_util import env, templatesdir

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
    _q_exports = ['', 'add_bookmark', 'go', 'css', 'blast']

    def __init__(self, genome_name, db, nlmsa_list, wrappers=None):
        self.genome_name = genome_name
        self.db = db
        self.nlmsa_list = nlmsa_list
        self.wrappers = wrappers

        self.blast = blast_view.BlastView(genome_name, db)

    def css(self):
        cssfile = os.path.join(templatesdir, 'thin_green_line.css')
        
        response = quixote.get_response()
        response.set_content_type('text/css')
        return open(cssfile).read()

    def _q_index(self):
        session = db.get_session()
        genome_name = self.genome_name
        bookmark_l = bookmarks.get_all(session, self.genome_name)

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
            template = env.get_template('BasicView/add_bookmark.html')
            return template.render(locals())

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
        try:
            interval = parse_interval_string(self.db, component)
        except ValueError:
            return "no such page"
        
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
        template = env.get_template('InternalView/index.html')
        return template.render(locals())

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
