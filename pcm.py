#!/usr/bin/env python3
"""Professional Camera Man — Created by Caleb Elizondo. Run:  python3 pcm.py   (see README.md)"""
import sys

if sys.version_info < (3, 8):
    sys.exit("Python 3.8 or newer is needed.")
from pcm.cli import main

if __name__ == "__main__":
    sys.exit(main())
