"""
Vérificateur de port OLT
Analyze les statistiques et détermine si un redémarrage est possible
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Iterator


@dataclass
class PortStatus:
    """Représente l'état d'un port OLT"""

    pon_power: Optional[str] = None
    ack: int = 0
    req: int = 0
    slice_status: Optional[str] = None

    @property
    def ratio(self) -> float:
        """Calcule le ratio ACK/REQ en pourcentage"""
        if self.req == 0:
            return 0.0
        return round((self.ack / self.req) * 100, 2)
    
    @property
    def can_restart(self) -> bool:
        """Détermine si le redémarrage est autorisé"""
        return (
            self.pon_power == "GOOD" and
            self.ratio >= 95.0 and
            self.slice_status == "ONLINE"
        )
    
    @property
    def block_reason(self) -> Optional[str]:
        """Retourne la raison du blocage si applicable"""
        if self.pon_power != "GOOD":
            return "Redémarrage bloqué : cause = PON Power FAIL"
        
        if self.ratio < 95.0:
            return f"Redémarrage bloqué : cause = Ratio ACK/REQ {self.ratio}%"
        if self.slice_status != "ONLINE":
            return f"Redémarrage bloqué : cause = slice {self.slice_status}"
        
        return None
    
    def to_dict(self) -> dict:
        """Convertit l'object en dictionnaire"""
        return {
            "pon_power": self.pon_power,
            "ack": self.ack,
            "req": self.req,
            "ratio": self.ratio,
            "slice_status": self.slice_status,
            "can_restart": self.can_restart,
            "block_reason": self.block_reason
        }
class PortChecker:
    """Vérifie l'état d'un port OLT à partir d'un fichier de stats"""

    def __init__(self, file_path: str | Path):
        """
        Initialise le checker avec un fichier de stats

        Args:
            File_path: Chemin vers le fichier de statistiques

        Raises:
            FileNotfoundError: Si le fichier n'existe pas
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        
    def _read_file(self) -> Iterator[str]:
        """
        Lit le fichier ligne par ligne avec un context manager

        Yields:
            les lignes du fichiers une par une
        """
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                yield line

    def check(self) -> PortStatus:
        """
        Analyse le fichier et retourne l'état du port

        returns:
            Un objet PortStatus avec les données extraites
        """
        status = PortStatus()
        
        #Lire le fichier ligne par ligne
        for line in self._read_file():
            #on cherche PON-Power
            if 'PON-Power' in line:
                match = re.search(r'PON-Power\s+(\w+)', line)
                if match:
                    status.pon_power = match.group(1)

            #on cherche REQ & ACK
            elif 'REQ' in line and 'ACK' in line:
                req_match = re.search(r'(\d+)\s+REQ', line)
                ack_match = re.search(r'(\d+)\s+ACK', line)
                if req_match and ack_match:
                    status.req = int(req_match.group(1))
                    status.ack = int(ack_match.group(1))

            #on cherche Slice status
            elif 'Slice:' in line:
                match = re.search(r'Slice:\s+(\w+)', line)
                if match:
                    status.slice_status = match.group(1)
        return status