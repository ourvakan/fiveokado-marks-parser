from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker, session
from sqlalchemy.exc import DatabaseError, ProgrammingError
import pandas as pd
import yaml
from pathlib import Path
from contextlib import contextmanager
import logging
import socket
import sqlite3

import utils.setup_logging
from db.models import Base

logger = logging.getLogger(__file__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def get_class_by_tablename(tablename):
    """Return class reference mapped to table.
    Raise an exception if class not found

    :param tablename: String with name of table.
    :return: Class reference.
    """
    for c in Base._decl_class_registry.values():
        if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
            return c
    raise AttributeError(f'No model with tablename "{tablename}"')


class DbConfig(object):
    base_path = Path(__file__).parent.parent

    def __init__(self, db_config):
        self._conf = yaml.load(open(f'{type(self).base_path}/db/config.yml'), Loader=yaml.FullLoader)[db_config]

        if db_config.startswith('sqlite'):
            path_to_sqlite = self.base_path / self._conf['path_from_base']
            self.connect_str = self._conf["connect_str"].format(path=path_to_sqlite)
        else:
            self.connect_str = self._conf["connect_str"].format(
                user=self._conf["user"], password=self._conf["password"],
                address=self._conf["address"], schema=self._conf["schema"])


class DBConnection:
    """
    Initializes connection to a database
    To update models file use:
    sqlacodegen --outfile models.py mysql+pymysql://{user}:{pwd}@{address}
    """
    _sessions = sessionmaker()

    def __init__(self, db_config: str) -> None:
        # We neither create connection, nor session here
        self.metadata = MetaData()
        self.config = DbConfig(db_config)

        if db_config.startswith('sqlite'):
            self.engine = create_engine(self.config.connect_str,
                                        connect_args={'detect_types': sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES},
                                        native_datetime=True)  # , echo=True
        else:
            self.engine = create_engine(self.config.connect_str)

    @contextmanager
    def get_test_session(self, **kwargs) -> session:
        """
        Test session context, even commits won't be persisted into db.
        :Keyword Arguments:
            * autoflush (``bool``) -- default: True
            * autocommit (``bool``) -- default: False
            * expire_on_commit (``bool``) -- default: True
        """
        try:
            connection = self.engine.connect()
            transaction = connection.begin()
            my_session = type(self)._sessions(bind=connection, **kwargs)
        except Exception as e:
            ExceptionHandler.handle_connection_exceptions(e)
        try:
            yield my_session
        except Exception as e:
            ExceptionHandler.handle_user_side_exceptions(e)
        finally:
            # Do cleanup, rollback and closing, whatever happens
            my_session.close()
            transaction.rollback()
            connection.close()

    @contextmanager
    def get_live_session(self) -> session:
        """
        This is a session that can be committed. Changes will be reflected in the database.
        """
        # Automatic transaction and connection handling in session
        connection = self.engine.connect()
        my_session = type(self)._sessions(bind=connection)
        try:
            yield my_session
        except Exception as e:
            ExceptionHandler.handle_user_side_exceptions(e)
        finally:
            my_session.close()
            connection.close()

    def read_as_df(self, query, **kwargs) -> pd.DataFrame:
        """
        Query may be an SQL string or an SQLAlchemy selectable
        : Keyword Arguments:
        * coerce_float : boolean, default True
            Attempts to convert values of non-string, non-numeric objects (like decimal.Decimal) to floating point, useful for SQL result sets.
        * parse_dates : list or dict, default: None
            List of column names to parse as dates, Dict of {column_name: format string} or Dict of {column_name: arg dict},
        * columns : list, default: None
            List of column names to select from SQL table (only used when reading a table).
        * chunksize : int, default None
            If specified, return an iterator where chunksize is the number of rows to include in each chunk.

        read more in the original documentation: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_sql.html
        """
        df = pd.read_sql(query, self.engine, **kwargs)
        return df


class ExceptionHandler:

    @staticmethod
    def handle_connection_exceptions(exc):
        if isinstance(exc, socket.timeout):
            logger.exception('Failed to connect to the database. TimeOutException. The address may be wrong.')
            raise
        if isinstance(exc, ProgrammingError):
            logger.exception(f'{exc}\nFailed to connect to the database - wrong password, username or schema.')
            raise
        if isinstance(exc, DatabaseError):
            logger.exception(f'{exc}\nFailed to connect to the database - wrong address.')
            raise
        logger.exception(exc)
        raise

    @staticmethod
    def handle_user_side_exceptions(exc):
        logger.exception(exc)
        raise
