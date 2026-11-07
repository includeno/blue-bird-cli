"""Bluebird's documented URL scheme, shared by preview and dispatch."""
import argparse
from urllib.parse import quote, urlencode


def positive_minutes(value):
    try:
        minutes = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('duration must be a positive integer (minutes)')
    if minutes <= 0:
        raise argparse.ArgumentTypeError('duration must be a positive integer (minutes)')
    return minutes


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError('value must not be blank')
    return value


def build_url(args):
    if args.command == 'open': return 'bluebird:'
    if args.command == 'focus': return 'bluebird://focus'
    params = {key: getattr(args, key) for key in ('title', 'notes', 'duration', 'priority', 'tags')
              if getattr(args, key) is not None}
    if 'priority' in params:
        params['priority'] = {'low': 1, 'medium': 2, 'high': 3}[params['priority']]
    return 'bluebird://add?' + urlencode(params, quote_via=quote)
