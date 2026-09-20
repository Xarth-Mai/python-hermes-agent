"""Run with PYTHONPATH pointing at the prepared source, or against the installed package"""

import os
import shlex
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
    }):
        from tools.daemon_pool import DaemonThreadPoolExecutor
        from hermes_cli import gateway

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
            with patch.object(gateway.shutil, "which", return_value="/usr/bin/hermes"), patch.object(
                gateway, "_system_service_identity", return_value=("service", "service", tmp, 1000)
            ):
                for system in (False, True):
                    unit = gateway.generate_systemd_unit(system=system, run_as_user="service")
                    profile_arg = f" --profile {profile}" if profile else ""
                    assert f"ExecStart=/usr/bin/hermes{profile_arg} gateway run\n" in unit
                    assert "VIRTUAL_ENV=" not in unit
                    assert f'Environment="HERMES_HOME={home}"\n' in unit
                    assert f"TimeoutStopSec={timeout}\n" in unit
        with patch.object(gateway.shutil, "which", return_value=None):
            assert gateway._systemd_gateway_entrypoint() == (
                f"{shlex.quote(gateway.get_python_path())} -m hermes_cli.main"
            )
print("Package checks passed: daemon workers, bounded exit, system/user units, profiles, stop budgets")
