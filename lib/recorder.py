import interact
import ZODB, transaction
from BTrees.OOBTree import OOBTree

class Recorder:
    """ A class for managing simple records.
    The records stored in a dictionary like manner,
    that is, one key, one value, ZODB is used.
    """

    contName = 'main'

    def __init__(self, db_path, contName=None):
        self.db_path    = db_path
        self.conn       = None
        if contName:
            self.contName   = contName

    def opendb(self, contName=None):
        """ Open the database if not yet,
        return the required container.
        """
        if self.conn is None:
            self.conn = ZODB.connection(self.db_path)
        if contName is None:
            contName = self.contName
        if contName is None:
            raise "must specify a container name"
        return self.getContainer(self.conn.root, contName)

    def getContainer(self, root, contName):
        """ return a ZODB container, create it if not yet exists
        """
        cont = getattr(root, contName, None)
        if cont is None:
            cont = OOBTree()
            setattr(root, contName, cont)
            transaction.commit()
        return cont

    def closedb(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def persist(self):
        """ Make the record persistent
        """
        transaction.commit()

    def save(self, key, ent, contName=None):
        cont = self.opendb(contName=contName)
        cont[key] = ent
        self.persist()

    def add(self, key, ent):
        self.save(key, ent)

    def delete(self, key):
        cont = self.opendb()
        del cont[key]
        self.persist()

    def search(self, filter):
        # filter is a function takes two arguments, and returns Boolean
        # subclass must overload the __str__ method
        cont = self.opendb()
        entries = ((k, v) for k,v in cont.items() if filter(k, v))
        return entries

    def list(self):
        return Recorder.search(self, filter=(lambda k,v: True))

    def menu(self):
        choices = [
            ['add', self.add],
            ['list', self.list],
            ['search', self.search],
            ['edit', self.edit],
            ['delete', self.delete]
        ]
        i, junk = interact.printAndPick([x for x, y in choices], prompt='choice: ', lineMode=True)
        action = choices[i][-1]
        action()
