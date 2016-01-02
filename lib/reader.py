#!/usr/local/bin/python3
'''
Author: Joshua Chen
Date: 2015-04-26, finished on 2015-05-01, took about 10 hours
Location: Shenzhen

This tool can be used to open a pre-set pdf book, keep track of
the openning time period, and log the read record, and viewing
log records. It can also be used to preview the plan, take notes,
log errata.
'''

import sys, os, time, shelve
import interact
from timeutils import isotime, strtosecond
from recorder import Recorder

class Config:
    '''
    a class to store the config info of the program.
    and provides some helper methods.
    '''
    def __init__(self, basedir=None):
        '''
        auto detect for the settings, and guide for initialization if needed.
        settings are:
            base_dir   : base directory
            book_name  : book name
            book_file  : book file base name
            end_page   : last page number of the book
            log_file   : log db base name
            note_file  : note db base name
            errata_file: errata db base name
            init_done  : flag to signified if settings are set
        in database, we store the base name of file, when loaded, we
        add the base directory to the beginning to build a full path.
        '''
        if basedir and os.path.isdir(basedir):
            self.base_dir   = os.path.normpath(basedir)
        else:
            self.base_dir   = os.path.dirname(os.path.realpath(__file__))

        config_file = '.reading_settings'
        config_path = os.path.join(self.base_dir, config_file)
        db = shelve.open(config_path)
        if not db.get('init_done'):
            self.init(db)
        self.load(db)

        self.logger = Logger(self.log_path)
        db.close()

    def init(self, db):
        '''
        guide user step by step to initialize the settings
        '''
        print('Initial setting, please answer some questions')
        book_name   = interact.readstr('book name: ')
        book_file   = interact.readstr('basename of book file: ')
        end_page    = interact.readint('last page number: ')
        default     = '.log'
        log_file    = interact.readstr('basename of log file [%s]: ' % default, default)
        default     = '.note'
        note_file   = interact.readstr('basename of note file [%s]: ' % default, default)
        default     = '.errata'
        errata_file = interact.readstr('basename of errata file [%s]: ' % default, default)

        # path of the pdf reader log file for determine the exit page number
        reader_log = os.path.join(os.getenv('HOME'), '.pv')
        if not os.path.exists(reader_log):
            print('could not find the pdf reader log file in default location')
            print('enter a full path or leave it empty for none: ')
            reader_log = interact.readstr('')

        # defference between the actual page number and the page label
        page_num_diff = interact.readint('page number of the first page label: ')
        page_num_diff -= 1

        db['book_name']     = book_name
        db['book_file']     = book_file
        db['end_page']      = end_page
        db['log_file']      = log_file
        db['note_file']     = note_file
        db['errata_file']   = errata_file
        db['reader_log']    = reader_log
        db['page_num_diff'] = page_num_diff
        db['page_per_day']  = 18
        db['init_done']     = True

    def load(self, db):
        '''
        load the settings from the database to the instance
        '''
        self.book_name      = db['book_name']
        self.book_path      = os.path.join(self.base_dir, db['book_file'])
        self.end_page       = db['end_page']
        self.log_path       = os.path.join(self.base_dir, db['log_file'])
        self.note_path      = os.path.join(self.base_dir, db['note_file'])
        self.errata_path    = os.path.join(self.base_dir, db['errata_file'])
        self.reader_log     = db['reader_log']
        self.page_num_diff  = db['page_num_diff']
        self.page_per_day   = db['page_per_day']

    def cal_start_page(self):
        '''
        calculate the starting page of the next reading from the log data.

        '''
        log = self.logger.last_complete_log()
        return log.end_page if log else 1


class Viewer:
    '''
    class for openning the pdf file and go to a specified page,
    waiting for it to return, and retain the time info of
    the start and the end.
    '''
    def __init__(self, logger, config, start_page=0, take_log=True):
        if start_page:
            self.start_page = start_page + config.page_num_diff
        else:
            self.start_page = config.cal_start_page() + config.page_num_diff

        self.take_log = take_log
        self.logger = logger
        self.book = config.book_path
        self.config = config
        self.__view()
        
    def __view(self):
        self.run()
        self.__log()

    def __log(self):
        '''
        log the start time, end time, and start page, end page
        '''
        if not self.take_log:
            return
        complete = bool(self.end_page)
        ent = self.logger.make_log(book_name=self.config.book_name,
                                   start_time=self.start_time,
                                   end_time=self.end_time,
                                   start_page=self.start_page - self.config.page_num_diff,
                                   end_page=self.end_page,
                                   complete=complete)
        self.logger.save(str(ent.start_time), ent)

    def run(self):
        '''
        open the document, and wait for it to end
        '''
        cmd = 'pv -p %s %s' % (self.start_page, self.book)
        self.start_time = int(time.time())
        os.system(cmd)
        self.end_time = int(time.time())
        self.end_page = self.get_end_page()

    def get_end_page(self):
        """
        get the last page number from the pdf reader program 'pv'
        the page number stored in the reader log file starts at 0.
        """
        reader_log = self.config.reader_log
        if not reader_log:
            return None

        file = os.path.realpath(self.book)
        for line in open(reader_log):
            arr  = line.split(' ')
            page = arr[-1]
            path = ' '.join(arr[:-1])
            if path == file:
                page = int(page) - self.config.page_num_diff + 1
                return page

        print('Failed to determine the end page')
        print(str(sys.exc_info()[1]) + '\nYou need to complete it manually')
        return None


class Record:
    '''
    just a namespace for a record
    '''
    

class LogEntry(Record):
    '''
    class for the log data, and method for representing the log entry
    '''
    def __str__(self):
        start   = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))
        end     = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time))
        seconds = self.end_time - self.start_time
        dura_h  = seconds // 3600
        dura_m  = (seconds % 3600) // 60
        dura_s  = seconds % 60
        text = '%s (time: %s:%s:%s, page: %s-%s)\n%s' % (
                    start, dura_h, dura_m, dura_s, self.start_page, self.end_page, end)
        return text

    def detail(self):
        start_time  = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.start_time))
        end_time    = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.end_time))
        duration    = (self.end_time - self.start_time) // 60
        page_count  = self.end_page - self.start_page
        format      = '[%s] - [%s] (%3d mins): %s-%s (%2d pages)'
        return format % (start_time, end_time, duration,
                        self.start_page, self.end_page, page_count)


class Logger(Recorder):
    '''
    for logging both the temporory log and the complete log
    these are the infos in an log entry:
    book_name, start_time, end_time, start_page, end_page.
    key for the log entry is the current time stamp.
    '''
    def make_log(self, book_name, start_time, end_time, start_page, end_page=None, complete=False):
        '''
        the end_page can be ommited when add a temporary log while reading,
        it will be fed when user complete the log later. the 'complete' signifies
        if the log's info are all fed.
        '''
        ent = LogEntry()
        ent.book_name   = book_name
        ent.start_time  = start_time
        ent.end_time    = end_time
        ent.start_page  = start_page
        ent.end_page    = end_page
        ent.complete    = complete
        return ent

    def fetch_tmplogs(self):
        self.opendb()
        tmplogs = [x for x in self.db.values() if not x.complete]
        tmplogs = sorted(tmplogs, key=lambda x: int(x.start_time))
        self.closedb()
        return tmplogs

    def ask_start_time(self, default=None):
        return self.ask_time('start time', default)

    def ask_end_time(self, default=None):
        return self.ask_time('end time', default)

    def ask_time(self, prompt='', default=None):
        '''
        interactively ask the user for time string
        '''
        if default:
            default_time_str = isotime(default)
            extra_text = '[%s]' % default_time_str
            prompt = '%s %s: ' % (prompt, extra_text)
            time_str = interact.readstr(prompt)
            time_str = time_str if time_str else default_time_str
        else:
            prompt = '%s: ' % prompt
            time_str = interact.readstr(prompt)
        if time_str:
            second = strtosecond(time_str)
            return second
        else:
            print('bad value, exit')
            exit(1)

    def ask_start_page(self, default=None):
        '''
        interactively ask the user for the start page number
        '''
        prompt = 'start page'
        return self.ask_page(prompt, default)

    def ask_end_page(self, default=None):
        '''
        interactively ask the user for the end page number
        '''
        prompt = 'end page'
        return self.ask_page(prompt, default)

    def ask_page(self, prompt='', default=None):
        '''
        interactively ask the user for page number
        '''
        if default:
            extra_text = '[%s]' % default
            prompt = '%s %s: ' % (prompt, extra_text)
            page = interact.readint(prompt, default=default)
        else:
            prompt = '%s: ' % prompt
            page = interact.readint(prompt)
        if page:
            return page
        else:
            print('bad value, exit')
            exit(1)

    def last_complete_log(self):
        '''
        return the latest log that is completed
        '''
        self.opendb()
        logs = (x for x in self.db.values() if x.complete)
        logs = sorted(logs, key=lambda x: int(x.start_time))
        self.closedb()
        return logs[-1] if logs else None

    def fetch_complete(self):
        self.opendb()
        logs = [x for x in self.db.values() if x.complete]
        logs = sorted(logs, key=lambda x: int(x.start_time))
        self.closedb()
        return logs

    def list(self):
        '''
        list all complete log entries
        '''
        for log in self.fetch_complete():
            print(log.detail())

    def list_sum(self):
        result = {}
        for log in self.fetch_complete():
            day         = time.strftime('%Y-%m-%d', time.localtime(log.start_time))
            duration    = (log.end_time - log.start_time) // 60
            pages       = log.end_page - log.start_page
            if day in result:
                result[day][0] += duration      # time summary
                result[day][1] += pages         # page summary
            else:
                result[day] = []
                result[day].append(duration)
                result[day].append(pages)
        for day in sorted(result.keys()):
            print('%s: %3d mins, %2d pages' % (day, result[day][0], result[day][1]))

    def clear_tmp_log(self):
        '''
        clear the temporary log
        '''
        self.opendb()
        for k, v in self.db.items():
            if not v.complete:
                del self.db[k]
        self.closedb()

    def dellast(self):
        self.opendb()
        keys = [k for k in self.db if self.db[k].complete]
        key = sorted(keys)[-1]
        log = self.db[key]
        i = interact.readstr('%s\nconfirm? [n] ' % log.detail())
        if i not in ('y', 'Y'):
            return
        del self.db[key]
        self.closedb()


class App:
    def __init__(self, config):
        self.args = sys.argv[1:]
        self.logger = config.logger
        self.config = config

    def help(self):
        '''
        show usage message
        '''
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
        print('%s plan [date spage epage numpage]  --  %s' % (basename, 'show reading plan'))

    def read(self, *args):
        '''
        open the reader in the background
        '''
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
        '''
        clear the temporary log entries from the main log database
        '''
        self.logger.clear_tmp_log()

    def list_log(self):
        '''
        list all complete log entries
        '''
        self.logger.list()

    def list_sum(self):
        '''
        list summaries of all complete log entries by days
        '''
        self.logger.list_sum()

    def log(self):
        '''
        complete an temporary log, or manually add a new complete one
        '''
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
        '''
        show the reading plan in the future from a given day
        if no day given, use the current day.
        '''
        second = time.mktime(time.strptime(day, '%Y-%m-%d')) if day else time.time()
        start_page = int(start_page) if start_page else self.config.cal_start_page()
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
        '''
        add notes to the notes database
        '''
        noteObj = Noter(self.config.note_path, self.config.book_name)
        actions = ['add', 'list', 'edit', 'delete']
        picked  = interact.printAndPick(actions, lineMode=True)
        func    = getattr(noteObj, picked[1])
        func()

    def errata(self):
        '''
        add errata record to the errata database
        '''
        Errator(self.config.errata_path, self.config.book_name).add()

    def sync(self, *args):
        if len(args) < 1:
            self.help()
            exit(1)
        Synchronizer(self.config, args[0])

    def today(self):
        '''show statistics of today '''
        # pull all logs of today, print statistics
        first_second = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')))
        last_second  = first_second + 86400
        db = self.logger.dbinstance()
        valid = lambda x: first_second <= int(x) <= last_second
        keys = [k for k in db if valid(k) and db[k].complete]

        spent_time = 0
        page_count = 0
        for key in keys:
            ent = db[key]
            spent_time += (ent.end_time - ent.start_time)
            page_count += (ent.end_page - ent.start_page)

        # get the start page, page_per_day
        start_page      = self.config.cal_start_page() - page_count
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
        """
        args is the arguments from the command line
        """
        action_map = {
            'read'  : (lambda: self.read(*args[2:])),
            'log'   : self.log,
            'cl'    : self.clear_log,
            'll'    : self.list_log,
            'days'  : self.list_sum,
            'note'  : self.note,
            'today' : self.today,
            'dellast'  : self.dellast,
            'plan'  : (lambda: self.plan(*args[2:])),
            'errata': self.errata,
            'sync'  : (lambda: self.sync(*args[2:])),
        }
        action = action_map.get(args[1], self.help)
        action()


class Noter(Recorder):
    def __init__(self, db_path, book_name):
        Recorder.__init__(self, db_path)
        self.book_name = book_name

    def make_makers(self):
        makers = []
        makers.append(('book',    (lambda x: self.book_name, None)))
        makers.append(('chapter', (interact.readint, 'Chapter: ')))
        makers.append(('subject', (interact.readstr, 'Subject: ')))
        makers.append(('content', (self.edit_content, None)))
        self.makers = makers

    def edit(self):
        '''
        change an existing note
        '''
        self.opendb()
        notes = sorted(self.db.items(), key=lambda x: int(x[0]))
        self.closedb()
        text_list = []
        for time, note in notes:
            text = isotime(int(time)) + '\n' + note.content[:80]
            text_list.append(text)
        idx, junk = interact.printAndPick(text_list)

        key  = notes[idx][0]
        note = notes[idx][1]

        prompt = 'Chapter [%s]: ' % note.chapter
        note.chapter = interact.readint(prompt, default=note.chapter)
        prompt = 'Subject [%s]: ' % note.subject
        note.subject = interact.readstr(prompt, default='') or note.subject
        note.content = self.edit_content(data=note.content)
        self.save(key, note)

    def list(self):
        self.opendb()
        notes = sorted(self.db.items(), key=lambda x: int(x[0]))
        self.closedb()
        text_list = []
        for time, note in notes:
            text = isotime(int(time)) + '\n' + note.content[:80]
            text_list.append(text)
        res = interact.printAndPick(text_list)
        if res:
            idx = res[0]
        else:
            return
        key  = notes[idx][0]
        note = notes[idx][1]
        print('-' * 80)
        print('Book: %s' % note.book)
        print('Chapter: %s' % note.chapter)
        print('Subject: %s' % note.subject)
        print('Content:\n%s' % note.content)

    def delete(self):
        assert False, 'not yet implemented'

    def add(self):
        '''
        caller must supply the field names and maker
        function and arguments for each field.
        '''
        self.make_makers()
        ent = Record()
        for (field_name, (func, args)) in self.makers:
            setattr(ent, field_name, func(args))
        self.save(str(int(time.time())), ent)

    def edit_content(self, *junk, data=None):
        '''
        edit (add, change, delete) some data, and return it as string
        use temporary file to store the data while creating.
        '''
        import tempfile
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        if data:
            tmpfile.write(data.encode())
            tmpfile.flush()
        self.edit_file(tmpfile.name)
        content = open(tmpfile.name).read()
        os.unlink(tmpfile.name)
        return content

    def edit_file(self, path):
        '''
        edit a file of a given name, using the editor
        specified in EDITOR environment variable, or
        vi if none specified.
        '''
        default_editor = 'vi'
        editor = os.environ.get('EDITOR')
        if not editor: editor = default_editor
        os.system('%s %s' % (editor, path))


class Errator(Noter):
    def make_makers(self):
        makers = []
        makers.append(('book',    (lambda x: self.book_name, None)))
        makers.append(('page',    (interact.readstr, 'Page: ')))
        makers.append(('content', (self.edit_content, None)))
        self.makers = makers

class Synchronizer:
    '''class to sync logs, notes, erratas'''
    def __init__(self, config, dstdir):
        if not os.path.isdir(dstdir):
            print('%s not exists, or is not a directory' % dstdir, file=stderr)
            return

        # files to sync
        self.files  = [os.path.basename(x) for x in (config.log_path, config.note_path, config.errata_path)]

        # check file existence
        for file in self.files:
            if not os.path.exists(os.path.join(dstdir, file)):
                prompt = 'no "%s" in the dst dir, new file will be created, continue? [n]: ' % file
                ans = interact.readstr(prompt)
                if ans not in ('y', 'Y'):
                    return

        self.dstdir = dstdir
        self.sync()

    def sync(self):
        '''synchronize method
        send all data in source db but not in the
        destination db to the destination db
        '''
        import shelve
        srcdir = config.base_dir
        for file in self.files:
            srcpath = os.path.join(srcdir, file)
            dstpath = os.path.join(self.dstdir, file)
            srcdb   = shelve.open(srcpath)
            dstdb   = shelve.open(dstpath)
            keys    = [k for k in srcdb if k not in dstdb]
            count   = 0
            for key in keys:
                dstdb[key] = srcdb[key]
                print('transferring %s' % key)
                count += 1
            srcdb.close()
            dstdb.close()
            print('done, %s records transferred to %s' % (count, dstpath))


if __name__ == '__main__':
    print('not allowed to run directly', file=sys.stderr)
    exit(1)
