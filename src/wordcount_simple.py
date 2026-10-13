"""Méthode 1 : comptage de mots en Python séquentiel simple (dictionnaire)."""
import sys


def compter_occurrences(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        mots = f.read().split()

    compteur = {}
    for mot in mots:
        compteur[mot] = compteur.get(mot, 0) + 1
    return compteur


if __name__ == "__main__":
    fichier = sys.argv[1] if len(sys.argv) > 1 else "mots.txt"
    resultats = compter_occurrences(fichier)
    for mot, nb in sorted(resultats.items(), key=lambda x: x[1], reverse=True):
        print(f"{mot} : {nb}")
