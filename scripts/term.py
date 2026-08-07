"""Tiny ANSI helpers for the rebuild narration. Plain escape codes, no
dependencies; disabled automatically when stdout isn't a terminal (logs and
pipes stay clean). FORCE_COLOR=1 overrides for testing."""

import os
import sys

_ON = sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1"


def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _ON else str(s)


def bold(s):
    return _c("1", s)


def dim(s):
    return _c("2", s)


def cyan(s):
    return _c("36", s)


def green(s):
    return _c("32", s)


def amber(s):
    return _c("33", s)


def red(s):
    return _c("31", s)


RULE = "─" * 70
HEAVY = "═" * 70
