"""
Tests d'infrastructure pour le playbook Ansible
Tests avec Testinfra URL https://blog.stephane-robert.info/post/ansible-test-infra-playbook/
"""

import pytest
import json
import testinfra


@pytest.fixture
def host():
    """Fixture pour se connecter en local"""
    return testinfra.get_host("local://")


@pytest.fixture
def project_root(host):
    """Retourne le chemin du projet"""
    cmd = host.run("pwd")
    return cmd.stdout.strip()


class TestCLIScript:
    """Tests du script CLI"""
    
    def test_cli_script_exists(self, host):
        """Test : Le script CLI doit exister"""
        script = host.file("src/check_port_cli.py")
        assert script.exists
        assert script.is_file
    
    def test_cli_script_executable(self, host):
        """Test : Le script CLI doit être exécutable"""
        script = host.file("src/check_port_cli.py")
        assert script.mode & 0o111  # Vérifie les bits d'exécution
    
    def test_cli_with_valid_stats(self, host):
        """Test : Le CLI doit retourner can_restart=true avec des stats OK"""
        cmd = host.run("python3 src/check_port_cli.py fixtures/stats_ok.txt")
        
        assert cmd.rc == 0
        result = json.loads(cmd.stdout)
        assert result["can_restart"] is True
        assert result["pon_power"] == "GOOD"
        assert result["ratio"] >= 95.0
    
    def test_cli_with_pon_fail(self, host):
        """Test : Le CLI doit retourner can_restart=false avec PON FAIL"""
        cmd = host.run("python3 src/check_port_cli.py fixtures/stats_pon_fail.txt")
        
        assert cmd.rc == 1
        result = json.loads(cmd.stdout)
        assert result["can_restart"] is False
        assert "PON Power FAIL" in result["message"]
    
    def test_cli_with_low_ratio(self, host):
        """Test : Le CLI doit retourner can_restart=false avec ratio bas"""
        cmd = host.run("python3 src/check_port_cli.py fixtures/stats_ratio_low.txt")
        
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
    
    def test_playbook_dry_run_ok(self, host):
        """Test : Dry-run avec des stats OK"""
        cmd = host.run(
            "ansible-playbook playbooks/restart_port.yml "
            "--check "
            "-e 'stats_file=fixtures/stats_ok.txt' "
            "-e 'olt=test-olt' "
            "-e 'port=1/1/1' "
            "-e 'skip_restart=true'"
        )
        
        # En mode check, on accepte des warnings
        assert "fatal" not in cmd.stderr.lower()
    
    def test_playbook_dry_run_blocked(self, host):
        """Test : Dry-run avec des stats bloquantes"""
        cmd = host.run(
            "ansible-playbook playbooks/restart_port.yml "
            "--check "
            "-e 'stats_file=fixtures/stats_pon_fail.txt' "
            "-e 'olt=test-olt' "
            "-e 'port=1/1/1' "
            "-e 'skip_restart=true'"
        )
        
        # Le playbook doit s'arrêter avant le redémarrage
        assert "PON Power FAIL" in cmd.stdout or "PON Power FAIL" in cmd.stderr


class TestPlaybookExecution:
    """Tests d'exécution complète du playbook"""
    
    @pytest.fixture
    def mock_restart_script(self, host):
        """Crée un faux script de redémarrage"""
        script_path = "/tmp/mock_oltchiprzt.pl"
        host.run(f"""cat > {script_path} << 'EOF'
#!/bin/bash
echo "Port redémarré : OLT=$1 PORT=$2"
exit 0
EOF""")
        host.run(f"chmod +x {script_path}")
        
        yield script_path
        
        host.run(f"rm -f {script_path}")
    
    def test_full_execution_with_mock(self, host, mock_restart_script):
        """Test : Exécution complète avec un mock"""
        # Créer un playbook de test qui utilise le mock
        test_playbook = "/tmp/test_restart.yml"
        host.run(f"""cat > {test_playbook} << 'EOF'
---
- name: Test redémarrage port
  hosts: localhost
  gather_facts: no
  
  tasks:
    - name: Vérification
      script: "src/check_port_cli.py {{{{ stats_file }}}}"
      register: check
      ignore_errors: yes

    - name: Parse résultat
      set_fact:
        result: "{{{{ check.stdout | from_json }}}}"

    - name: Arrêt si bloqué
      meta: end_play
      when: not result.can_restart

    - name: Mock redémarrage
      command: "{mock_restart_script} {{{{ olt }}}} {{{{ port }}}}"
      register: restart

    - name: Afficher résultat
      debug:
        msg: "Redémarrage OK"
EOF""")
        
        cmd = host.run(
            f"ansible-playbook {test_playbook} "
            "-e 'stats_file=fixtures/stats_ok.txt' "
            "-e 'olt=test-olt' "
            "-e 'port=1/1/1'"
        )
        
        assert cmd.rc == 0
        assert "Port redémarré" in cmd.stdout
        
        host.run(f"rm -f {test_playbook}")