import pkg_resources
pkg_resources.require('Quixote>=2.6')

from quixote.directory import Directory

from jinja2 import Template
from urllib import quote_plus

class BasicView(Directory):
    _q_exports = ['']
    def _q_index(self):
        return 'hello, world'
