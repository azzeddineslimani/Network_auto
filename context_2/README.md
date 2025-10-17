# Système de Surveillance CSV
Context_2
Système automatique de surveillance de dossier avec traitement CSV et alertes.

## Installation
```bash
# Créer le projet
mkdir surveillance-csv
cd surveillance-csv

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install pandas
sudo apt-get install inotify-tools

# Créer requirements.txt
echo "pandas==2.2.0" > requirements.txt
```

## Fichiers nécessaires

1. **traiter.py** - Script Python de traitement
2. **surveiller.sh** - Script Bash de surveillance
3. **test.csv** - Fichier CSV de test
4. **requirements.txt** - Dépendances Python

## Configuration

### Modifier le dossier à surveiller

Ouvrez `surveiller.sh` et modifiez la ligne :
```bash
DOSSIER="/chemin/vers/dossier"
```

### Modifier les seuils d'alerte

Ouvrez `traiter.py` et modifiez :
```python
SEUIL_LATENCE = 200         # ms
SEUIL_PACKET_LOSS = 5       # %
SEUIL_BANDWIDTH_MIN = 10    # Mbps
```

## Utilisation
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Rendre le script exécutable
chmod +x surveiller.sh

# Tester manuellement
python3 traiter.py test.csv

# Lancer la surveillance
./surveiller.sh
```

## Format CSV

Le fichier CSV doit contenir les colonnes suivantes :
```csv
timestamp,bandwidth_mbps,latency_ms,packet_loss
2025-07-02 10:00:00,90,150,0.02
```

**Colonnes obligatoires :**
- timestamp : Date et heure
- bandwidth_mbps : Bande passante en Mbps
- latency_ms : Latence en millisecondes
- packet_loss : Perte de paquets en pourcentage

## Fichiers générés

- **alertes.txt** - Journal de tous les événements et anomalies
- **donnees_propres.csv** - Données nettoyées et filtrées

## Consulter les résultats
```bash
# Voir les logs en temps réel
tail -f alertes.txt

# Voir tous les logs
cat alertes.txt

# Compter les alertes
grep "ALERTE" alertes.txt | wc -l

# Voir les données nettoyées
cat donnees_propres.csv
```

## Détection d'anomalies

Le système détecte automatiquement :

- Latence supérieure à 200ms
- Perte de paquets supérieure à 5%
- Bande passante inférieure à 10 Mbps

## Dépannage

| Problème | Solution |
|----------|----------|
| inotifywait: command not found | sudo apt-get install inotify-tools |
| No module named 'pandas' | pip install pandas (avec venv activé) |
| Permission denied | chmod +x surveiller.sh |
| Script ne détecte pas les fichiers | Vérifier le chemin DOSSIER dans surveiller.sh |

## Arrêt

Pour arrêter la surveillance, appuyez sur `Ctrl + C`

## Structure du projet
```
surveillance-csv/
├── venv/
├── traiter.py
├── surveiller.sh
├── test.csv
├── requirements.txt
├── alertes.txt           (généré)
└── donnees_propres.csv   (généré)
```

## Exemple de sortie
```
[2025-07-02 14:30:22] === DÉBUT ===
[2025-07-02 14:30:22] Fichier lu : 4 lignes
[2025-07-02 14:30:22] Nettoyage : 4 → 4 lignes
[2025-07-02 14:30:22] ALERTE 2025-07-02 10:05:00 : Latence 210ms
[2025-07-02 14:30:22] ALERTE 2025-07-02 10:10:00 : Bande passante 5 Mbps
[2025-07-02 14:30:22] ALERTE 2025-07-02 10:15:00 : Perte 8.5%
[2025-07-02 14:30:22] 3 anomalie(s) détectée(s)
[2025-07-02 14:30:22] Sauvegardé dans donnees_propres.csv
[2025-07-02 14:30:22] === FIN ===
```

## Commandes utiles
```bash
# Activer/désactiver l'environnement virtuel
source venv/bin/activate
deactivate

# Vider les logs
> alertes.txt

# Voir les dernières lignes du log
tail -n 20 alertes.txt

# Chercher un mot spécifique
grep "Latence" alertes.txt
```