import time
import os

class Viewer:
    """ class for openning the book, and go to a specified page,
    waiting for it to return, and retain the time info of the
    start and the end as well as the last page.

    To use different program to view the book, extend this class,
    and redefine the 'run' and 'get_end_page' methods.
    """
    viewer_log = os.path.join(os.getenv('HOME'), '.pv')

    def __init__(self, logger, config, start_page=0, take_log=True):
        if start_page:
            self.start_page = start_page + config.page_num_diff
        else:
            self.start_page = logger.cal_start_page() + config.page_num_diff
        self.take_log = take_log
        self.logger = logger
        self.book = config.book_path
        self.config = config
        self.__view()
        
    def __view(self):
        self.run()
        self.__log()

    def __log(self):
        """ log the start time, end time, start page, and end page
        """
        if not self.take_log:
            return
        complete = bool(self.end_page)
        ent = self.logger.make_log(
                    book_name=self.config.book_name,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    start_page=self.start_page - self.config.page_num_diff,
                    end_page=self.end_page,
                    complete=complete)
        self.logger.save(str(ent.start_time), ent)

    def run(self):
        """ open the book with the specified program,
        wait for it to end
        """
        cmd = 'pv -p %s %s' % (self.start_page, self.book)
        self.start_time = int(time.time())
        os.system(cmd)
        self.end_time = int(time.time())
        self.end_page = self.get_end_page()

    def get_end_page(self):
        """ get the last page number which was recorded
        before the viewer program quit.
        """
        viewer_log = self.viewer_log
        if not os.path.exists(viewer_log):
            print('%s not exists, check the viewer program' % viewer_log)
            return None

        file = os.path.realpath(self.book)
        for line in open(viewer_log):
            arr  = line.split(' ')
            page = arr[-1]
            path = ' '.join(arr[:-1])
            if path == file:
                page = int(page) - self.config.page_num_diff + 1
                return page

        print('Failed to determine the end page')
        print(str(sys.exc_info()[1]) + '\nYou need to complete it manually')
        return None
