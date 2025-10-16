#!/usr/bin/env python3
"""
Script CLI pour vérifier l'état d'un port OLT
Version universelle qui fonctionne partout
"""

import sys
import json
from pathlib import Path

# Stratégie d'import intelligente
def import_port_checker():
    """Importe PortChecker depuis le bon endroit selon le contexte"""
    
    # Essai 1 : Import depuis le même dossier (contexte rôle Ansible)
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from port_checker import PortChecker
        return PortChecker
    except ImportError:
        pass
    
    # Essai 2 : Import depuis src/ (contexte développement)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from src.port_checker import PortChecker
        return PortChecker
    except ImportError:
        pass
    
    # Essai 3 : Import absolu (contexte package installé)
    try:
        from src.port_checker import PortChecker
        return PortChecker
    except ImportError:
        print(json.dumps({
            "can_restart": False,
            "message": "Erreur : Impossible d'importer PortChecker"
        }))
        sys.exit(1)

# Import global
PortChecker = import_port_checker()


def main():
    """Point d'entrée du script CLI"""
    
    if len(sys.argv) < 2:
        result = {
            "can_restart": False,
            "message": "Usage: check_port_cli.py <fichier_stats>"
        }
        print(json.dumps(result))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        checker = PortChecker(file_path)
        status = checker.check()
        
        result = {
            "can_restart": status.can_restart,
            "message": status.block_reason or "OK - Toutes les conditions sont remplies",
            "pon_power": status.pon_power,
            "ratio": status.ratio,
            "ack": status.ack,
            "req": status.req,
            "slice_status": status.slice_status
        }
        
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if status.can_restart else 1)
        
    except FileNotFoundError as e:
        result = {
            "can_restart": False,
            "message": f"Erreur : {str(e)}"
        }
        print(json.dumps(result))
        sys.exit(1)
    except Exception as e:
        result = {
            "can_restart": False,
            "message": f"Erreur inattendue : {str(e)}"
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == "__main__":
    main()