"""Tests : les méthodes de comptage donnent des résultats corrects et identiques."""
import os
import subprocess
import sys
from collections import Counter

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))
sys.path.insert(0, os.path.join(RACINE, "hadoop"))

import generer_fichier  # noqa: E402
import wordcount_mapreduce  # noqa: E402
import wordcount_simple  # noqa: E402


@pytest.fixture
def petit_fichier(tmp_path):
    chemin = tmp_path / "mots.txt"
    chemin.write_text("chat\nchien\nchat\narbre\nchat\nchien\n", encoding="utf-8")
    return str(chemin)


def test_simple_petit_exemple(petit_fichier):
    assert wordcount_simple.compter_occurrences(petit_fichier) == {"chat": 3, "chien": 2, "arbre": 1}


def test_mapreduce_petit_exemple(petit_fichier):
    assert wordcount_mapreduce.compter_occurrences(petit_fichier) == {"chat": 3, "chien": 2, "arbre": 1}


def test_etapes_mapreduce():
    assert wordcount_mapreduce.mapper("chat chien\n") == [("chat", 1), ("chien", 1)]
    groupes = wordcount_mapreduce.shuffle([("a", 1), ("b", 1), ("a", 1)])
    assert dict(groupes) == {"a": [1, 1], "b": [1]}
    assert wordcount_mapreduce.reducer(groupes) == {"a": 2, "b": 1}


def test_fichier_vide(tmp_path):
    vide = tmp_path / "vide.txt"
    vide.write_text("", encoding="utf-8")
    assert wordcount_simple.compter_occurrences(str(vide)) == {}
    assert wordcount_mapreduce.compter_occurrences(str(vide)) == {}


def test_generation_et_duplication(tmp_path):
    n, m = 1000, 7
    base = generer_fichier.generer_base(str(tmp_path / "base.txt"), n)
    lignes = open(base, encoding="utf-8").read().splitlines()
    assert len(lignes) == n
    assert all(len(l.split()) == 1 for l in lignes)          # un mot par ligne
    assert len(set(lignes)) < n                               # il y a des répétitions
    gros = generer_fichier.dupliquer(base, str(tmp_path / "gros.txt"), m)
    assert len(open(gros, encoding="utf-8").read().splitlines()) == m * n
    # dupliquer m fois multiplie chaque compteur par m
    c_base = wordcount_simple.compter_occurrences(base)
    c_gros = wordcount_simple.compter_occurrences(gros)
    assert c_gros == {mot: nb * m for mot, nb in c_base.items()}


def test_methodes_identiques_et_conformes_a_counter(tmp_path):
    fichier = generer_fichier.generer_base(str(tmp_path / "f.txt"), 20_000, graine=1)
    attendu = Counter(open(fichier, encoding="utf-8").read().split())
    assert wordcount_simple.compter_occurrences(fichier) == attendu
    assert wordcount_mapreduce.compter_occurrences(fichier) == attendu


def test_mapper_reducer_streaming(tmp_path):
    """Simule Hadoop Streaming en local : cat | mapper | sort | reducer."""
    fichier = generer_fichier.generer_base(str(tmp_path / "f.txt"), 5_000, graine=3)
    texte = open(fichier, encoding="utf-8").read()
    mapper = os.path.join(RACINE, "hadoop", "mapper.py")
    reducer = os.path.join(RACINE, "hadoop", "reducer.py")
    sortie_map = subprocess.run([sys.executable, mapper], input=texte, capture_output=True,
                                text=True, check=True).stdout
    trie = "".join(sorted(sortie_map.splitlines(keepends=True)))   # phase de shuffle/sort
    sortie_red = subprocess.run([sys.executable, reducer], input=trie, capture_output=True,
                                text=True, check=True).stdout
    resultat = {l.split("\t")[0]: int(l.split("\t")[1]) for l in sortie_red.splitlines()}
    assert resultat == Counter(texte.split())
