from record import Record
from recorder import Recorder
from timeutils import isotime
import interact
import os

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
        """ change an existing note
        """
        cont = self.opendb()
        notes = sorted(cont.items(), key=lambda x: int(x[0]))
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
        cont = self.opendb()
        notes = sorted(cont.items(), key=lambda x: int(x[0]))
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
        """ caller must supply the field names and
        maker function and arguments for each field.
        """
        self.make_makers()
        ent = Record()
        for (field_name, (func, args)) in self.makers:
            setattr(ent, field_name, func(args))
        self.save(str(int(time.time())), ent)

    def edit_content(self, *junk, data=None):
        """ edit (add, change, delete) some data, and return it
        as string use temporary file to store the data while creating.
        """
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
        """ edit a file of a given name, using the editor
        specified in EDITOR environment variable, or vi
        if none specified.
        """
        default_editor = 'vi'
        editor = os.environ.get('EDITOR')
        if not editor: editor = default_editor
        os.system('%s %s' % (editor, path))
