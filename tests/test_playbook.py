"""
Tests d'infrastructure pour le playbook Ansible
Tests avec Testinfra
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
    """Retourne le chemin absolu du projet"""
    return host.run("pwd").stdout.strip()


class TestCLIScript:
    """Tests du script CLI"""
    
    def test_cli_script_exists(self, host):
        """Test : Le script CLI doit exister"""
        assert host.file("src/check_port_cli.py").exists
    
    def test_cli_script_executable(self, host):
        """Test : Le script CLI doit être exécutable (ou exécutable via python)"""
        result = host.run("python3 src/check_port_cli.py")
        assert "Usage:" in result.stdout or "fichier" in result.stdout
    
    def test_cli_with_valid_stats(self, host, project_root):
        """Test : Le CLI doit retourner can_restart=true avec des stats OK"""
        cmd = host.run(f"python3 {project_root}/src/check_port_cli.py {project_root}/fixtures/stats_ok.txt")
        
        assert cmd.rc == 0
        result = json.loads(cmd.stdout)
        assert result["can_restart"] is True
        assert result["pon_power"] == "GOOD"
        assert result["ratio"] >= 95.0
    
    def test_cli_with_pon_fail(self, host, project_root):
        """Test : Le CLI doit retourner can_restart=false avec PON FAIL"""
        cmd = host.run(f"python3 {project_root}/src/check_port_cli.py {project_root}/fixtures/stats_pon_fail.txt")
        
        assert cmd.rc == 1
        result = json.loads(cmd.stdout)
        assert result["can_restart"] is False
        assert "PON Power FAIL" in result["message"]
    
    def test_cli_with_low_ratio(self, host, project_root):
        """Test : Le CLI doit retourner can_restart=false avec ratio bas"""
        cmd = host.run(f"python3 {project_root}/src/check_port_cli.py {project_root}/fixtures/stats_ratio_low.txt")
        
        assert cmd.rc == 1
        result = json.loads(cmd.stdout)
        assert result["can_restart"] is False
        assert "Ratio" in result["message"]


class TestAnsiblePlaybook:
    """Tests du playbook Ansible"""
    
    def test_playbook_exists(self, host):
        """Test : Le playbook doit exister"""
        playbook = host.file("playbooks/restart_port.yml")
        assert playbook.exists
        assert playbook.is_file
    
    def test_playbook_syntax(self, host):
        """Test : Le playbook doit avoir une syntaxe valide"""
        cmd = host.run("ansible-playbook --syntax-check playbooks/restart_port.yml")
        assert cmd.rc == 0
    
    def test_playbook_execution_ok(self, host):
        """Test : Exécution réelle avec des stats OK"""
        cmd = host.run(
            "ansible-playbook playbooks/restart_port.yml "
            "-e 'stats_file=fixtures/stats_ok.txt' "
            "-e 'olt=test-olt' "
            "-e 'olt_port=1/1/1' "
            "-e 'skip_restart=true'"
        )
        
        # Devrait réussir
        assert cmd.rc == 0, f"Playbook failed: {cmd.stdout}"
        assert "PON-Power: GOOD" in cmd.stdout
    
    def test_playbook_execution_blocked(self, host):
        """Test : Exécution réelle avec des stats bloquantes"""
        cmd = host.run(
            "ansible-playbook playbooks/restart_port.yml "
            "-e 'stats_file=fixtures/stats_pon_fail.txt' "
            "-e 'olt=test-olt' "
            "-e 'olt_port=1/1/1' "
            "-e 'skip_restart=true'"
        )
        
        # Le playbook doit échouer
        assert cmd.rc != 0
        assert "PON Power FAIL" in cmd.stdout or "PON-Power: FAIL" in cmd.stdout


class TestPlaybookExecution:
    """Tests d'exécution complète du playbook"""
    
    @pytest.fixture
    def mock_restart_script(self, host):
        """Crée un faux script de redémarrage"""
        script_path = "/tmp/mock_oltchiprzt.pl"
        host.run(f"""cat > {script_path} << 'EOF'
#!/bin/bash
echo "Port redemarr e: OLT=$1 PORT=$2"
exit 0
EOF""")
        host.run(f"chmod +x {script_path}")
        
        yield script_path
        
        host.run(f"rm -f {script_path}")
    
    def test_full_execution_with_mock(self, host, mock_restart_script, project_root):
        """Test : Exécution complète avec un mock"""
        
        # Créer un playbook de test
        test_playbook = "/tmp/test_restart.yml"
        host.run(f"""cat > {test_playbook} << 'EOF'
---
- name: Test redemarrage port
  hosts: localhost
  gather_facts: no
  
  vars:
    project_root: "{project_root}"
  
  tasks:
    - name: Construire chemin absolu
      set_fact:
        stats_abs: "{{{{ project_root }}}}/{{{{ stats_file }}}}"
    
    - name: Verification
      command: "python3 {{{{ project_root }}}}/src/check_port_cli.py {{{{ stats_abs }}}}"
      register: check
      ignore_errors: yes
      changed_when: false

    - name: Parse resultat
      set_fact:
        result: "{{{{ check.stdout | from_json }}}}"
      when: check.stdout is defined

    - name: Arret si bloque
      meta: end_play
      when: not result.can_restart

    - name: Mock redemarrage
      command: "{mock_restart_script} {{{{ olt }}}} {{{{ olt_port }}}}"
      register: restart

    - name: Afficher resultat
      debug:
        msg: "Redemarrage OK"
EOF""")
        
        cmd = host.run(
            f"ansible-playbook {test_playbook} "
            "-e 'stats_file=fixtures/stats_ok.txt' "
            "-e 'olt=test-olt' "
            "-e 'olt_port=1/1/1'"
        )
        
        assert cmd.rc == 0, f"Playbook failed: {cmd.stdout}"
        assert "Redemarrage OK" in cmd.stdout
        
        host.run(f"rm -f {test_playbook}")