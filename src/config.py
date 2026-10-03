"""Configuration du projet Pétale."""

# --- Données de la forêt (serveur de Julien) --------------------------------------
URL_BASE = "https://julienrat.github.io/api_simulator/data/"
URLS_SERIE = [URL_BASE + f"2023-{mois}.json" for mois in ("07", "08", "09", "10")]
CHAMP_BRUT = "SF_tree_09_Avg"   # flux de sève de l'arbre n°9, toutes les 30 min

# --- Déroulé ----------------------------------------------------------------------
NB_ETATS = 12          # nombre de hauteurs successives du piston
DUREE_TOTALE_S = 60    # durée totale du parcours
ATTENTE_DEPART_S = 3   # temps laissé au piston pour redescendre avant de commencer

BONUS_MONTEE = 40      # degrés ajoutés à chaque phase de montée (0 = désactivé)
PART_AVANT_BONUS = 0.5 # part du temps de l'état passée à la hauteur normale avant le bonus

# --- Hauteurs du piston (angles du servo) -------------------------------------------
ANGLE_BAS = 0          # flux le plus faible
ANGLE_HAUT = 180       # flux le plus fort

# --- Liaison USB avec l'ESP32 ---------------------------------------------------------
PORT_SERIE = "COM3"
VITESSE_SERIE = 115200