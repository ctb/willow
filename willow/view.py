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
from .bookmarks import Bookmark
from pygr import annotation, cnestedlist, nlmsa_utils
from pygr_draw.annotation import FeatureWrapperFactory

def bookmarks_to_nlmsa(bookmarks_l, genome_db):
    d = dict([ (b.name, b) for b in bookmarks_l ])
    annodb = annotation.AnnotationDB(d, genome_db, annotationType='mark:',
                                     sliceAttrDict=dict(id='sequence',
                                                        start='start',
                                                        stop='stop',
                                                        orientation='orientation'))

    al = cnestedlist.NLMSA('foo', mode='memory', pairwiseMode=True)
    for k in annodb:
        al.addAnnotation(annodb[k])

    try:
        al.build()
    except nlmsa_utils.EmptyAlignmentError:
        al = None

    return al

class BookmarkWrapperFactory(FeatureWrapperFactory):
    def __call__(self, feature):
        d = dict(self.values)
        d['name'] = 'b:' + feature.name
        return self.klass(self, feature, d)
    
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
    _q_exports = ['', 'add_bookmark', 'go', 'css', 'blast', 'delete_bookmark']

    def __init__(self, genome_name, genome_db, nlmsa_list, wrappers=None):
        self.genome_name = genome_name
        self.genome_db = genome_db
        self.nlmsa_list = nlmsa_list
        self.wrappers = wrappers

        self.blast = blast_view.BlastView(genome_name, genome_db)
        self.session = db.get_session()

        self._load_bookmarks()

    def _load_bookmarks(self):
        self.bookmarks_l = bookmarks.get_all(self.session, self.genome_name)
        self.bookmarks_al = bookmarks_to_nlmsa(self.bookmarks_l, self.genome_db)

    def css(self):
        cssfile = os.path.join(templatesdir, 'thin_green_line.css')
        
        response = quixote.get_response()
        response.set_content_type('text/css')
        return open(cssfile).read()

    def _q_index(self):
        genome_name = self.genome_name
        bookmarks_l = self.bookmarks_l

        template = env.get_template('BasicView/index.html')

        return template.render(locals())

    def add_bookmark(self):
        request = quixote.get_request()
        response = quixote.get_response()
        form = request.form

        sequence = form.get('sequence')
        start = int(form.get('start'))
        stop = int(form.get('stop'))
        color = form.get('color', 'green')
        
        name = form.get('name', '')
        if not name:
            template = env.get_template('BasicView/add_bookmark.html')
            return template.render(locals())

        ###

        bookmarks.add_bookmark(name, self.genome_name, sequence, start, stop,
                               +1, color)

        self._load_bookmarks()

        url = request.get_url(1)
        url += '/go?sequence=%s&start=%d&stop=%d' % (quote_plus(sequence),
                                                    start, stop)
        return response.redirect(url)

    def delete_bookmark(self):
        request = quixote.get_request()
        response = quixote.get_response()
        form = request.form

        bookmark_id = int(form['bookmark_id'])

        session = db.get_session()
        b = session.query(Bookmark).filter(Bookmark.id==bookmark_id).first()
        session.delete(b)
        session.commit()

        self._load_bookmarks()

        return response.redirect(request.get_url(1))

    def go(self):
        request = quixote.get_request()
        form = request.form
        url = request.get_url(1)
        response = quixote.get_response()

        sequence = form.get('sequence')

        start = form.get('start')
        if not start:
            start = 0
        start = int(start)

        try:
            stop = form.get('stop')
            if not stop:
                stop = len(self.genome_db[sequence])
            stop = int(stop)
        except KeyError:
            return response.redirect(url)

        url += '/%s:%s-%s/' % (quote_plus(sequence), start, stop)
        return response.redirect(url)
    
    def _q_lookup(self, component):
        try:
            interval = parse_interval_string(self.genome_db, component)
        except ValueError:
            return ErrorView("No such page.")
        except KeyError:
            return ErrorView("No such sequence in '%s'" % (self.genome_name,))

        nlmsa_list = [self.bookmarks_al]
        nlmsa_list.extend(self.nlmsa_list)

        wrappers = [BookmarkWrapperFactory()]
        wrappers.extend(self.wrappers)
        
        return IntervalView(interval, nlmsa_list, wrappers)

class IntervalView(Directory):
    _q_exports = ['', 'png', 'json']

    def __init__(self, interval, nlmsa_list, wrappers):
        self.interval = interval
        self.nlmsa_list = nlmsa_list
        self.wrappers = wrappers

    def _q_index(self):
        ival = self.interval
        parent_len = len(ival.pathForward)

        move_left_start = max(ival.start - len(ival)/2, 0)
        move_left_stop = min(move_left_start + len(ival), parent_len)

        move_right_stop = min(parent_len, ival.stop + len(ival)/2)
        move_right_start = max(0, move_right_stop - len(ival))

        zoom_out_start = max(ival.start - len(ival)/2, 0)
        zoom_out_stop = min(parent_len, ival.stop + len(ival)/2)
        
        zoom_in_start = ival.start + len(ival) / 4
        zoom_in_stop = ival.stop - len(ival) / 4

        l = []
        for i, nlmsa in enumerate(self.nlmsa_list):
            try:
                features = nlmsa[ival]
            except (KeyError, TypeError):
                features = []
            l.append((i, len(features)))
            print i, len(features)

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

class ErrorView(Directory):
    _q_exports = ['']

    def __init__(self, message):
        self.message = message

    def _q_index(self):
        message = self.message
        template = env.get_template('error.html')
        return template.render(locals())
