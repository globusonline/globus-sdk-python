.. globus-sdk-python documentation master file, created by
   sphinx-quickstart on Fri Apr  1 14:35:36 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Globus SDK for Python (Beta)
============================

This SDK provides a convenient Pythonic interface to
`Globus <https://www.globus.org>`_ REST APIs,
including the Transfer API and the Globus Auth API. Documentation
for the REST APIs is available at https://docs.globus.org.

Two interfaces are provided - a low level interface, supporting only
``GET``, ``PUT``, ``POST``, and ``DELETE`` operations, and a high level
interface providing helper methods for common API resources.

Source code is available at https://github.com/globus/globus-sdk-python.

Installation
============

The Globus SDK requires `Python <https://www.python.org/>`_ 2.6+ or 3.2+.
If a supported version of Python is not already installed on your system, see
this `Python installation guide \
<http://docs.python-guide.org/en/latest/starting/installation/>`_.

The simplest way to install the Globus SDK is using the ``pip`` package manager
(https://pypi.python.org/pypi/pip), which is included in most Python
installations:

::

    pip install globus-sdk

This will install the Globus SDK and it's dependencies.

Bleeding edge versions of the Globus SDK can be installed by checking out the
git repository and installing it manually:

::

    git checkout https://github.com/globus/globus-sdk-python.git
    cd globus-sdk-python
    python setup.py install


Basic Usage
===========

Most APIs require authentication using an access token, so the first
step to using the SDK is to acquire a token. For development, the
simplest way to get a token is to use the `Globus Tokens
<https://tokens.globus.org>`_ webapp. Globus Tokens provides you with
tokens for all Globus APIs which are valid for two days, and are tied to
a consent for ``Globus Tokens``. The appropriate method for obtaining
tokens for a production application depends on the type of application,
and is outside the scope of the SDK documentation (see the REST
documentation at https://docs.globus.org).

The webapp will provide you with instructions to save your tokens to the Globus
SDK config file, at ``~/.globus.cfg``.

To use the Transfer API:

.. code-block:: python

    from __future__ import print_function # for python 2
    from globus_sdk import TransferClient

    tc = TransferClient() # uses transfer_token from the config file

    # high level interface; provides iterators for list responses
    print("My Endpoints:")
    for ep in tc.endpoint_search(filter_scope="my-endpoints"):
        print(ep["display_name"], ep["id"])

API Documentation
=================
.. toctree::
   :maxdepth: 2

   api
   api/response
   api/exceptions
   api/baseclient
   oauth
   config
   deprecations

License
=======

Copyright 2016 University of Chicago

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
