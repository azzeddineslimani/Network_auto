#!/bin/bash

DOSSIER="/chemin/vers/dossier"

echo "🔍 Surveillance : $DOSSIER"

inotifywait -m -e create "$DOSSIER" | while read chemin action fichier
do
    if [[ "$fichier" == *.csv ]]; then
        echo "📄 Nouveau : $fichier"
        sleep 2
        python3 traiter.py "$DOSSIER/$fichier"
    fi
done