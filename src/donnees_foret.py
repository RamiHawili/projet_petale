"""
Récupère le flux de sève de l'arbre n°9 sur le serveur de Julien
et le découpe en NB_ETATS hauteurs de piston, dans l'ordre chronologique.
"""
import json
import urllib.request
from urllib.error import URLError

import config as cfg


def telecharger_serie() -> list[tuple[str, float]]:
    """Renvoie toutes les mesures valides [(horodatage, valeur), ...] triées."""
    serie = []
    for url in cfg.URLS_SERIE:
        try:
            with urllib.request.urlopen(url, timeout=30) as reponse:
                lignes = json.load(reponse)
        except (URLError, TimeoutError, json.JSONDecodeError) as erreur:
            print(f"[!] {url} : {erreur}")
            continue
        for ligne in lignes:
            valeur = ligne.get(cfg.CHAMP_BRUT)
            if isinstance(valeur, (int, float)):   # ignore les valeurs invalides
                serie.append((ligne["TIMESTAMP_UTC"], valeur))
    serie.sort()
    return serie


def calculer_etats(serie: list[tuple[str, float]]) -> list[dict]:
    """Découpe la série en NB_ETATS périodes et calcule la hauteur de chacune."""
    # 1. SF_diff de chaque jour = écart entre la valeur max et la valeur min
    jours = {}
    for horodatage, valeur in serie:
        jours.setdefault(horodatage[:10], []).append(valeur)
    sf_jours = [(jour, max(v) - min(v))
                for jour, v in sorted(jours.items()) if len(v) >= 24]  # jours complets

    # 2. Découpage en NB_ETATS périodes, valeur médiane de chaque période
    n = len(sf_jours)
    etats = []
    for i in range(cfg.NB_ETATS):
        groupe = sf_jours[i * n // cfg.NB_ETATS:(i + 1) * n // cfg.NB_ETATS]
        valeurs = sorted(sf for _, sf in groupe)
        etats.append({"debut": groupe[0][0], "fin": groupe[-1][0],
                      "sf": valeurs[len(valeurs) // 2]})

    # 3. Hauteur : période la plus faible = bas, la plus forte = haut
    bas = min(e["sf"] for e in etats)
    haut = max(e["sf"] for e in etats)
    for e in etats:
        ratio = (e["sf"] - bas) / (haut - bas) if haut > bas else 0.5
        e["angle"] = round(cfg.ANGLE_BAS + ratio * (cfg.ANGLE_HAUT - cfg.ANGLE_BAS))
    return etats


if __name__ == "__main__":
    serie = telecharger_serie()
    print(f"{len(serie)} mesures valides")
    for e in calculer_etats(serie):
        print(e)