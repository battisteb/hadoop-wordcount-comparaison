#!/usr/bin/env python3
"""Reducer Hadoop Streaming : les clés arrivent triées, on somme les valeurs consécutives."""
import sys

mot_courant, total = None, 0
for ligne in sys.stdin:
    mot, valeur = ligne.rstrip("\n").split("\t", 1)
    if mot == mot_courant:
        total += int(valeur)
    else:
        if mot_courant is not None:
            print(f"{mot_courant}\t{total}")
        mot_courant, total = mot, int(valeur)
if mot_courant is not None:
    print(f"{mot_courant}\t{total}")
