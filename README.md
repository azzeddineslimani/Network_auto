# Network_auto
Context 1: Restart OLT Port based on data in the olt_dig_output.txt

# Automatisation de redémarrage de ports OLT

Outil d'automatisation pour vérifier et redémarrer les ports OLT selon des critères métier stricts.

## Vue d'ensemble

Ce projet automatise la décision de redémarrage d'un port OLT en vérifiant trois conditions critiques :

1. **PON-Power** doit être à l'état GOOD
2. **Ratio ACK/REQ** doit être supérieur ou égal à 95%
3. **Slice** doit être à l'état ONLINE

Si l'une de ces conditions n'est pas remplie, le redémarrage est bloqué avec un message explicite.

## Architecture

### Décisions techniques principales

**DÉCISION 1 : TDD strict**
- Les tests ont été écrits AVANT le code
- Garantit la fiabilité et la maintenabilité du code
- 26 tests couvrent tous les cas d'usage

**DÉCISION 2 : Séparation des responsabilités**
- `src/port_checker.py` : Logique métier pure (parsing et validation)
- `src/check_port_cli.py` : Interface CLI pour Ansible
- `playbooks/` : Playbooks Ansible pour l'orchestration
- `roles/` : Rôle Ansible standalone et portable

**DÉCISION 3 : Utilisation de regex uniquement**
- Pas de dépendances externes (pas de Pandas)
- Lecture ligne par ligne pour optimiser la mémoire
- Suffisant pour le format de fichier traité

**DÉCISION 4 : Rôle Ansible standalone**
- Le rôle peut être utilisé indépendamment du reste du projet
- Tous les fichiers nécessaires sont embarqués dans le rôle
- Facilite la distribution et la réutilisation

## Structure du projet
```
.
├── src/
│   ├── port_checker.py          # Module de vérification (source)
│   └── check_port_cli.py        # Script CLI (source)
├── tests/
│   ├── test_port_checker.py     # Tests unitaires (10 tests)
│   └── test_playbook.py         # Tests Ansible (10 tests)
├── playbooks/
│   └── restart_port.yml         # Playbook principal
├── roles/
│   └── olt_port_restart/        # Rôle Ansible standalone
│       ├── tasks/main.yml
│       ├── files/
│       │   ├── port_checker.py  # Copie synchronisée
│       │   └── check_port_cli.py# Copie synchronisée
│       ├── defaults/main.yml
│       ├── meta/main.yml
│       ├── tests/test_role.py   # Tests du rôle (6 tests)
│       └── README.md
├── fixtures/                    # Fichiers de test
│   ├── stats_ok.txt
│   ├── stats_pon_fail.txt
│   └── stats_ratio_low.txt
├── requirements.txt             # Aucune dépendance
└── requirements-dev.txt         # Outils de test
```

## Prérequis

- Python 3.6 ou supérieur
- Ansible 2.9 ou supérieur
- Accès à la commande `oltchiprzt.pl` (pour le redémarrage réel)

## Installation
```bash
# Cloner le projet
git clone <repository>
cd olt-port-automation

# Installer les dépendances de développement (pour les tests)
pip install -r requirements-dev.txt
```

## Format du fichier de statistiques

Le fichier doit respecter ce format :
```
* Stats:
  * Port: NNI-Link UP - PON-Power GOOD
  * Nb clients: 3
  * MpcpPortRegister:  188 REQ - 180 ACK
  * Slice: ONLINE depuis 2025-06-15 09:40:45
```

## Utilisation

### Option 1 : Utiliser le playbook
```bash
ansible-playbook playbooks/restart_port.yml \
  -e "stats_file=/chemin/vers/stats.txt" \
  -e "olt=olt-paris-01" \
  -e "olt_port=1/1/1"
```

### Option 2 : Utiliser le rôle standalone

Créer un playbook qui utilise le rôle :
```yaml
---
- name: Redémarrage de port OLT
  hosts: localhost
  
  roles:
    - role: roles/olt_port_restart
      stats_file: /opt/pon/stats.txt
      olt: olt-paris-01
      olt_port: 1/1/1
```

Exécuter :
```bash
ansible-playbook mon_playbook.yml
```

### Option 3 : Utiliser le script Python directement
```bash
python3 src/check_port_cli.py /chemin/vers/stats.txt
```

Sortie JSON :
```json
{
  "can_restart": true,
  "message": "OK - Toutes les conditions sont remplies",
  "pon_power": "GOOD",
  "ratio": 95.74,
  "ack": 180,
  "req": 188,
  "slice_status": "ONLINE"
}
```

## Variables disponibles

### Playbook et rôle

| Variable | Requis | Description | Exemple |
|----------|--------|-------------|---------|
| `stats_file` | Oui | Chemin vers le fichier de stats | `/opt/pon/stats.txt` |
| `olt` | Oui | Nom ou IP de l'OLT | `olt-paris-01` |
| `olt_port` | Oui | Numéro du port | `1/1/1` |
| `skip_restart` | Non | Ne pas redémarrer (mode test) | `true` ou `false` |

## Tests

Le projet utilise pytest et Testinfra pour les tests.
```bash
# Tests unitaires Python (10 tests)
pytest tests/test_port_checker.py -v

# Tests du playbook Ansible (10 tests)
pytest tests/test_playbook.py -v

# Tests du rôle (6 tests)
pytest roles/olt_port_restart/tests/test_role.py -v

# Tous les tests avec couverture
pytest tests/ roles/olt_port_restart/tests/ -v --cov=src
```

**DÉCISION : Couverture de tests complète**
- 26 tests au total
- Tous les scénarios testés (succès et échecs)
- Tests d'intégration avec Testinfra
- Validation de la syntaxe Ansible

## Développement

### Synchronisation des fichiers

**IMPORTANT : Architecture à double emplacement**

Le code source principal est dans `src/` et doit être copié vers le rôle après chaque modification :
```bash
# Après avoir modifié src/port_checker.py ou src/check_port_cli.py
cp src/port_checker.py roles/olt_port_restart/files/
cp src/check_port_cli.py roles/olt_port_restart/files/
```

**RÈGLE ABSOLUE :**
- Modifiez TOUJOURS le code dans `src/`
- Ne modifiez JAMAIS directement dans `roles/olt_port_restart/files/`
- Copiez vers le rôle après chaque modification
- Lancez les tests après la synchronisation

### Workflow de développement
```bash
# 1. Modifier le code dans src/
vim src/port_checker.py

# 2. Synchroniser vers le rôle
cp src/port_checker.py roles/olt_port_restart/files/
cp src/check_port_cli.py roles/olt_port_restart/files/

# 3. Lancer les tests
pytest tests/ roles/olt_port_restart/tests/ -v

# 4. Committer
git add .
git commit -m "description des changements"
```

## Exemples de sortie

### Redémarrage autorisé
```
TASK [olt_port_restart : Afficher le diagnostic]
ok: [localhost] => {
    "msg": [
        "============================================",
        "DIAGNOSTIC DU PORT OLT",
        "============================================",
        "PON-Power     : GOOD",
        "REQ           : 188",
        "ACK           : 180",
        "Ratio ACK/REQ : 95.74%",
        "Slice         : ONLINE",
        "--------------------------------------------",
        "Décision      : OK - Toutes les conditions sont remplies",
        "============================================"
    ]
}

TASK [olt_port_restart : Confirmer le redémarrage]
ok: [localhost] => {
    "msg": "Port 1/1/1 redémarré avec succès sur OLT olt-paris-01"
}
```

### Redémarrage bloqué
```
TASK [olt_port_restart : Bloquer le redémarrage si conditions non remplies]
fatal: [localhost]: FAILED! => {
    "msg": "Redémarrage bloqué : cause = PON Power FAIL"
}
```

## Distribution du rôle

Le rôle `olt_port_restart` est autonome et peut être distribué indépendamment :
```bash
# Copier le rôle vers un autre projet
cp -r roles/olt_port_restart /chemin/vers/autre/projet/roles/

# Utiliser dans n'importe quel playbook
ansible-playbook playbook.yml
```

## Dépannage

### Le fichier stats n'est pas trouvé

Vérifier que le chemin est absolu ou relatif au bon répertoire.
```bash
# Utiliser un chemin absolu
ansible-playbook playbooks/restart_port.yml \
  -e "stats_file=$(pwd)/fixtures/stats_ok.txt" \
  -e "olt=test" \
  -e "olt_port=1/1/1"
```

### Erreur d'import Python

Vérifier que les fichiers sont bien synchronisés :
```bash
diff src/port_checker.py roles/olt_port_restart/files/port_checker.py
diff src/check_port_cli.py roles/olt_port_restart/files/check_port_cli.py
```

Si différents, resynchroniser :
```bash
cp src/*.py roles/olt_port_restart/files/
```

### Tests qui échouent
```bash
# Nettoyer l'environnement
rm -rf /tmp/olt_automation
rm -rf .pytest_cache

# Relancer les tests
pytest tests/ -v
```

## Décisions de conception

### Pourquoi regex plutôt que Pandas ?

- Fichier simple avec quelques lignes seulement
- Pas besoin de dépendances lourdes
- Lecture ligne par ligne plus économe en mémoire
- Déploiement simplifié (pas d'installation de packages)

### Pourquoi un rôle Ansible standalone ?

- Portabilité : peut être utilisé dans d'autres projets
- Distribution facilitée : un seul dossier à copier
- Tests isolés : le rôle a ses propres tests
- Réutilisabilité : publication possible sur Ansible Galaxy

### Pourquoi TDD (Test-Driven Development) ?

- Qualité du code garantie dès le départ
- Documentation vivante via les tests
- Refactoring sécurisé
- Confiance dans les modifications

### Pourquoi deux emplacements pour le code ?

- `src/` : Code source principal, facile à tester et maintenir
- `roles/olt_port_restart/files/` : Code embarqué pour l'autonomie du rôle
- Compromis entre maintenabilité et portabilité