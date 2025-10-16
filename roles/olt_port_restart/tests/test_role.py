"""
Tests TDD pour le rôle Ansible olt_port_restart
"""

import pytest
import json
import testinfra
from pathlib import Path


@pytest.fixture
def host():
    """Fixture pour se connecter en local"""
    return testinfra.get_host("local://")


@pytest.fixture
def project_root(host):
    """Retourne le chemin du projet"""
    return host.run("pwd").stdout.strip()


@pytest.fixture
def role_path(project_root):
    """Retourne le chemin du rôle"""
    return f"{project_root}/roles/olt_port_restart"


@pytest.fixture
def fixtures_path(host):
    """Crée les fixtures de test"""
    # Stats OK
    stats_ok = """
* Stats:
  * Port: NNI-Link UP - PON-Power GOOD
  * Nb clients: 3
  * MpcpPortRegister:  188 REQ - 180 ACK
  * Slice: ONLINE depuis 2025-06-15 09:40:45
"""
    
    # Stats PON FAIL
    stats_fail = """
* Stats:
  * Port: NNI-Link UP - PON-Power FAIL
  * Nb clients: 3
  * MpcpPortRegister:  188 REQ - 180 ACK
  * Slice: ONLINE depuis 2025-06-15 09:40:45
"""
    
    # Créer les fichiers
    host.run(f"echo '{stats_ok}' > /tmp/test_stats_ok.txt")
    host.run(f"echo '{stats_fail}' > /tmp/test_stats_fail.txt")
    
    yield {
        "ok": "/tmp/test_stats_ok.txt",
        "fail": "/tmp/test_stats_fail.txt"
    }
    
    # Nettoyer
    host.run("rm -f /tmp/test_stats_*.txt")


class TestRoleStructure:
    """Tests de la structure du rôle"""
    
    def test_role_structure_exists(self, host, role_path):
        """Test : La structure du rôle doit exister"""
        assert host.file(f"{role_path}/tasks/main.yml").exists
        assert host.file(f"{role_path}/defaults/main.yml").exists
        assert host.file(f"{role_path}/meta/main.yml").exists
    
    def test_role_files_exist(self, host, role_path):
        """Test : Les fichiers Python doivent être présents"""
        assert host.file(f"{role_path}/files/port_checker.py").exists
        assert host.file(f"{role_path}/files/check_port_cli.py").exists
    
    def test_meta_syntax(self, host, role_path):
        """Test : Le fichier meta doit être du YAML valide"""
        cmd = host.run(f"python3 -c \"import yaml; yaml.safe_load(open('{role_path}/meta/main.yml'))\"")
        assert cmd.rc == 0


class TestRoleExecution:
    """Tests d'exécution du rôle"""
    
    def test_role_with_stats_ok(self, host, fixtures_path, project_root):
        """Test : Le rôle doit réussir avec des stats OK"""
        playbook = f"""
---
- hosts: localhost
  gather_facts: no
  roles:
    - role: {project_root}/roles/olt_port_restart
      stats_file: /tmp/test_stats_ok.txt
      olt: test-olt
      olt_port: 1/1/1
      skip_restart: true
"""
        host.run(f"echo '{playbook}' > /tmp/test_role_ok.yml")
        
        cmd = host.run("ansible-playbook /tmp/test_role_ok.yml")
        
        assert cmd.rc == 0, f"Playbook failed: {cmd.stderr}"
        assert "PON-Power" in cmd.stdout
        assert "GOOD" in cmd.stdout
        
        host.run("rm -f /tmp/test_role_ok.yml")
    
    def test_role_with_stats_fail(self, host, fixtures_path, project_root):
        """Test : Le rôle doit bloquer avec PON FAIL"""
        playbook = f"""
---
- hosts: localhost
  gather_facts: no
  roles:
    - role: {project_root}/roles/olt_port_restart
      stats_file: /tmp/test_stats_fail.txt
      olt: test-olt
      olt_port: 1/1/1
      skip_restart: true
"""
        host.run(f"echo '{playbook}' > /tmp/test_role_fail.yml")
        
        cmd = host.run("ansible-playbook /tmp/test_role_fail.yml")
        
        assert cmd.rc != 0
        assert "PON Power FAIL" in cmd.stdout or "PON-Power: FAIL" in cmd.stdout
        
        host.run("rm -f /tmp/test_role_fail.yml")
    
    def test_role_without_required_vars(self, host, project_root):
        """Test : Le rôle doit échouer sans variables requises"""
        playbook = f"""
---
- hosts: localhost
  gather_facts: no
  roles:
    - role: {project_root}/roles/olt_port_restart
"""
        host.run(f"echo '{playbook}' > /tmp/test_role_novars.yml")
        
        cmd = host.run("ansible-playbook /tmp/test_role_novars.yml")
        
        assert cmd.rc != 0
        assert "Variables requises" in cmd.stdout or "assertion failed" in cmd.stdout.lower() or "Variables requises" in cmd.stderr
        
        host.run("rm -f /tmp/test_role_novars.yml")
