#!/usr/bin/env python3
"""Mapper Hadoop Streaming : émet (mot, 1) pour chaque mot lu sur stdin."""
import sys

for ligne in sys.stdin:
    for mot in ligne.strip().split():
        print(f"{mot}\t1")
