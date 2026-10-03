"""
Projet Pétale — le piston rejoue le flux de sève de l'arbre n°9.
1. Le piston redescend en position basse.
2. Toute la série (juillet -> octobre 2023) est découpée en NB_ETATS étapes,
   jouées dans l'ordre en DUREE_TOTALE_S secondes. Arrêt : Ctrl+C
"""
import time

import config as cfg
from donnees_foret import telecharger_serie, calculer_etats
from liaison_esp32 import connecter_esp32, envoyer_commande


def jj_mm(date: str) -> str:
    """'2023-07-19' -> '19/07'"""
    return f"{date[8:10]}/{date[5:7]}"


def main() -> None:
    # --- 1. Données de la forêt --------------------------------------------------
    print("Téléchargement des données de la forêt...")
    serie = telecharger_serie()
    if not serie:
        print("Aucune donnée récupérée, le piston ne bouge pas.")
        return
    etats = calculer_etats(serie)
    print(f"{len(serie)} mesures du {jj_mm(serie[0][0])} au {jj_mm(serie[-1][0])} "
          f"-> {len(etats)} états\n")

    # --- 2. Connexion à l'ESP32 --------------------------------------------------
    esp = connecter_esp32()
    if esp is None:
        return

    try:
        # --- 3. Départ toujours en position basse ---------------------------------
        print(f"Retour en position basse ({cfg.ANGLE_BAS} deg)...")
        envoyer_commande(esp, f"POS:{cfg.ANGLE_BAS}", ecoute_s=0.2)
        time.sleep(cfg.ATTENTE_DEPART_S)
        print("Départ !\n")

        # --- 4. Parcours des états dans l'ordre -----------------------------------
        pause = cfg.DUREE_TOTALE_S / len(etats)
        for i, e in enumerate(etats, start=1):
            envoyer_commande(esp, f"POS:{e['angle']}", ecoute_s=0.2)
            print(f"État {i:2d}/{len(etats)} | {jj_mm(e['debut'])} -> {jj_mm(e['fin'])} | "
                  f"SF_diff {e['sf']:.4f} | hauteur {e['angle']:3d} deg")
            time.sleep(max(0, pause - 0.2))

    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        envoyer_commande(esp, "STOP", ecoute_s=0.2)
        esp.close()
        print("Terminé.")


if __name__ == "__main__":
    main()