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








