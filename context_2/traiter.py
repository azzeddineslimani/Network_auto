#!/usr/bin/env python3
import pandas as pd
import sys
from datetime import datetime

# ========== CONFIGURATION ==========
SEUIL_LATENCE = 200         # ms
SEUIL_PACKET_LOSS = 5       # %
SEUIL_BANDWIDTH_MIN = 10    # Mbps

FICHIER_LOG = "alertes.txt"
FICHIER_CSV = "donnees_propres.csv"


# ========== FONCTIONS ==========

def log(message):
    """Écrit dans le log avec horodatage"""
    heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ligne = f"[{heure}] {message}\n"
    print(ligne.strip())
    
    with open(FICHIER_LOG, "a", encoding="utf-8") as f:
        f.write(ligne)


def lire_csv(fichier):
    """Lit le fichier CSV"""
    try:
        df = pd.read_csv(fichier, skipinitialspace=True)
        log(f"✓ Fichier lu : {len(df)} lignes")
        return df
    except Exception as e:
        log(f"✗ ERREUR lecture : {e}")
        sys.exit(1)


def nettoyer(df):
    """Nettoie les données"""
    avant = len(df)
    
    df = df.drop_duplicates()
    df = df.dropna()
    
    df['bandwidth_mbps'] = pd.to_numeric(df['bandwidth_mbps'], errors='coerce')
    df['latency_ms'] = pd.to_numeric(df['latency_ms'], errors='coerce')
    df['packet_loss'] = pd.to_numeric(df['packet_loss'], errors='coerce')
    
    df = df[(df['bandwidth_mbps'] >= 0) & 
            (df['latency_ms'] >= 0) & 
            (df['packet_loss'] >= 0)]
    
    apres = len(df)
    log(f"✓ Nettoyage : {avant} → {apres} lignes")
    return df


def detecter_anomalies(df):
    """Détecte les anomalies"""
    anomalies = 0
    
    for _, ligne in df.iterrows():
        problemes = []
        
        if ligne['latency_ms'] > SEUIL_LATENCE:
            problemes.append(f"Latence {ligne['latency_ms']}ms")
        
        if ligne['packet_loss'] > SEUIL_PACKET_LOSS:
            problemes.append(f"Perte {ligne['packet_loss']}%")
        
        if ligne['bandwidth_mbps'] < SEUIL_BANDWIDTH_MIN:
            problemes.append(f"Bande passante {ligne['bandwidth_mbps']} Mbps")
        
        if problemes:
            log(f"⚠ ALERTE {ligne['timestamp']} : {', '.join(problemes)}")
            anomalies += 1
    
    if anomalies == 0:
        log("✓ Aucune anomalie")
    else:
        log(f"⚠ {anomalies} anomalie(s) détectée(s)")
    
    return df


def sauvegarder(df):
    """Sauvegarde en CSV"""
    import os
    mode = 'a' if os.path.exists(FICHIER_CSV) else 'w'
    df.to_csv(FICHIER_CSV, mode=mode, header=(mode == 'w'), index=False)
    log(f"✓ Sauvegardé dans {FICHIER_CSV}")


# ========== MAIN ==========

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 traiter.py fichier.csv")
        sys.exit(1)
    
    fichier = sys.argv[1]
    
    log("=== DÉBUT ===")
    df = lire_csv(fichier)
    df = nettoyer(df)
    df = detecter_anomalies(df)
    sauvegarder(df)
    log("=== FIN ===\n")