"""
Import et nettoyage des données de la forêt (arbre n°9, QUPU009).
"""
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # crée l'image sans ouvrir de fenêtre
import matplotlib.pyplot as plt

import config as cfg


def charger_donnees_foret() -> pd.DataFrame:
    """
    Lit l'Excel et renvoie les colonnes utiles, typées, pour l'année choisie.
    """
    # 1. Lecture des 4 colonnes utiles uniquement
    df = pd.read_excel(cfg.FICHIER_FORET, sheet_name=cfg.FEUILLE_FORET,
                       usecols=cfg.COLONNES, engine="openpyxl")

    # 2. Conversion des types
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # 3. Valeurs corrompues (=-Inf, #NOM?, NA...) -> case vide (NaN)
    for col in cfg.COLONNES_NUMERIQUES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].where(~df[col].isin([float("inf"), float("-inf")]))

    # 4. Filtre sur l'année et tri chronologique, la date devient l'index
    df = df[df["year"] == cfg.ANNEE].sort_values("date").set_index("date")

    # 5. Vérifie que les 365 jours sont présents (ajoute les jours absents en vide)
    calendrier = pd.date_range(f"{cfg.ANNEE}-01-01", f"{cfg.ANNEE}-12-31", freq="D")
    manquants = calendrier.difference(df.index)
    if len(manquants):
        print(f"[!] {len(manquants)} jour(s) absent(s) du fichier, ajoutés en vide")
    return df.reindex(calendrier).rename_axis("date")

def interpoler(serie: pd.Series, strategie_bords: str = cfg.STRATEGIE_BORDS):
    """
    Interpolation linéaire temporelle + traitement des bords.

    Renvoie la série complétée et un masque True/False des valeurs reconstruites.
    """
    manquant = serie.isna()

    # Trous internes : droite entre la valeur valide d'avant et celle d'après
    s = serie.interpolate(method="time", limit_area="inside")

    # Trous en début ou fin de série (aucun en 2023)
    if strategie_bords == "bfill":
        s = s.bfill().ffill()
    elif strategie_bords == "min":
        s = s.fillna(serie.min())
    elif strategie_bords != "none":
        raise ValueError(f"Stratégie inconnue : {strategie_bords}")
    return s, manquant

def agreger_par_mois(df: pd.DataFrame) -> pd.DataFrame:
    """
    Statistiques mensuelles + delta de SF_diff d'un mois sur l'autre.
    """
    mensuel = df.resample("MS").agg(
        SF_diff_moy=("SF_diff", "mean"),
        SF_diff_min=("SF_diff", "min"),
        SF_diff_max=("SF_diff", "max"),
        AirTC_1_avg_moy=("AirTC_1_avg", "mean"),
        jours_SF_interpoles=("SF_diff_interpole", "sum"),
        jours_T_interpoles=("AirTC_1_avg_interpole", "sum"),
    )
    # Variation de la moyenne de SF_diff par rapport au mois précédent
    mensuel["delta_SF_diff"] = mensuel["SF_diff_moy"].diff()

    # Index lisible : "2023-01" au lieu de "2023-01-01"
    mensuel.index = mensuel.index.strftime("%Y-%m")
    mensuel.index.name = "mois"
    return mensuel.round(5)

def rapport_qualite(df_brut: pd.DataFrame) -> pd.DataFrame:
    """
    Nombre de valeurs corrompues par colonne et par mois (données d'origine).
    """
    rapport = df_brut[cfg.COLONNES_NUMERIQUES].isna().groupby(df_brut.index.month).sum()
    rapport.index.name = "mois"
    rapport.columns = [f"{c}_nb_invalides" for c in rapport.columns]
    return rapport

def figure_controle(df_brut: pd.DataFrame, df: pd.DataFrame) -> None:
    """
    Superpose mesures valides et valeurs interpolées de SF_diff.
    """
    cfg.DOSSIER_FIGURES.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df.index, df["SF_diff"], color="tab:orange", lw=1, label="Série complétée")
    ax.scatter(df_brut.index, df_brut["SF_diff"], s=8, color="tab:blue",
               label="Mesures valides")
    interp = df[df["SF_diff_interpole"]]
    ax.scatter(interp.index, interp["SF_diff"], s=8, color="tab:red", marker="x",
               label="Valeurs interpolées")

    ax.set_title(f"Flux de sève (SF_diff) — arbre n°9 — {cfg.ANNEE}")
    ax.set_ylabel("SF_diff (°C)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(cfg.DOSSIER_FIGURES / f"controle_SF_diff_{cfg.ANNEE}.png", dpi=150)
    plt.close(fig)