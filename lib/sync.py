import os
import interact

class Synchronizer:
    """ Send data of logs, notes, erratas
    from one place to another.
    """

    def __init__(self, config, dstdir):
        if not os.path.isdir(dstdir):
            print('%s not exists, or is not a directory' % dstdir, file=stderr)
            return

        # files to sync
        self.files  = [os.path.basename(x) for x in (config.log_path, config.note_path, config.errata_path)]
        self.srcdir = config.base_dir

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
        """ Send all data in source db but not in the
        destination db to the destination db.
        """
        from recorder import Recorder
        for file in self.files:
            srcpath = os.path.join(self.srcdir, file)
            dstpath = os.path.join(self.dstdir, file)
            srcRec  = Recorder(srcpath)
            srcdb   = srcRec.opendb()
            dstRec  = Recorder(dstpath)
            dstdb   = dstRec.opendb()
            keys    = [k for k in srcdb if k not in dstdb]
            count   = 0
            for key in keys:
                dstdb[key] = srcdb[key]
                print('transferring %s' % key)
                count += 1
            dstRec.persist()
            print('done, %s records transferred to %s' % (count, dstpath))
