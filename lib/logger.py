from record import Record
from recorder import Recorder
from timeutils import isotime, strtosecond
import time
import interact

class LogEntry(Record):
    """ class for the log data, and method
    for representing the log entry
    """
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
    """ Logging both the temporory log and the complete log

    Info in an log entry:
        book_name
        start_time
        end_time
        start_page
        end_page.

    key of the log entry is the current time stamp.
    """

    def make_log(self, book_name, start_time, end_time,
                    start_page, end_page=None, complete=False):
        """ the end_page can be ommited when add a temporary
        log while reading, it will be fed when user complete
        the log later. the 'complete' signifies if the log's
        info are all fed.
        """
        ent = LogEntry()
        ent.book_name   = book_name
        ent.start_time  = start_time
        ent.end_time    = end_time
        ent.start_page  = start_page
        ent.end_page    = end_page
        ent.complete    = complete
        return ent

    def fetch_tmplogs(self):
        cont = self.opendb()
        tmplogs = [x for x in cont.values() if not x.complete]
        tmplogs = sorted(tmplogs, key=lambda x: int(x.start_time))
        return tmplogs

    def ask_start_time(self, default=None):
        return self.ask_time('start time', default)

    def ask_end_time(self, default=None):
        return self.ask_time('end time', default)

    def ask_time(self, prompt='', default=None):
        """ interactively ask the user for time string
        """
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
        """ interactively ask the user for the start page number
        """
        prompt = 'start page'
        return self.ask_page(prompt, default)

    def ask_end_page(self, default=None):
        """ interactively ask the user for the end page number
        """
        prompt = 'end page'
        return self.ask_page(prompt, default)

    def ask_page(self, prompt='', default=None):
        """ interactively ask the user for page number
        """
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
        """ return the latest log that is completed
        """
        cont = self.opendb()
        logs = (x for x in cont.values() if x.complete)
        logs = sorted(logs, key=lambda x: int(x.start_time))
        return logs[-1] if logs else None

    def fetch_complete(self):
        cont = self.opendb()
        logs = [x for x in cont.values() if x.complete]
        logs = sorted(logs, key=lambda x: int(x.start_time))
        return logs

    def list(self):
        """ list all complete log entries
        """
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
        """ clear the temporary log
        """
        cont = self.opendb()
        for k, v in cont.items():
            if not v.complete:
                del cont[k]
        self.persist()

    def dellast(self):
        cont = self.opendb()
        keys = [k for k in cont if cont[k].complete]
        if not keys: return
        key = sorted(keys)[-1]
        log = cont[key]
        default = 'n'
        i = interact.readstr('%s\nconfirm? [%s] ' % (log.detail(), default), default)
        if i not in ('y', 'Y'):
            return
        del cont[key]
        self.persist()

    def cal_start_page(self):
        """ calculate the starting page of
        the next reading from the log data.
        """
        log = self.last_complete_log()
        return log.end_page if log else 1
