from __future__ import print_function

import sys


class SafeIO(object):
    """SafeIO allows developers to change how the SDK prints output strings
    to the user. By default, it provides a generic 'write()' method for
    printing strings to stdout, but can be changed if needed."""

    def write(self, message, *args, **kwargs):
        print_kwargs = {
            k: arg for k, arg in kwargs.items() if k in ("sep", "end", "file", "flush")
        }
        print_kwargs["file"] = print_kwargs.get("file") or sys.stderr
        messages = [message] + list(args)
        print(*messages, **print_kwargs)

    def set_write_function(self, func):
        setattr(self, "write", func)


_safe_io = None


def get_safe_io():
    global _safe_io
    if _safe_io is None:
        _safe_io = SafeIO()
    return _safe_io


def safe_print(message, *args, **kwargs):
    get_safe_io().write(message, *args, **kwargs)
