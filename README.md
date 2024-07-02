# queryspy

This library catches N+1s in your Django project.

## Features

- Detects N+1s from missing prefetches and from use of `.defer()`/`.only()`
- Configurable thresholds
- Allow-list
- TODO: catches unused eager loads
- Well-tested
- No dependencies

## Acknowledgements

This library draws heavily from jmcarp's [nplusone](https://github.com/jmcarp/nplusone/).
It's not exactly a fork, but not far from it.

## Installation

To install `queryspy`, add it to your `INSTALLED_APPS` and `MIDDLEWARE`. You probably
don't want to run it in production: I haven't profiled it but it will have a performance
impact.

```python
if DEBUG:
    INSTALLED_APPS.append("queryspy")
    MIDDLEWARE.append("queryspy.middleware.queryspy_middleware")
```

This will detect N+1s that happen in web requests. If you also want to find N+1s in other
places like background tasks or management commands, you can use the `setup` and
`teardown` functions, or the `queryspy_context` context manager:

```python
from queryspy import setup, teardown, queryspy_context


def foo():
    setup()
    try:
        # ...
    finally:
        teardown()


@queryspy_context()
def bar():
    # ...


def baz():
    with queryspy_context():
        # ...
```

For example, if you use Celery, you can configure this using [signals](https://docs.celeryq.dev/en/stable/userguide/signals.html):

```python
from celery.signals import task_prerun, task_postrun
from queryspy import setup, teardown
from django.conf import settings

if settings.DEBUG:
    @task_prerun.connect()
    def setup_queryspy(*args, **kwargs):
        setup()

    @task_postrun.connect()
    def teardown_queryspy(*args, **kwargs):
        teardown()
```

## Configuration

By default, any issues detected by `queryspy` will raise a `QuerySpyError`. If you'd
rather log any detected N+1s, you can set:

```
QUERYSPY_RAISE = False
```

N+1s will be reported when the same query is executed twice. To configure this
threshold, set the following in your Django settings.

```python
QUERYSPY_NPLUSONE_THRESHOLD = 3
```

To handle false positives, you can temporarily disable `queryspy` in parts of your code
using a context manager:

```python
from queryspy import queryspy_ignore

with queryspy_ignore():
    # code in this block will not log/raise queryspy errors
```

Finally, if you want to ignore N+1 alerts from a specific model/field globally, you can
add it to your settings:
```python
QUERYSPY_ALLOWLIST = [
    {"model": "polls.Question", "field": "options"},

    # you can use fnmatch syntax in the model/field, too
    {"model": "polls.*", "field": "options"},

    # if you don't pass in a field, all N+1s arising from the model will be ignored
    {"model": "polls.Question"},
]
```

## Contributing

1. First, install [uv](https://github.com/astral-sh/uv).
2. Create a virtual env using `uv venv` and activate it with `source .venv/bin/activate`.
3. Run `make install` to install dev dependencies.
4. To run tests, run `make test`.

