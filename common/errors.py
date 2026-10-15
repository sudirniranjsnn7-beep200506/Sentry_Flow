"""
common/errors.py
----------------
Typed exception hierarchy for FlowSentry.

All pipeline components raise from this module so callers can catch
specific failure modes without inspecting error messages.

Every class has a docstring that maps it to the networking or ML concept
it protects, keeping the architecture explainable at viva level.

TRD §26, NFR-009.
"""


class FlowSentryError(Exception):
    """Base class for all FlowSentry typed exceptions."""


class ConfigError(FlowSentryError):
    """Raised when configuration is missing, invalid, or inconsistent.

    Examples: YAML parse failure, missing required key, invalid value type.
    TRD §25, FR-012.
    """


class DatasetError(FlowSentryError):
    """Raised when a dataset file is missing, unreadable, or has an unexpected format.

    Examples: file not found in data/raw/, unrecognised extension, truncated CSV.
    TRD §5, DS-001.
    """


class LabelMappingError(FlowSentryError):
    """Raised when the label mapping cannot be applied safely.

    Conditions that raise this error:
    - config/label_mapping.yaml has status != "approved"   (G-LABEL gate)
    - An original label found in the data has no mapping entry
    - The mapping file is structurally invalid

    Training is refused until the team approves the mapping.
    TRD §6, DS-002, DS-007, AGENTS.md G-LABEL.
    """


class SchemaMismatchError(FlowSentryError):
    """Raised when inference-time feature columns differ from the training schema.

    The networking chain (five-tuple → flow features → ML) requires that the
    feature vector the model sees at inference is produced by identical
    definitions, units, and column names as at training time.

    TRD §9.3, FE-008, ML-009, AGENTS.md G-SCHEMA.
    """


class ExtractorUnavailableError(FlowSentryError):
    """Raised when the flow extractor (CICFlowMeter) cannot be located or verified.

    CICFlowMeter converts PCAP files → bidirectional flow CSVs.
    If it cannot be found or its verify_available() check fails,
    PCAP classification cannot proceed.

    TRD §22, AGENTS.md G-CFM, U-05.
    """


class ExtractionError(FlowSentryError):
    """Raised when flow extraction from a PCAP file fails.

    Examples: CICFlowMeter returns non-zero exit code, output CSV is empty
    (zero flows extracted), output CSV has unexpected format.

    TRD §22, PC-004.
    """


class ModelNotFoundError(FlowSentryError):
    """Raised when a requested model ID does not exist in the registry.

    TRD §20, FR-007.
    """


class RegistryIntegrityError(FlowSentryError):
    """Raised when a registry entry fails its SHA-256 integrity check.

    Indicates that the pipeline.joblib file has been modified or corrupted
    since it was registered. Loading is refused to prevent unsafe inference.

    TRD §20, ML-009.
    """


class CaptureError(FlowSentryError):
    """Raised when live traffic capture cannot proceed.

    Examples: missing Npcap driver on Windows, insufficient privileges,
    unknown interface name, tshark/Scapy not available.

    Should include actionable guidance in the error message.
    TRD §23.2, RT-005, U-13.
    """


class LeakageGuardError(FlowSentryError):
    """Raised when a structural data-leakage guard is triggered.

    Examples:
    - A module that must not access the test set attempts to import
      the test loader (structural import guard)
    - Row-ID overlap detected between train and test splits
    - A transformer is found to have been fitted on test data

    TRD §12, ML-008, AGENTS.md ML rules.
    """
