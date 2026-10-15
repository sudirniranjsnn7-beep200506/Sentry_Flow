"""
scripts/verify_environment.py
-----------------------------
Environment verification script for FlowSentry (Phase 1, CN-001).

Reports:
  - Python version and platform
  - Installed library versions (all required packages)
  - Availability of optional external tools: tshark, java
  - Best-effort capture-privilege check (feeds U-13)

Never fails merely because optional tools are absent;
reports their status clearly so the team can resolve U-13 and U-05.

Saves report text to docs/verification/environment.txt.

Run:
    python scripts/verify_environment.py

TRD §25, FR-011, NFR-004.
"""

from __future__ import annotations

import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "docs" / "verification" / "environment.txt"

# Required package name (PyPI) → import name for fallback version detection
REQUIRED_PACKAGES: list[tuple[str, str]] = [
    ("pandas", "pandas"),
    ("scikit-learn", "sklearn"),
    ("xgboost", "xgboost"),
    ("scapy", "scapy"),
    ("PyYAML", "yaml"),
    ("joblib", "joblib"),
    ("matplotlib", "matplotlib"),
    ("pytest", "pytest"),
]


def check_python() -> dict[str, str]:
    """Collect Python runtime information."""
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "os": platform.system(),
        "architecture": platform.machine(),
    }


def check_packages() -> dict[str, str]:
    """Check whether each required package is installed and report its version."""
    results: dict[str, str] = {}
    for pkg_name, import_name in REQUIRED_PACKAGES:
        try:
            version = importlib.metadata.version(pkg_name)
            results[pkg_name] = f"OK  {version}"
        except importlib.metadata.PackageNotFoundError:
            # Fallback: try importing and reading __version__
            try:
                mod = __import__(import_name)
                ver = getattr(mod, "__version__", "unknown")
                results[pkg_name] = f"OK  {ver}  (via import; pip metadata not found)"
            except ImportError:
                results[pkg_name] = "MISSING — install from requirements.txt"
    return results


def check_external_tool(
    command: str, version_flag: str = "--version"
) -> dict[str, str]:
    """Return path and version info for an external CLI tool.

    Parameters
    ----------
    command:
        Executable name (looked up via PATH).
    version_flag:
        Flag to pass to the command to get its version string.

    Returns
    -------
    dict with keys: available, path, version
    """
    path = shutil.which(command)
    if path is None:
        return {"available": "NO", "path": "not in PATH", "version": "N/A"}
    try:
        result = subprocess.run(
            [command, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Some tools write version to stderr (e.g. java -version)
        output = result.stdout.strip() or result.stderr.strip()
        version_line = output.splitlines()[0] if output else "unknown"
        return {"available": "YES", "path": path, "version": version_line}
    except subprocess.TimeoutExpired:
        return {"available": "TIMEOUT", "path": path, "version": "timed out after 10s"}
    except OSError as exc:
        return {"available": "ERROR", "path": path, "version": str(exc)}


def check_tshark() -> dict[str, str]:
    """Check for tshark (required for live capture at CN-016)."""
    return check_external_tool("tshark", "--version")


def check_java() -> dict[str, str]:
    """Check for java (required if using Java-based CICFlowMeter at CN-013)."""
    return check_external_tool("java", "-version")


def check_capture_privileges() -> dict[str, str]:
    """Best-effort heuristic check for packet-capture privileges.

    This is a heuristic only.  Actual capture is verified at CN-016.
    Feeds U-13 (OS/hardware/capture privileges decision).
    """
    os_name = platform.system()
    if os_name == "Windows":
        # Check for Npcap or WinPcap DLL
        npcap_dll = Path(r"C:\Windows\System32\Npcap\wpcap.dll")
        winpcap_dll = Path(r"C:\Windows\System32\wpcap.dll")
        if npcap_dll.exists():
            return {
                "available": "LIKELY",
                "note": f"Npcap wpcap.dll found at {npcap_dll}",
            }
        elif winpcap_dll.exists():
            return {
                "available": "LIKELY",
                "note": f"WinPcap wpcap.dll found at {winpcap_dll}",
            }
        else:
            return {
                "available": "UNKNOWN",
                "note": (
                    "Neither Npcap nor WinPcap DLL found. "
                    "Install Npcap (https://npcap.com) for live capture. "
                    "Admin privileges will also be required."
                ),
            }
    elif os_name in ("Linux", "Darwin"):
        try:
            if os.geteuid() == 0:  # type: ignore[attr-defined]
                return {"available": "YES", "note": "Running as root"}
        except AttributeError:
            pass
        # Check cap_net_raw on Linux
        try:
            result = subprocess.run(
                ["getcap", sys.executable],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "cap_net_raw" in result.stdout:
                return {
                    "available": "LIKELY",
                    "note": f"cap_net_raw set on {sys.executable}",
                }
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return {
            "available": "UNKNOWN",
            "note": (
                "Not root; cap_net_raw not confirmed. "
                "May need sudo or setcap for live capture."
            ),
        }
    else:
        return {
            "available": "UNKNOWN",
            "note": f"Unrecognised OS: {os_name}. Capture verification deferred to CN-016.",
        }


def format_report(
    python_info: dict[str, str],
    packages: dict[str, str],
    tshark: dict[str, str],
    java: dict[str, str],
    capture: dict[str, str],
) -> str:
    """Format all collected information into a human-readable report string."""
    sep = "=" * 72
    sec = "-" * 72
    lines: list[str] = [
        sep,
        "FlowSentry -- Environment Verification Report  (CN-001)",
        f"Generated : {datetime.now().isoformat()}",
        sep,
        "",
        "-- Python Runtime " + "-" * 54,
    ]
    for k, v in python_info.items():
        lines.append(f"  {k:<30} {v}")

    lines += [
        "",
        "-- Required Python Packages " + "-" * 44,
    ]
    all_ok = True
    for pkg, status in packages.items():
        ok = status.startswith("OK")
        prefix = "  [OK]" if ok else "  [!!]"
        if not ok:
            all_ok = False
        lines.append(f"{prefix} {pkg:<22} {status}")
    status_line = "ALL OK" if all_ok else "ONE OR MORE MISSING -- run: pip install -r requirements.txt"
    lines.append(f"\n  Overall package status: {status_line}")

    lines += [
        "",
        "-- External Tools " + "-" * 54,
        "  (Optional for Phase 1; required for later phases as noted)",
        "",
        "  tshark  (required for live capture, CN-016):",
    ]
    for k, v in tshark.items():
        lines.append(f"    {k:<18} {v}")

    lines += [
        "",
        "  java  (required if using Java CICFlowMeter implementation, CN-013):",
    ]
    for k, v in java.items():
        lines.append(f"    {k:<18} {v}")

    lines += [
        "",
        "-- Capture Privileges " + "-" * 51,
        "  (Best-effort heuristic; verified at CN-016)",
        "",
    ]
    for k, v in capture.items():
        lines.append(f"  {k:<18} {v}")

    lines += [
        "",
        "-- Unresolved Items Surfaced " + "-" * 43,
        "  U-13 : OS / capture privileges -- see 'Capture Privileges' above.",
        "  U-05 : CICFlowMeter -- NOT verified here; verified separately at CN-013.",
        "",
        "  Record findings in: docs/decisions/decisions.md",
        "",
        sep,
    ]
    return "\n".join(lines)


def main() -> None:
    python_info = check_python()
    packages = check_packages()
    tshark = check_tshark()
    java = check_java()
    capture = check_capture_privileges()

    report = format_report(python_info, packages, tshark, java, capture)
    print(report)

    # Save to docs/verification/
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\nReport saved -> {REPORT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
