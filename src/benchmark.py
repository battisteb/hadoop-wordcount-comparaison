"""Benchmark des 3 méthodes de comptage de mots sur des fichiers de tailles croissantes.

Pour chaque facteur m, on génère le fichier de m x N lignes, puis on mesure :
  - méthode 1 (Python simple)        : `python src/wordcount_simple.py fichier`
  - méthode 2 (pseudo-MapReduce)     : `python src/wordcount_mapreduce.py fichier`
  - méthode 3 (Hadoop MapReduce)     : job WordCount Java + job Hadoop Streaming (Python)
Les temps Python sont des temps "murs" de processus complets (équivalent de `time python ...`),
avec le pic de mémoire (RSS). On vérifie aussi que les 3 méthodes donnent le même résultat.

Usage :
    python src/benchmark.py --n 10000 --m 1 10 100 1000 --repetitions 3 [--sans-hadoop | --sans-python]
"""
import argparse
import csv
import os
import statistics
import subprocess
import sys
import time

import psutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generer_fichier  # noqa: E402
import wordcount_simple  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RACINE, "src")


def executer_python(script, fichier):
    """Lance un script Python dans un nouveau processus ; renvoie (durée s, pic RSS Mo, sortie)."""
    t0 = time.perf_counter()
    proc = psutil.Popen([sys.executable, os.path.join(SRC, script), fichier],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    pic = 0
    # on échantillonne la mémoire du processus jusqu'à sa fin (la sortie est petite : pas de blocage du pipe)
    while proc.poll() is None:
        try:
            pic = max(pic, proc.memory_info().rss)
        except psutil.Error:
            pass
        time.sleep(0.01)
    out, err = proc.communicate()
    duree = time.perf_counter() - t0
    if proc.returncode != 0:
        raise RuntimeError(err)
    return duree, pic / 1e6, out


def parser_sortie(texte):
    resultat = {}
    for ligne in texte.splitlines():
        mot, nb = ligne.rsplit(" : ", 1)
        resultat[mot] = int(nb)
    return resultat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10_000)
    parser.add_argument("--m", type=int, nargs="+", default=[1, 10, 100, 500, 1000, 2000])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--repetitions-hadoop", type=int, default=1,
                        help="répétitions des jobs Hadoop (chaque job dure ~1 à 2 min)")
    parser.add_argument("--sans-hadoop", action="store_true")
    parser.add_argument("--sans-python", action="store_true")
    parser.add_argument("--out", default=os.path.join(RACINE, "results", "benchmark.csv"))
    args = parser.parse_args()

    data = os.path.join(RACINE, "data")
    os.makedirs(data, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    base = generer_fichier.generer_base(os.path.join(data, f"mots_N{args.n}.txt"), args.n)

    if not args.sans_hadoop:
        import hadoop_runner
        print("Démarrage du cluster Hadoop...", flush=True)
        hadoop_runner.demarrer_cluster()

    lignes = []
    for m in args.m:
        nom = f"mots_N{args.n}_m{m}.txt"
        fichier = generer_fichier.dupliquer(base, os.path.join(data, nom), m)
        taille = os.path.getsize(fichier) / 1e6
        reference = wordcount_simple.compter_occurrences(fichier)
        print(f"\n=== m={m} : {args.n * m} lignes, {taille:.2f} Mo", flush=True)

        methodes_python = [] if args.sans_python else [("python_simple", "wordcount_simple.py"),
                                                       ("pseudo_mapreduce", "wordcount_mapreduce.py")]
        for methode, script in methodes_python:
            durees, pics = [], []
            for _ in range(args.repetitions):
                d, pic, out = executer_python(script, fichier)
                durees.append(d)
                pics.append(pic)
                assert parser_sortie(out) == reference, f"{methode} : résultat incorrect"
            lignes.append(dict(m=m, lignes=args.n * m, taille_mo=round(taille, 3), methode=methode,
                               temps_s=round(statistics.median(durees), 4),
                               temps_min_s=round(min(durees), 4), memoire_mo=round(max(pics), 1),
                               upload_hdfs_s=""))
            print(f"  {methode:<18} {statistics.median(durees):8.3f} s   {max(pics):8.1f} Mo", flush=True)

        if not args.sans_hadoop:
            entree, t_upload = hadoop_runner.envoyer_hdfs(nom)
            for methode, job in [("hadoop_java", hadoop_runner.wordcount_java),
                                 ("hadoop_streaming", hadoop_runner.wordcount_streaming)]:
                durees = []
                for _ in range(args.repetitions_hadoop):
                    resultat, d = job(entree)
                    durees.append(d)
                    assert resultat == reference, f"{methode} : résultat incorrect"
                lignes.append(dict(m=m, lignes=args.n * m, taille_mo=round(taille, 3), methode=methode,
                                   temps_s=round(statistics.median(durees), 4),
                                   temps_min_s=round(min(durees), 4), memoire_mo="",
                                   upload_hdfs_s=round(t_upload, 3)))
                print(f"  {methode:<18} {statistics.median(durees):8.3f} s   (upload HDFS {t_upload:.2f} s)",
                      flush=True)

        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
            w.writeheader()
            w.writerows(lignes)

    print(f"\nRésultats écrits dans {args.out}")


if __name__ == "__main__":
    main()
