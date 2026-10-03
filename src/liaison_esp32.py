"""Liaison USB avec l'ESP32 : envoie OUVRIR / FERMER / STOP."""
import time

import serial

import config as cfg


def connecter_esp32() -> serial.Serial | None:
    """Ouvre le port série SANS redémarrer l'ESP32 (le piston garde sa position)."""
    esp = serial.Serial()
    esp.port = cfg.PORT_SERIE
    esp.baudrate = cfg.VITESSE_SERIE
    esp.timeout = 1
    esp.dtr = False   # ces deux lignes empêchent le redémarrage
    esp.rts = False   # de l'ESP32 à l'ouverture du port
    try:
        esp.open()
    except serial.SerialException as erreur:
        print(f"[!] Impossible d'ouvrir {cfg.PORT_SERIE} : {erreur}")
        print("    Ferme le moniteur série de l'IDE Arduino.")
        return None
    time.sleep(0.5)
    print(f"Connecté à l'ESP32 sur {cfg.PORT_SERIE}")
    return esp


def envoyer_commande(esp: serial.Serial, commande: str, ecoute_s: float = 1.5) -> list[str]:
    """Envoie une commande et renvoie les réponses de l'ESP32."""
    esp.reset_input_buffer()
    esp.write((commande + "\n").encode())
    reponses = []
    fin = time.time() + ecoute_s
    while time.time() < fin:
        ligne = esp.readline().decode(errors="ignore").strip()
        if ligne:
            reponses.append(ligne)
    return reponses


if __name__ == "__main__":
    esp = connecter_esp32()
    if esp:
        for commande in ["MONTER", "DESCENDRE"]:
            print(f"> {commande} : {envoyer_commande(esp, commande)}")
        esp.close()