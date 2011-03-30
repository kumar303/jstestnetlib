==============================
JS TestNet Client Library
==============================

Client library to execute JavaScript tests against a `JS TestNet`_ server.

.. _`JS TestNet`: https://github.com/kumar303/jstestnet

Install
=======

Using pip_ run::

  pip install git+git://github.com/kumar303/jstestnetlib.git#egg=jstestnetlib

.. _pip: http://pip.openplans.org/

Running Tests
=============

You can execute JavaScript tests using Nose_ after installing the package.  For example...

::

  nosetests --with-jstests \
            --jstests-server http://0.0.0.0:8000/ \
            --jstests-suite name-of-test-suite \
            --jstests-browsers firefox,chrome -v

.. _Nose: http://somethingaboutorange.com/mrl/projects/nose/
