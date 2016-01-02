#!/usr/local/bin/python3
"""
Author: Joshua Chen
Date: 2015-04-26, finished on 2015-05-01, took about 10 hours
Location: Shenzhen

This tool can be used to open a pre-set pdf book, keep track of
the openning time period, and log the read record, and viewing
log records. It can also be used to preview the plan, take notes,
log errata.
"""

import sys, os, time
import interact
from recorder import Recorder
from viewer import Viewer
from logger import Logger
from noter import Noter
from errator import Errator
from sync import Synchronizer

class Config:
    """ Store the config info of the program,
    and provides some helper methods.
    """
    defaultLogPath    = ".log"
    defaultNotePath   = ".note"
    defaultErrataPath = ".errata"
    defaultPagePerDay = 18
    config_file       = '.reading_settings'

    def __init__(self, basedir=None):
        """ Auto detect for the settings, and guide for
        initialization if needed.

        Settings are:
            base_dir   : base directory
            book_name  : book name
            book_file  : book file base name or abs path
            end_page   : last page number of the book
            log_file   : log db base name
            note_file  : note db base name
            errata_file: errata db base name
            init_done  : flag to signified if settings are set

        In database, store the base name of file, when loaded,
        the base directory will be added to build a full path,
        book_file is an exception.
        """
        if basedir and os.path.isdir(basedir):
            self.base_dir   = os.path.normpath(basedir)
        else:
            self.base_dir   = os.path.dirname(os.path.realpath(__file__))

        config_path = os.path.join(self.base_dir, self.config_file)
        rec         = Recorder(config_path)
        db          = rec.opendb()
        if not db.get('init_done'):
            self.init(db)
            rec.persist()
        self.load(db)

        self.logger = Logger(self.log_path)
        rec.closedb()

    def config(self):
        """ Call init or update to set the settings
        """
        config_path = os.path.join(self.base_dir, self.config_file)
        rec = Recorder(config_path)
        db  = rec.opendb()
        if not db.get('init_done'):
            self.init(db)
        else:
            self.update(db)
        rec.persist()

    def getBookFileName(self, default=None):
        """ Get the file name from user, check file existence
        """
        if default:
            prompt =  'abs path (or relative to the base dir) of book file\n'
            prompt += '  [%s]: ' % default
        else:
            prompt =  'abs path (or relative to the base dir) of book file\n'
            prompt += '  --> '
        while True:
            book_file = interact.readstr(prompt, default=default)
            book_path = self.fixupBookPath(book_file)
            if not os.path.exists(book_path):
                print('%s not exists' % book_path, file=sys.stderr)
            else:
                return book_file

    def init(self, db):
        """ Initialize the settings interactively
        """
        print('Initial setting, please answer some questions')
        book_name   = interact.readstr('book name: ')
        book_file   = self.getBookFileName()
        end_page    = interact.readint('last page number: ')
        default     = self.defaultLogPath
        log_file    = interact.readstr('basename of log file [%s]: ' % default, default)
        default     = self.defaultNotePath
        note_file   = interact.readstr('basename of note file [%s]: ' % default, default)
        default     = self.defaultErrataPath
        errata_file = interact.readstr('basename of errata file [%s]: ' % default, default)

        # path of the book viewer log file for determine the exit page
        # number user must change the Viewer class to change this value
        viewer_log = Viewer.viewer_log
        prompt =  'viewer log: %s\n' % viewer_log
        prompt += '  to change this value, you need to edit\n'
        prompt += '  the Viewer class, press Enter to continue '
        interact.readstr(prompt, '')

        # defference between the actual page number and the page label
        page_num_diff = interact.readint('page number of the first page label: ')
        page_num_diff -= 1

        # page per day
        default       = self.defaultPagePerDay
        prompt        = 'how many pages for one day? [%s]: ' % default
        page_per_day  = interact.readint(prompt, default)

        db['book_name']     = book_name
        db['book_file']     = book_file
        db['end_page']      = end_page
        db['log_file']      = log_file
        db['note_file']     = note_file
        db['errata_file']   = errata_file
        db['viewer_log']    = viewer_log
        db['page_num_diff'] = page_num_diff
        db['page_per_day']  = page_per_day
        db['init_done']     = True

    def fixupBookPath(self, name):
        """ If the name is not absolute, make it
        an abosolute base on the self.base_dir.
        """
        if os.path.isabs(name):
            path = name
        else:
            path = os.path.join(self.base_dir, name)
        return path

    def load(self, db):
        """ Load the settings from the database to the instance
        """
        self.book_name      = db['book_name']
        self.book_path      = self.fixupBookPath(db['book_file'])
        self.end_page       = db['end_page']
        self.log_path       = os.path.join(self.base_dir, db['log_file'])
        self.note_path      = os.path.join(self.base_dir, db['note_file'])
        self.errata_path    = os.path.join(self.base_dir, db['errata_file'])
        self.page_num_diff  = db['page_num_diff']
        self.page_per_day   = db['page_per_day']

    def update(self, db):
        """ Update the settings interactively
        """
        default     = self.book_name
        prompt      = 'book name [%s]: ' % default
        book_name   = interact.readstr(prompt, default)

        default     = self.book_path
        book_file   = self.getBookFileName(default=default)

        default     = self.end_page
        prompt      = 'last page number [%s]: ' % default
        end_page    = interact.readint(prompt, default)

        default     = os.path.basename(self.log_path)
        prompt      = 'basename of log file [%s]: ' % default
        log_file    = interact.readstr(prompt, default)

        default     = os.path.basename(self.note_path)
        prompt      = 'basename of note file [%s]: ' % default
        note_file   = interact.readstr(prompt, default)

        default     = os.path.basename(self.errata_path)
        prompt      = 'basename of errata file [%s]: ' % default
        errata_file = interact.readstr(prompt, default)

        # path of the book viewer log file for determine the exit page
        # number user must change the Viewer class to change this value
        viewer_log = Viewer.viewer_log
        prompt =  'viewer log: %s\n' % viewer_log
        prompt += '  to change this value, you need to edit\n'
        prompt += '  the Viewer class, press Enter to continue '
        interact.readstr(prompt, '')

        # defference between the actual page number and the page label
        default       = self.page_num_diff + 1
        prompt        = 'page number of the first page label [%s]: ' % default
        page_num_diff = interact.readint(prompt, default)
        page_num_diff -= 1

        # page per day
        default       = self.page_per_day
        prompt        = 'how many pages for one day? [%s]: ' % default
        page_per_day  = interact.readint(prompt, default)

        db['book_name']     = book_name
        db['book_file']     = book_file
        db['end_page']      = end_page
        db['log_file']      = log_file
        db['note_file']     = note_file
        db['errata_file']   = errata_file
        db['page_num_diff'] = page_num_diff
        db['page_per_day']  = page_per_day
        db['init_done']     = True

        print('done.')


class App:
    def __init__(self, config):
        self.args = sys.argv[1:]
        self.logger = config.logger
        self.config = config

    def help(self):
        """ Show usage message
        """
        basename = os.path.basename(sys.argv[0])
        print('Usage:')
        print('%s read [page] [nolog] --  %s' % (basename, 'read the book'))
        print('%s log          --  %s' % (basename, 'add reading log'))
        print('%s ll           --  %s' % (basename, 'list reading log'))
        print('%s dellast      --  %s' % (basename, 'delete the last log'))
        print('%s days         --  %s' % (basename, 'list summary of days'))
        print('%s cl           --  %s' % (basename, 'clear temporary reading log'))
        print('%s note         --  %s' % (basename, 'add note'))
        print('%s errata       --  %s' % (basename, 'collect errata'))
        print('%s today        --  %s' % (basename, 'show today\'s statistics'))
        print('%s sync dstdir  --  %s' % (basename, 'sync data to files in dstdir'))
        print('%s config       --  %s' % (basename, 'interactive configuring'))
        print('%s plan [date spage epage numpage]  --  %s' % (basename, 'show reading plan'))

    def read(self, *args):
        """ Open the reader in the background
        """
        args = list(args)
        take_log = True    # if log automatically
        start_page = 0
        if len(args):
            if 'nolog' in args:
                take_log = False
                args.remove('nolog')
            if len(args) and args[0].isdigit():
                start_page = int(args[0])
        if os.fork() == 0:
            os.setsid()
            Viewer(self.logger, self.config, start_page, take_log)
        
    def clear_log(self):
        """ Clear the temporary log entries from the main log database
        """
        self.logger.clear_tmp_log()

    def list_log(self):
        """ List all complete log entries
        """
        self.logger.list()

    def list_sum(self):
        """ List summaries of all complete log entries by days
        """
        self.logger.list_sum()

    def log(self):
        """ Complete an temporary log, or manually add a new complete one
        """
        # use the tmp log record if any
        tmplogs = self.logger.fetch_tmplogs()
        if tmplogs:
            ent = interact.printAndPick(tmplogs)
            if ent:
                ent.start_time  = self.logger.ask_start_time(ent.start_time)
                ent.end_time    = self.logger.ask_end_time(ent.end_time)
                ent.start_page  = self.logger.ask_start_page(ent.start_page)
                ent.end_page    = self.logger.ask_end_page(ent.end_page)
                ent.complete    = True
                self.logger.save(str(ent.start_time), ent)
                return

        start_time  = self.logger.ask_start_time()
        end_time    = self.logger.ask_end_time()
        start_page  = self.logger.ask_start_page()
        end_page    = self.logger.ask_end_page()
        ent = self.logger.make_log(self.config.book_name, start_time, end_time, start_page, end_page, True)
        self.logger.save(str(ent.start_time), ent)

    def plan(self, day=None, start_page=None, end_page=None, page_per_day=None):
        """ Show the reading plan in the future from a given day
        if no day given, use the current day.
        """
        second = time.mktime(time.strptime(day, '%Y-%m-%d')) if day else time.time()
        start_page = int(start_page) if start_page else self.logger.cal_start_page()
        end_page = int(end_page) if end_page else self.config.end_page
        if page_per_day:
            page_per_day = int(page_per_day)
        else:
            page_per_day = self.config.page_per_day
        def producer(first_of_day, second):
            end = False
            while not end:
                last_of_day = first_of_day + page_per_day - 1
                if last_of_day > end_page:
                    last_of_day = end_page
                    end = True
                text = time.strftime('%Y-%m-%d', time.localtime(second))
                text = '%s %s - %s' % (text, first_of_day, last_of_day)
                yield text
                first_of_day = last_of_day + 1
                second += 86400     # the next day
        for line in producer(start_page, second):
            print(line)

    def note(self):
        """ Add notes to the notes database
        """
        noteObj = Noter(self.config.note_path, self.config.book_name)
        actions = ['add', 'list', 'edit', 'delete']
        picked  = interact.printAndPick(actions, lineMode=True)
        func    = getattr(noteObj, picked[1])
        func()

    def errata(self):
        """ Add errata record to the errata database
        """
        Errator(self.config.errata_path, self.config.book_name).add()

    def sync(self, *args):
        if len(args) < 1:
            self.help()
            exit(1)
        Synchronizer(self.config, args[0])

    def today(self):
        """ Show statistics of today
        """
        # pull all logs of today, print statistics
        first_second = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')))
        last_second  = first_second + 86400
        db = self.logger.opendb()
        valid = lambda x: first_second <= int(x) <= last_second
        keys = [k for k in db if valid(k) and db[k].complete]

        spent_time = 0
        page_count = 0
        for key in keys:
            ent = db[key]
            spent_time += (ent.end_time - ent.start_time)
            page_count += (ent.end_page - ent.start_page)

        # get the start page, page_per_day
        start_page      = self.logger.cal_start_page() - page_count
        page_per_day    = self.config.page_per_day
        end_page        = start_page + page_per_day

        stat_text = 'done' if page_count >= page_per_day else 'not done'
        dura_h    = spent_time // 3600
        dura_m    = (spent_time % 3600) // 60
        dura_s    = spent_time % 60
        time_str  = '%s:%s:%s' % (dura_h, dura_m, dura_s)
        print('Task: %s-%s (%s pages)' % (start_page, end_page, page_per_day))
        print('Page: %s/%s (%s)' % (page_count, page_per_day, stat_text))
        print('Time: %s spent' % time_str)

    def dellast(self):
        self.logger.dellast()

    def run(self, args):
        """ Args is the arguments from the command line
        """
        action_map = {
            'read'    : (lambda: self.read(*args[2:])),
            'log'     : self.log,
            'cl'      : self.clear_log,
            'll'      : self.list_log,
            'days'    : self.list_sum,
            'note'    : self.note,
            'today'   : self.today,
            'dellast' : self.dellast,
            'plan'    : (lambda: self.plan(*args[2:])),
            'errata'  : self.errata,
            'sync'    : (lambda: self.sync(*args[2:])),
            'config'  : self.config.config,
        }
        action = action_map.get(args[1], self.help)
        action()
