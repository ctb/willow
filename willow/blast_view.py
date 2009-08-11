import subprocess

import pkg_resources
pkg_resources.require('Quixote>=2.6')

import quixote
from quixote.directory import Directory

from pygr import sequtil, blast

from .web_util import env
from . import blastparser

class BlastView(Directory):
    _q_exports = [ '', 'do_blast' ]

    def __init__(self, genome_name, db):
        self.genome_name = genome_name
        self.db = db

    def _q_index(self):
        genome_name = self.genome_name
        filepath = self.db.filepath
        
        template = env.get_template('BlastView/index.html')
        return template.render(locals())

    def do_blast(self):
        request = quixote.get_request()
        form = request.form

        seq = form['seq']
        seq_type = sequtil.guess_seqtype(seq)
        db_type = self.db._seqtype
        prog = blast.blast_program(seq_type, db_type)
        
        do_translate = form.get('do_translate', 0)
        if do_translate:
            do_translate = int(do_translate)
        
        if prog == 'blastn' and do_translate:
            prog = 'tblastx'

        cmd = ['blastall', '-p', prog, '-d', self.db.filepath, '-e', '1']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate(">query\n" + seq)

        print 'BLAST STDERR:', stderr

        record = blastparser.parse_string(stdout).next()
        genome_name = self.genome_name
        filepath = self.db.filepath
        
        template = env.get_template('BlastView/results.html')
        return template.render(locals())
