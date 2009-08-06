import pkg_resources
pkg_resources.require('Quixote>=2.6')

from quixote.directory import Directory

from jinja2 import Template
from urllib import quote_plus

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

    def __init__(self, db, nlmsa_list):
        self.db = db
        self.nlmsa_list = nlmsa_list

    def _q_index(self):
        return 'hello, world'
    
    def _q_lookup(self, component):
        interval = parse_interval_string(self.db, component)
        return IntervalView(interval, self.nlmsa_list)

class IntervalView(Directory):
    _q_exports = ['']

    def __init__(self, interval, nlmsa_list):
        self.interval = interval
        self.nlmsa_list = nlmsa_list

    def _q_index(self):
        ival = self.interval
        l = [ (i, len(nlmsa[ival])) for (i, nlmsa) in enumerate(self.nlmsa_list) ]

        page = """
Interval: {{ ival.id }}[{{ ival.start }}:{{ ival.stop }}]
<p>
{% for i, n in l %}
{{ n }} features in nlmsa #{{ i }}<br>
{% endfor %}
"""
        return jinja_render(page, locals())
