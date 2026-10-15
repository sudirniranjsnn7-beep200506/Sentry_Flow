"""
tests/conftest.py
-----------------
Pytest configuration for FlowSentry.

Registers custom markers so that tests requiring external resources
(datasets, CICFlowMeter, capture privileges) are clearly labelled
as SKIPPED when those resources are unavailable.

IMPORTANT: A SKIPPED test is NEVER reported as PASSED.
This is enforced by the task verification protocol in AGENTS.md.

Markers:
  requires_dataset       — test needs real data in data/raw/
  requires_cicflowmeter  — test needs CICFlowMeter installed (G-CFM gate)
  requires_capture       — test needs capture driver + privileges (U-13)

TRD §28, NFR-006.
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register FlowSentry's custom pytest markers."""
    config.addinivalue_line(
        "markers",
        (
            "requires_dataset: test requires a real dataset in data/raw/. "
            "Skip when dataset is absent. "
            "Skipped != passed."
        ),
    )
    config.addinivalue_line(
        "markers",
        (
            "requires_cicflowmeter: test requires CICFlowMeter to be installed "
            "and verified (CN-013, G-CFM gate). "
            "Skip when extractor is unavailable. "
            "Skipped != passed."
        ),
    )
    config.addinivalue_line(
        "markers",
        (
            "requires_capture: test requires a capture driver (e.g. Npcap on Windows) "
            "and sufficient privileges for live packet capture (CN-016, U-13). "
            "Skip when privileges or driver are absent. "
            "Skipped != passed."
        ),
    )
