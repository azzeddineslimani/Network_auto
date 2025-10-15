"""
Tests unitaires pour le vérificateur de port OLT
"""

import pytest
from pathlib import Path
from src.port_checker import PortChecker, PortStatus

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent.parent / "fixtures"

@pytest.fixture
def stats_ok_file(fixtures_dir):
    return fixtures_dir / "stats_ok.txt"

@pytest.fixture
def stats_pon_fail_file(fixtures_dir):
    return fixtures_dir / "stats_pon_fail.txt"

@pytest.fixture
def stats_ratio_low_file(fixtures_dir):
    return fixtures_dir / "stats_ratio_low.txt"

class TestPortChecker:
    """Tests pour la classe PortChecker"""

    def test_init_with_valid_file(self, stats_ok_file):
        """Test : Le checker doir d'initialiser avec un fichier valide"""
        checker = PortChecker(stats_ok_file)
        assert checker.file_path == stats_ok_file
    
    def test_init_with_invalid_file(self):
        """Test : le checker doit lever une exception si le fichier n'existe pas"""
        with pytest.raises(FileNotFoundError):
            PortChecker("/foo/inexistant.txt")
    
    def test_parse_pon_power_good(self, stats_ok_file):
        """Test : doit extraire PON-Power = GOOD"""
        checker = PortChecker(stats_ok_file)
        status = checker.check()
        assert status.pon_power == "GOOD"
    
    def test_parse_pon_power_fail(self, stats_pon_fail_file):
        """Test: Doit extraire PON-Power = FAIL"""
        checker = PortChecker(stats_pon_fail_file)
        status = checker.check()
        assert status.pon_power == "FAIL"

    def test_parse_ack_req_ratio(self, stats_ok_file):
        """Test: Doit calculer le ratio ACK/REQ"""
        Checker = PortChecker(stats_ok_file)
        status = Checker.check()
        assert status.ack == 180
        assert status.req == 188
        assert status.ratio == pytest.approx(95.74, rel=0.01)

    def test_parse_slice_online(self, stats_ok_file):
        """Test: Doit extraire Slice = ONLINE"""
        checker = PortChecker(stats_ok_file)
        status = checker.check()
        assert status.slice_status == "ONLINE"


    def test_can_restart_all_conditions_ok(self, stats_ok_file):
        """Test: Peut redémarer le port si tout est OK"""
        checker = PortChecker(stats_ok_file)
        status = checker.check()
        assert status.can_restart is True
        assert status.block_reason is None

    def test_cannot_restart_pon_fail(self, stats_pon_fail_file):
        """Test : Ne peut pas redémarrer si PON-Power FAIL"""
        checker = PortChecker(stats_pon_fail_file)
        status = checker.check()
        assert status.can_restart is False
        assert "PON Power FAIL" in status.block_reason

    def test_cannot_restart_ratio_low(self, stats_ratio_low_file):
        """Test: Ne pas redémarrer si ratio < 95%"""
        checker = PortChecker(stats_ratio_low_file)
        status = checker.check()
        assert status.can_restart is False
        assert "Ratio" in status.block_reason
        assert status.ratio == 90.0

    def test_read_file_line_by_line(self, stats_ok_file):
        """Test : Doit lire le fichier ligne par ligne avec context manager"""
        checker = PortChecker(stats_ok_file)
        # On regard si la methode _read_file existe et retourne des lignes
        lines = list(checker._read_file())
        assert len(lines) > 0
        assert any("PON-Power" in line for line in lines)

class TestPortStatus:
    """Tests pour la classe PortStatus"""

    def test_port_status_creation(self):
        """Test : Doit créer un objet PortStatus"""
        status = PortStatus(
            pon_power="GOOD",
            ack=180,
            req=188,
            slice_status="ONLINE"
        )
        assert status.pon_power == "GOOD"
        assert status.ratio == pytest.approx(95.74, rel=0.01)

    def test_to_dict(self):
        """Test : doit convertir en disctionnaire"""
        status = PortStatus(
            pon_power="GOOD",
            ack=180,
            req=188,
            slice_status="ONLINE"
        )
        result = status.to_disct()
        assert isinstance(result, dict)
        assert result["pon_power"] == "GOOD"
        assert result["can_restart"] is True