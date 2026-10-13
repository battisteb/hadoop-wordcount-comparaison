"""Méthode 3 : pilotage d'un job WordCount Hadoop MapReduce depuis Python.

Le cluster tourne dans Docker (voir hadoop/docker-compose.yml). Chaque commande
est exécutée dans le conteneur `namenode` via `docker compose exec`.
"""
import os
import subprocess
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOSE = ["docker", "compose", "-f", os.path.join(RACINE, "hadoop", "docker-compose.yml")]
EXAMPLES_JAR = "/opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.4.1.jar"
STREAMING_JAR = "/opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar"


def sh(commande, check=True):
    """Exécute une commande shell dans le conteneur namenode et renvoie stdout."""
    res = subprocess.run(COMPOSE + ["exec", "-T", "namenode", "bash", "-c", commande],
                         capture_output=True, text=True, encoding="utf-8")
    if check and res.returncode != 0:
        raise RuntimeError(f"échec : {commande}\n{res.stderr[-3000:]}")
    return res.stdout


def demarrer_cluster(attente_max=180):
    subprocess.run(COMPOSE + ["up", "-d"], check=True, capture_output=True)
    debut = time.time()
    while time.time() - debut < attente_max:
        try:
            rapport = sh("hdfs dfsadmin -report 2>/dev/null | grep -c 'Live datanodes (1)'", check=False)
            noeuds = sh("yarn node -list 2>/dev/null | grep -c RUNNING", check=False)
            if rapport.strip() == "1" and noeuds.strip() not in ("", "0"):
                sh("hdfs dfsadmin -safemode leave", check=False)
                return True
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError("le cluster Hadoop n'a pas démarré")


def arreter_cluster():
    subprocess.run(COMPOSE + ["down"], check=True, capture_output=True)


def envoyer_hdfs(nom_fichier):
    """Copie data/<nom_fichier> dans HDFS (/input/<nom>/). Renvoie (chemin HDFS, durée)."""
    dossier = f"/input/{os.path.splitext(nom_fichier)[0]}"
    t0 = time.perf_counter()
    sh(f"hdfs dfs -mkdir -p {dossier} && hdfs dfs -put -f /data/{nom_fichier} {dossier}/")
    return dossier, time.perf_counter() - t0


def lire_resultat(sortie):
    """Lit les fichiers part-* d'un dossier de sortie HDFS -> dict mot -> nombre."""
    texte = sh(f"hdfs dfs -cat {sortie}/part-*")
    resultat = {}
    for ligne in texte.splitlines():
        if ligne.strip():
            mot, nb = ligne.split("\t")
            resultat[mot] = int(nb)
    return resultat


def wordcount_java(entree, sortie="/output/java"):
    """Job WordCount Java fourni avec Hadoop (hadoop-mapreduce-examples). Renvoie (dict, durée)."""
    sh(f"hdfs dfs -rm -r -f -skipTrash {sortie}", check=False)
    t0 = time.perf_counter()
    sh(f"hadoop jar {EXAMPLES_JAR} wordcount {entree} {sortie}")
    duree = time.perf_counter() - t0
    return lire_resultat(sortie), duree


def wordcount_streaming(entree, sortie="/output/streaming"):
    """Job Hadoop Streaming utilisant hadoop/mapper.py et hadoop/reducer.py. Renvoie (dict, durée)."""
    sh(f"hdfs dfs -rm -r -f -skipTrash {sortie}", check=False)
    t0 = time.perf_counter()
    sh(f"hadoop jar {STREAMING_JAR} -files /jobs/mapper.py,/jobs/reducer.py "
       f"-mapper 'python3 mapper.py' -reducer 'python3 reducer.py' "
       f"-input {entree} -output {sortie}")
    duree = time.perf_counter() - t0
    return lire_resultat(sortie), duree
