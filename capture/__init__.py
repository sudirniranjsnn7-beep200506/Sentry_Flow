"""
capture — live traffic capture helpers.

Provides Tshark and Scapy wrappers for writing packets to .pcap files
and rotating PCAP chunks for near-live classification.

Networking concepts: network interfaces, BPF filters, packet capture,
snapshot length (snaplen), chunk rotation.

Implemented at CN-016. Placeholder only at CN-001.
TRD §2, TRD §23.
"""
