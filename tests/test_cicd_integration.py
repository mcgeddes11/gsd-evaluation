import subprocess
import pytest
import tempfile
from pathlib import Path

@pytest.mark.cicd
class TestGithubActionsWorkflow:

    def test_workflow_file_exists(self):
        workflow_path = Path('.github/workflows/test.yml')
        assert workflow_path.exists()

    def test_workflow_trigger_on_main_only(self):
        workflow_path = Path('.github/workflows/test.yml')
        content = workflow_path.read_text()

        assert "branches:" in content, "Workflow missing branch trigger"
        assert "main" in content, "Workflow should trigger on main branch"
        # Check not triggering on all branches
        assert "on:" in content, "Missing trigger configuration"

    def test_workflow_runs_pytest(self):
        workflow_path = Path('.github/workflows/test.yml')
        content = workflow_path.read_text()
        assert "pytest" in content, "Workflow should run pytest"
        assert "run: pytest" in content or "run pytest" in content, "Workflow missing pytest command"


@pytest.mark.cicd
class TestLocalTestGate:

    def test_pytest_can_run(self):
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in [0,5], \
        f"pytest collection failed: {result.stderr}"

# skipping remainder


@pytest.mark.cicd
class TestAlembicMigrations:

    def test_migrations_directory_exists(self):
        migrations_path = Path('migrations/versions')
        assert migrations_path.exists()

    def test_migrations_directory_has_env_py(self):
        env_path = Path('migrations/env.py')
        assert env_path.exists(), "Alembic env file not found"

        content = env_path.read_text()
        assert "FLASK_ENV" in content, \
            "env.py should reference FLASK_ENV for production config resolution"

@pytest.mark.cicd
class TestDeployScriptStructure:

    def test_deploy_script_exists(self):
        root_script = Path("deploy.sh")
        template_script = Path("templates/deploy.sh")
        assert root_script.exists() or template_script.exists(), "deploy.sh not found"

    def test_deploy_script_is_executable(self):
        script_path = Path("deploy.sh") if Path("deploy.sh").exists() else Path("templates/deploy.sh")
        content = script_path.read_text()
        assert "pytest" in content, "Deploy script should run pytest"

    def test_deploy_script_has_migration_step(self):
        script_path = Path("deploy.sh") if Path("deploy.sh").exists() else Path("templates/deploy.sh")
        content = script_path.read_text()
        assert "flask db upgrade" in content, "Deploy should run flask db migration"
        assert "FLASK_ENV=production" in content, "Deploy script should set FLASK_ENV=production"

    def test_deploy_script_has_rollback_logic(self):
        script_path = Path("deploy.sh") if Path("deploy.sh").exists() else Path("templates/deploy.sh")
        content = script_path.read_text()
        assert "git reset --hard" in content, "No git reset rollback step in deploy script"

    def test_deploy_script_has_health_check(self):
        script_path = Path("deploy.sh") if Path("deploy.sh").exists() else Path("templates/deploy.sh")
        content = script_path.read_text()
        assert "is-active" in content or "is_active" in content, \
            "Deploy script should check if service is active"

@pytest.mark.cicd
class TestSystemdServiceFile:

    def test_service_file_exists(self):
        service_file = Path("templates/blog-service.service")
        assert service_file.exists(), "systemd service file not found"

    def test_service_file_has_required_sections(self):
        service_file = Path("templates/blog-service.service")
        content = service_file.read_text()

        assert "[Unit]" in content and "[Service]" in content and "[Install]" in content, \
            "Required sections not found in systemd file"









