What is this?
=============

This is a pytest plugin based on pytest-mongodb_ and mongomock_ that enables you
to test your code that relies on a callback- or Future-based API for non-blocking access
to a MongoDB and expects certain data to be present.
It allows you to specify fixtures for database collections in JSON/BSON or YAML
format. Under the hood we use the mongomock library, that you should
consult for documentation on how to use MongoDB mock objects. If suitable you
can also use a real MongoDB server.


Configuration
-------------

If you don't want to put your database fixtures on the top-level directory of your package
you have to specify a directory where ``pytest-async-mongodb`` looks for your data definitions.

To do so put a line like the following under the ``pytest`` section of your
``pytest.ini``-file put a

.. code-block:: ini

    [pytest]
    async_mongodb_fixture_dir =
      tests/unit/fixtures

    async_mongodb_fixtures =
      fixture_1
      fixture_2

``pytest-async-mongodb`` would then look for files ending in ``.yaml`` or ``.json`` in that
directory.

Unlike pytest-mongodb, you cannot specify a real MongoDB connection with the pymongo client.


Basic usage
-----------

After you configured ``pytest-async-mongodb`` so that it can find your fixtures you're ready to
specify some data. Regardless of the markup language you choose, the data is provided
as a list of documents (dicts). The collection that these documents are being inserted
into is given by the filename of your fixture-file. E.g.: If you had a file named
``players.yaml`` with the following content:

.. code-block:: yaml

    -
      name: Mario
      surname: Götze
      position: striker

    -
      name: Manuel
      surname: Neuer
      position: keeper


you'd end up with a collection ``players`` that has the above player definitions
inserted. If your fixture file is in JSON/BSON format you can also use BSON specific
types like ``$oid``, ``$date``, etc.


You get ahold of the database in your test-function by using the ``async_mongodb`` fixture
like so:

.. code-block:: python

    @pytest.mark.asyncio
    async def test_players(async_mongodb):
        manuel = await async_mongodb.players.find_one({'name': 'Manuel'})
        assert manuel['surname'] == 'Neuer'


For further information refer to the mongomock_ documentation.

.. _mongomock: https://github.com/vmalloc/mongomock
.. _pytest: https://docs.pytest.org/en/latest/
.. _pytest-mongodb: https://github.com/mdomke/pytest-mongodb/
