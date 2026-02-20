Static pages for pretalx
========================

.. image:: https://raw.githubusercontent.com/pretalx/pretalx-pages/python-coverage-comment-action-data/badge.svg
   :target: https://htmlpreview.github.io/?https://github.com/pretalx/pretalx-pages/blob/python-coverage-comment-action-data/htmlcov/index.html
   :alt: Coverage

This is a plugin for `pretalx`_ that allows you to add static pages to your
event, for example FAQ, Terms of Service, a Code of Conduct, etc.

|screenshots|

Development setup
-----------------

1. Make sure that you have a working `pretalx development setup`_.

2. Clone this repository, eg to ``local/pretalx-pages``.

3. Activate the virtual environment you use for pretalx development.

4. Run ``pip install -e .`` within this directory to register this application with pretalx's plugin registry.

5. Restart your local pretalx server. This plugin should show up in the plugin list shown on startup in the console.
   You can now use the plugin from this repository for your events by enabling it in the 'plugins' tab in the settings.

This project uses `just`_ as a task runner and `uv`_ for dependency management.

Code style
~~~~~~~~~~

To check your plugin for code style violations, run::

    just fmt-check

To auto-fix formatting issues, run::

    just fmt

Testing
~~~~~~~

To run the test suite, run::

    just test

This will automatically install pretalx if it's not already present. If you want
to test against a local pretalx checkout instead, run::

    just install-pretalx-local /path/to/pretalx


License
-------

Copyright 2019 Tobias Kunze

Released under the terms of the Apache License 2.0


.. _pretalx: https://github.com/pretalx/pretalx
.. _pretalx development setup: https://docs.pretalx.org/en/latest/developer/setup.html
.. _just: https://just.systems/
.. _uv: https://docs.astral.sh/uv/
.. |screenshots| image:: https://raw.githubusercontent.com/pretalx/pretalx-pages/master/assets/screenshots.png
   :alt: Screenshots of pretalx pages
