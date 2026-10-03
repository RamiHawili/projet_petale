"""Compare deux mesures successives : flux en hausse -> OUVRIR, en baisse -> FERMER."""
import config as cfg


def est_mesure_brute(sf: float) -> bool:
    return sf > cfg.SEUIL_ECHELLE


def decider_commande(sf_avant: float | None, sf_maintenant: float | None) -> str | None:
    """Renvoie "MONTER", "DESCENDRE" ou None (aucune commande)."""
    if sf_avant is None or sf_maintenant is None:
        return None
    # Changement de type de valeur (brute <-> journalière) : pas comparable
    if est_mesure_brute(sf_avant) != est_mesure_brute(sf_maintenant):
        return None

    variation = sf_maintenant - sf_avant
    if est_mesure_brute(sf_maintenant):
        variation = -variation          # mesure brute inversée
        seuil = cfg.SEUIL_BRUT
    else:
        seuil = cfg.SEUIL_JOUR

    if variation > seuil:
        return "MONTER"
    if variation < -seuil:
        return "DESCENDRE"
    return None


if __name__ == "__main__":
    exemples = [(0.3196, 0.3147), (0.2984, 0.3017), (0.2909, 0.2904),
                (0.0286, 0.0450), (0.3100, 0.0350), (0.0120, None)]
    for avant, maintenant in exemples:
        print(f"{avant} -> {str(maintenant):<6} : {decider_commande(avant, maintenant)}")