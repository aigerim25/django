#!/usr/bin/env python
import os
import sys

from decouple import AutoConfig

ENV_ID_KEY = 'BLOG_ENV_ID'
DEFAULT_ENV_ID = 'local'
SETTINGS_MODULE_TEMPLATE = 'settings.env.{env_id}'
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings')


def main() -> None:
    config = AutoConfig(search_path=SETTINGS_DIR)
    env_id = config(ENV_ID_KEY, default=DEFAULT_ENV_ID)
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        SETTINGS_MODULE_TEMPLATE.format(env_id=env_id),
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and is the virtual "
            'environment activated?'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()