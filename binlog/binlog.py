from collections import namedtuple
import os

from bsddb3 import db

Record = namedtuple('Record', ['liidx', 'clidx', 'value'])


class Binlog:
    @staticmethod
    def open_environ(path, create=True):
        """Open or create the db environment."""
        if not os.path.isdir(path):
            if os.path.exists(path):
                raise ValueError('%s is not a directory' % path)
            else:
                if create:
                    os.makedirs(path)
                else:
                    raise ValueError('environment does not exists.')

        env = db.DBEnv()

        flags = 0;
        flags |= db.DB_CREATE
        flags |= db.DB_INIT_MPOOL
        flags |= db.DB_INIT_LOCK
        flags |= db.DB_INIT_LOG
        flags |= db.DB_INIT_TXN

        env.open(path, flags)

        return env

    @staticmethod
    def open_logindex(env, filename):
        """Open or create the logindex inside the environment."""
        logindex = db.DB(env)
        try:
            logindex.open(filename, None, db.DB_RECNO, db.DB_CREATE)
        except db.DBError as exc:
            errcode, name = exc.args
            if errcode == 21:  # Is a directory
                raise ValueError('%s is a directory' % filename) from exc
            else:  # pragma: no cover
                raise

        return logindex
