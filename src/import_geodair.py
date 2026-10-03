"""
Import de l'export Geod'air : O3, moyenne journalière, station Talence, 2023.
"""
import pandas as pd

import config as cfg


def charger_geodair() -> pd.DataFrame:
    """
    Lit l'export Geod'air et ne garde que les jours de mesure valides.
    """
    df = pd.read_csv(cfg.FICHIER_GEODAIR, sep=";", encoding="utf-8-sig")

    df = df.rename(columns={"Date de début": "date", "valeur": "O3_ugm3",
                            "nom site": "station"})
    df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d %H:%M:%S").dt.normalize()

    # validité = -1 : taux de saisie trop faible, la valeur (souvent 0.0) est fausse
    invalides = df["validité"] != 1
    print(f"Geod'air : {invalides.sum()} jour(s) invalide(s) exclu(s) "
          f"sur {len(df)} ({', '.join(df.loc[invalides, 'date'].dt.strftime('%d/%m'))})")

    df = df[~invalides]
    return df[["date", "station", "O3_ugm3"]].set_index("date")


def agreger_geodair_par_mois(df: pd.DataFrame) -> pd.DataFrame:
    """
    Moyenne, min et max mensuels de l'O3, sur les jours valides uniquement.
    """
    mensuel = df.resample("MS").agg(
        O3_moy=("O3_ugm3", "mean"),
        O3_min=("O3_ugm3", "min"),
        O3_max=("O3_ugm3", "max"),
        jours_valides=("O3_ugm3", "count"),
    )
    mensuel.index = mensuel.index.strftime("%Y-%m")
    mensuel.index.name = "mois"
    return mensuel.round(1)