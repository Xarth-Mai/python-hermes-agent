"""Run with PYTHONPATH pointing at the prepared source, or against the installed package"""

import json
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures.thread import _threads_queues
from pathlib import Path
from unittest.mock import patch


with tempfile.TemporaryDirectory(prefix="hermes-package-check-") as tmp:
    root = Path(tmp)
    plugins = root / "plugins"
    plugins.mkdir()
    with patch.dict(os.environ, {
        "HOME": tmp,
        "HERMES_HOME": str(root / ".hermes"),
        "HERMES_BUNDLED_PLUGINS": str(plugins),
        "HERMES_RESTART_DRAIN_TIMEOUT": "",
        "HERMES_CRON_DRAIN_TIMEOUT": "",
        "HERMES_RUNTIME_DIR": "",
    }):
        from tools.daemon_pool import DaemonThreadPoolExecutor
        from hermes_cli.version_info import get_version_info
        from hermes_cli.steward import read_install_stamp
        from pm.paths import repo_root

        version = get_version_info()
        assert version.base_version == "0.22.0", version
        assert version.commit == "e06df9c2eae6901f4c88f464e0ae6e753c0428b8", version
        assert read_install_stamp(repo_root())["updateMechanism"] == "external"

        from hermes_cli import gateway
        from hermes_cli._launchers import _store_python, resolve_store_python
        from cron.scheduler_script import _run_job_script, _script_argv

        # A tool installed for another runtime must not take over the Arch package
        store = root / ".hermes" / "tools"
        managed_python = store / "python-test" / "bin" / "python3"
        managed_python.parent.mkdir(parents=True)
        managed_python.symlink_to(sys.executable)
        (store / "facts.json").write_text(json.dumps({
            "packages": {"python": {"entry": "python-test"}},
        }))
        assert _store_python(store) == managed_python
        for publication in (False, True):
            assert resolve_store_python(repo_root(), publication=publication) is None
            assert resolve_store_python(root / "other-checkout", publication=publication) == managed_python

        scripts = root / ".hermes" / "scripts"
        scripts.mkdir()
        probe = scripts / "package-probe.py"
        probe.write_text("import json, sys, httpx; print(json.dumps({'python': sys.executable, 'httpx': httpx.__version__}))\n")
        argv, overlay, error = _script_argv(probe)
        assert (argv, overlay, error) == ([sys.executable, str(probe)], {}, None)
        success, output = _run_job_script(probe.name)
        assert success, output
        assert json.loads(output)["python"] == sys.executable, output


        initialized = threading.local()
        with DaemonThreadPoolExecutor(
            max_workers=1, initializer=lambda: setattr(initialized, "value", 42)
        ) as pool:
            worker, value = pool.submit(
                lambda: (threading.current_thread(), initialized.value)
            ).result(timeout=10)
            assert value == 42 and worker.daemon
            assert worker not in _threads_queues
            assert pool.submit(threading.current_thread).result(timeout=10) is worker
        subprocess.run([sys.executable, "-c", "\n".join([
            "import threading",
            "from tools.daemon_pool import DaemonThreadPoolExecutor",
            "pool = DaemonThreadPoolExecutor(max_workers=1)",
            "pool.submit(threading.Event().wait)",
            "pool.shutdown(wait=False)",
        ])], check=True, timeout=10)

        for profile, drain, timeout in (("", 0, 70), ("lxxbot", 90, 120)):
            home = root / ".hermes"
            if profile:
                home = home / "profiles" / profile
            home.mkdir(parents=True, exist_ok=True)
            (home / "config.yaml").write_text(
                f"agent:\n  restart_drain_timeout: {drain}\n  cron_drain_timeout: 30\n"
            )
            os.environ["HERMES_HOME"] = str(home)
            with patch.object(
                gateway, "_system_service_identity", return_value=("service", "service", tmp, 1000)
            ):
                for system in (False, True):
                    unit = gateway.generate_systemd_unit(system=system, run_as_user="service")
                    profile_arg = f' "--profile" "{profile}"' if profile else ""
                    assert f'ExecStart="/usr/bin/hermes"{profile_arg} "gateway" "run"\n' in unit
                    assert "VIRTUAL_ENV=" not in unit
                    assert f'Environment="HERMES_HOME={home}"\n' in unit
                    assert f"TimeoutStopSec={timeout}\n" in unit
print("Package checks passed: release identity, external updates, cron execution with residual PM tools, daemon workers, bounded exit, system/user units, profiles, stop budgets")
