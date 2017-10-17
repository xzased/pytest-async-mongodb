import asyncio
import os
import functools
import json
import codecs

import mongomock
import pytest
import yaml
from bson import json_util


_cache = {}


def pytest_addoption(parser):

    parser.addini(
        name='async_mongodb_fixtures',
        help='Load these fixtures for tests',
        type='linelist')

    parser.addini(
        name='async_mongodb_fixture_dir',
        help='Try loading fixtures from this directory',
        default=os.getcwd())

    parser.addoption(
        '--async_mongodb-fixture-dir',
        help='Try loading fixtures from this directory')



def wrapper(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        coro_func = asyncio.coroutine(func)
        return await coro_func(*args, **kwargs)
    return wrapped


class AsyncClassMethod(object):

    ASYNC_METHODS = []

    def __getattribute__(self, name):
        attr = super(AsyncCollection, self).__getattribute__(name)
        if type(attr) == types.MethodType and name in self.ASYNC_METHODS:
            attr = wrapper(attr)
        return attr


class AsyncCollection(AsyncClassMethod, mongomock.Collection):

    ASYNC_METHODS = [
        'find_one',
        'find',
    ]


class AsyncDatabase(mongomock.Database):

    def get_collection(self, name, codec_options=None, read_preference=None,
                       write_concern=None):
        collection = self._collections.get(name)
        if collection is None:
            collection = self._collections[name] = AsyncCollection(self, name)
        return collection


class AsyncMockMongoClient(AsyncClassMethod, mongomock.MongoClient):

    ASYNC_METHODS = [
        'collection_names'
    ]

    def get_database(self, name, codec_options=None, read_preference=None,
                     write_concern=None):
        db = self._databases.get(name)
        if db is None:
            db = self._databases[name] = AsyncDatabase(self, name)
        return db


@pytest.fixture(scope='function')
def async_mongodb(pytestconfig):
    client = AsyncMockMongoClient()
    db = client['pytest']
    clean_database(db)
    load_fixtures(db, pytestconfig)
    return db


def clean_database(db):
    for name in db.collection_names(include_system_collections=False):
        db.drop_collection(name)


def load_fixtures(db, config):
    option_dir = config.getoption('async_mongodb_fixture_dir')
    ini_dir = config.getini('async_mongodb_fixture_dir')
    fixtures = config.getini('async_mongodb_fixtures')
    basedir = option_dir or ini_dir

    for file_name in os.listdir(basedir):
        collection, ext = os.path.splitext(os.path.basename(file_name))
        file_format = ext.strip('.')
        supported = file_format in ('json', 'yaml')
        selected = fixtures and collection in fixtures
        if selected and supported:
            path = os.path.join(basedir, file_name)
            load_fixture(db, collection, path, file_format)


def load_fixture(db, collection, path, file_format):
    if file_format == 'json':
        loader = functools.partial(json.load, object_hook=json_util.object_hook)
    elif file_format == 'yaml':
        loader = yaml.load
    else:
        return
    try:
        docs = _cache[path]
    except KeyError:
        with codecs.open(path, encoding='utf-8') as fp:
            _cache[path] = docs = loader(fp)

    for document in docs:
        db[collection].insert(document)
