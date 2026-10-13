"""Génération des fichiers de test pour le comptage de mots.

1. `generer_base`   : fichier de N lignes, chaque ligne contient UN mot (avec répétition).
2. `dupliquer`      : fichier plus gros de m x N lignes obtenu en dupliquant les N lignes m fois.

Usage :
    python src/generer_fichier.py --n 10000 --m 1 10 100 --out data
"""
import argparse
import os
import random

# Vocabulaire (mots de l'exemple du cours + quelques autres).
VOCABULAIRE = [
    "chat", "chien", "arbre", "fleur", "maison", "soleil", "montagne", "livre",
    "ciel", "mer", "lune", "route", "oiseau", "jardin", "voiture", "riviere",
    "foret", "nuage", "etoile", "pomme", "table", "porte", "fenetre", "ecole",
    "train", "velo", "musique", "papier", "crayon", "ordinateur", "donnee",
    "hadoop", "python", "cluster", "reseau", "serveur", "fichier", "ville",
    "plage", "neige",
]


def generer_base(chemin, n, graine=42):
    """Écrit n lignes contenant chacune un mot tiré (avec remise) du vocabulaire.

    Les poids suivent une loi de type Zipf (1/rang) pour obtenir une
    distribution réaliste : quelques mots très fréquents, beaucoup de mots rares.
    """
    rng = random.Random(graine)
    poids = [1 / (rang + 1) for rang in range(len(VOCABULAIRE))]
    mots = rng.choices(VOCABULAIRE, weights=poids, k=n)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(mots) + "\n")
    return chemin


def dupliquer(source, destination, m):
    """Crée un fichier contenant m copies successives du fichier source (m x N lignes)."""
    with open(source, "rb") as f:
        contenu = f.read()
    with open(destination, "wb") as f:
        for _ in range(m):
            f.write(contenu)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=10_000, help="nombre de lignes du fichier de base")
    parser.add_argument("--m", type=int, nargs="+", default=[1, 10, 100], help="facteurs de duplication")
    parser.add_argument("--out", default="data", help="dossier de sortie")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    base = generer_base(os.path.join(args.out, f"mots_N{args.n}.txt"), args.n, args.seed)
    print(f"base : {base}")
    for m in args.m:
        dest = dupliquer(base, os.path.join(args.out, f"mots_N{args.n}_m{m}.txt"), m)
        print(f"m={m:>6} -> {dest} ({os.path.getsize(dest) / 1e6:.2f} Mo, {args.n * m} lignes)")


if __name__ == "__main__":
    main()
