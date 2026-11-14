#!/usr/bin/env python
import os, sys
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ.setdefault("DJANGO_DEBUG", "1")  # local development default; production must set DJANGO_DEBUG=0
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
