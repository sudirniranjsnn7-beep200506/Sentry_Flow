"""
flow — flow extraction and feature normalisation.

Provides the FlowExtractor protocol, the CICFlowMeter adapter (subprocess-based),
an optional native Scapy fallback extractor, and the feature normaliser that
converts raw extractor CSV output into the canonical feature table.

Networking concepts: five-tuple (SrcIP, DstIP, SrcPort, DstPort, Protocol),
bidirectional flow, forward/backward direction, flow timeout, IAT statistics.

Implemented at CN-013 (adapter) and CN-014 (normaliser). Placeholder at CN-001.
TRD §2, §8, §9, §22.
"""
