from noter import Noter
import interact

class Errator(Noter):
    def make_makers(self):
        makers = []
        makers.append(('book',    (lambda x: self.book_name, None)))
        makers.append(('page',    (interact.readstr, 'Page: ')))
        makers.append(('content', (self.edit_content, None)))
        self.makers = makers
