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