"""Lit la mesure de flux de sève de l'arbre n°9 dans live.json."""
import json
import time
import urllib.request
from urllib.error import URLError

import config as cfg


def lire_mesure() -> tuple[str | None, float | None]:
    """Renvoie (heure de mise à jour, SF_diff). SF_diff = None si invalide."""
    url = f"{cfg.URL_LIVE}?t={int(time.time())}"  # évite une version en cache
    try:
        with urllib.request.urlopen(url, timeout=10) as reponse:
            donnees = json.load(reponse)
    except (URLError, TimeoutError, json.JSONDecodeError) as erreur:
        print(f"[!] Lecture de live.json impossible : {erreur}")
        return None, None

    sf = donnees.get(cfg.CHAMP_SF)
    if not isinstance(sf, (int, float)):  # vide ou texte ("#VALUE!") -> pas de mesure
        sf = None
    return donnees.get("timestamp_local_2026"), sf


if __name__ == "__main__":
    maj, sf = lire_mesure()
    print(f"Mise à jour : {maj}")
    print(f"{cfg.CHAMP_SF} = {sf}")