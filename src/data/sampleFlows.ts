import { NetworkFlow } from '../types';

export const SAMPLE_FLOWS: NetworkFlow[] = [
  {
    id: 'flow-001',
    timestamp: '2026-10-21 08:24:12',
    fiveTuple: {
      srcIp: '10.0.0.10',
      dstIp: '10.0.1.100',
      srcPort: 54122,
      dstPort: 80,
      protocol: 'TCP'
    },
    features: {
      duration: 3.42,
      max_biat: 0.84,
      mean_fiat: 0.125,
      mean_biat: 0.112,
      flowBytesPerSecond: 48250,
      min_flowiat: 0.00012,
      max_flowiat: 0.92,
      mean_flowiat: 0.086,
      std_flowiat: 0.182,
      flowPktsPerSecond: 85.2,
      totalFwdPackets: 92,
      totalBwdPackets: 184
    },
    predictedClass: 'Web Browsing',
    actualClass: 'Web Browsing',
    confidence: 0.982,
    probabilities: {
      'Web Browsing': 0.982,
      'VoIP': 0.004,
      'Streaming': 0.011,
      'File Transfer': 0.003
    },
    packetCount: 276,
    byteCount: 165015,
    decisionPath: [
      'flowBytesPerSecond <= 125,000 [Pass]',
      'mean_fiat > 0.035s (Not VoIP) [Pass]',
      'duration <= 15.0s (Not long streaming) [Pass]',
      'std_flowiat > 0.08s (Bursty Web Traffic) [Match]'
    ]
  },
  {
    id: 'flow-002',
    timestamp: '2026-10-21 08:24:15',
    fiveTuple: {
      srcIp: '10.0.0.11',
      dstIp: '10.0.1.101',
      srcPort: 16384,
      dstPort: 5060,
      protocol: 'UDP'
    },
    features: {
      duration: 18.60,
      max_biat: 0.024,
      mean_fiat: 0.0201,
      mean_biat: 0.0199,
      flowBytesPerSecond: 10400,
      min_flowiat: 0.0098,
      max_flowiat: 0.025,
      mean_flowiat: 0.0198,
      std_flowiat: 0.0018,
      flowPktsPerSecond: 100.1,
      totalFwdPackets: 930,
      totalBwdPackets: 932
    },
    predictedClass: 'VoIP',
    actualClass: 'VoIP',
    confidence: 0.998,
    probabilities: {
      'Web Browsing': 0.001,
      'VoIP': 0.998,
      'Streaming': 0.001,
      'File Transfer': 0.000
    },
    packetCount: 1862,
    byteCount: 193648,
    decisionPath: [
      'mean_fiat <= 0.028s (Isochronous Voice) [Pass]',
      'std_flowiat <= 0.005s (Ultra-low jitter) [Pass]',
      'flowBytesPerSecond <= 25,000 [Pass]',
      'Class Leaf: VoIP (Purity: 99.8%)'
    ]
  },
  {
    id: 'flow-003',
    timestamp: '2026-10-21 08:24:19',
    fiveTuple: {
      srcIp: '10.0.0.12',
      dstIp: '10.0.1.102',
      srcPort: 49810,
      dstPort: 554,
      protocol: 'TCP'
    },
    features: {
      duration: 45.2,
      max_biat: 0.42,
      mean_fiat: 0.18,
      mean_biat: 0.018,
      flowBytesPerSecond: 285400,
      min_flowiat: 0.00045,
      max_flowiat: 0.45,
      mean_flowiat: 0.022,
      std_flowiat: 0.048,
      flowPktsPerSecond: 240.5,
      totalFwdPackets: 480,
      totalBwdPackets: 10390
    },
    predictedClass: 'Streaming',
    actualClass: 'Streaming',
    confidence: 0.954,
    probabilities: {
      'Web Browsing': 0.022,
      'VoIP': 0.001,
      'Streaming': 0.954,
      'File Transfer': 0.023
    },
    packetCount: 10870,
    byteCount: 12900080,
    decisionPath: [
      'duration > 20.0s [Pass]',
      'mean_biat < 0.05s (Sustained server push) [Pass]',
      'flowBytesPerSecond between 100K and 600K [Pass]',
      'Class Leaf: Streaming (Purity: 95.4%)'
    ]
  },
  {
    id: 'flow-004',
    timestamp: '2026-10-21 08:24:22',
    fiveTuple: {
      srcIp: '10.0.0.13',
      dstIp: '10.0.1.103',
      srcPort: 52190,
      dstPort: 20,
      protocol: 'TCP'
    },
    features: {
      duration: 12.8,
      max_biat: 0.11,
      mean_fiat: 0.008,
      mean_biat: 0.0024,
      flowBytesPerSecond: 985000,
      min_flowiat: 0.00002,
      max_flowiat: 0.12,
      mean_flowiat: 0.0028,
      std_flowiat: 0.0084,
      flowPktsPerSecond: 820.4,
      totalFwdPackets: 2800,
      totalBwdPackets: 7700
    },
    predictedClass: 'File Transfer',
    actualClass: 'File Transfer',
    confidence: 0.978,
    probabilities: {
      'Web Browsing': 0.012,
      'VoIP': 0.000,
      'Streaming': 0.010,
      'File Transfer': 0.978
    },
    packetCount: 10500,
    byteCount: 12608000,
    decisionPath: [
      'flowBytesPerSecond > 650,000 (Bulk Data Transfer) [Pass]',
      'mean_biat <= 0.005s (Saturating link) [Pass]',
      'Class Leaf: File Transfer (Purity: 97.8%)'
    ]
  },
  {
    id: 'flow-005',
    timestamp: '2026-10-21 08:24:28',
    fiveTuple: {
      srcIp: '10.0.0.10',
      dstIp: '10.0.1.100',
      srcPort: 54130,
      dstPort: 443,
      protocol: 'TCP'
    },
    features: {
      duration: 1.85,
      max_biat: 0.45,
      mean_fiat: 0.092,
      mean_biat: 0.088,
      flowBytesPerSecond: 64100,
      min_flowiat: 0.00015,
      max_flowiat: 0.48,
      mean_flowiat: 0.065,
      std_flowiat: 0.112,
      flowPktsPerSecond: 94.0,
      totalFwdPackets: 58,
      totalBwdPackets: 116
    },
    predictedClass: 'Web Browsing',
    actualClass: 'Web Browsing',
    confidence: 0.965,
    probabilities: {
      'Web Browsing': 0.965,
      'VoIP': 0.005,
      'Streaming': 0.018,
      'File Transfer': 0.012
    },
    packetCount: 174,
    byteCount: 118585,
    decisionPath: [
      'duration <= 15.0s [Pass]',
      'flowBytesPerSecond <= 125,000 [Pass]',
      'mean_fiat > 0.035s [Pass]',
      'Class Leaf: Web Browsing (Purity: 96.5%)'
    ]
  },
  {
    id: 'flow-006',
    timestamp: '2026-10-21 08:24:32',
    fiveTuple: {
      srcIp: '10.0.0.11',
      dstIp: '10.0.1.101',
      srcPort: 16386,
      dstPort: 5060,
      protocol: 'UDP'
    },
    features: {
      duration: 24.1,
      max_biat: 0.026,
      mean_fiat: 0.0200,
      mean_biat: 0.0202,
      flowBytesPerSecond: 9800,
      min_flowiat: 0.0095,
      max_flowiat: 0.028,
      mean_flowiat: 0.0199,
      std_flowiat: 0.0019,
      flowPktsPerSecond: 99.8,
      totalFwdPackets: 1202,
      totalBwdPackets: 1205
    },
    predictedClass: 'VoIP',
    actualClass: 'VoIP',
    confidence: 0.995,
    probabilities: {
      'Web Browsing': 0.002,
      'VoIP': 0.995,
      'Streaming': 0.002,
      'File Transfer': 0.001
    },
    packetCount: 2407,
    byteCount: 235886,
    decisionPath: [
      'mean_fiat <= 0.028s [Pass]',
      'std_flowiat <= 0.005s [Pass]',
      'flowBytesPerSecond <= 25,000 [Pass]',
      'Class Leaf: VoIP (Purity: 99.5%)'
    ]
  },
  {
    id: 'flow-007',
    timestamp: '2026-10-21 08:24:39',
    fiveTuple: {
      srcIp: '10.0.0.13',
      dstIp: '10.0.1.103',
      srcPort: 52204,
      dstPort: 21,
      protocol: 'TCP'
    },
    features: {
      duration: 8.4,
      max_biat: 0.08,
      mean_fiat: 0.012,
      mean_biat: 0.0035,
      flowBytesPerSecond: 742000,
      min_flowiat: 0.00004,
      max_flowiat: 0.09,
      mean_flowiat: 0.0041,
      std_flowiat: 0.011,
      flowPktsPerSecond: 620.0,
      totalFwdPackets: 1800,
      totalBwdPackets: 3408
    },
    predictedClass: 'File Transfer',
    actualClass: 'File Transfer',
    confidence: 0.952,
    probabilities: {
      'Web Browsing': 0.018,
      'VoIP': 0.000,
      'Streaming': 0.030,
      'File Transfer': 0.952
    },
    packetCount: 5208,
    byteCount: 6232800,
    decisionPath: [
      'flowBytesPerSecond > 650,000 [Pass]',
      'mean_biat <= 0.005s [Pass]',
      'Class Leaf: File Transfer (Purity: 95.2%)'
    ]
  },
  {
    id: 'flow-008',
    timestamp: '2026-10-21 08:24:45',
    fiveTuple: {
      srcIp: '10.0.0.12',
      dstIp: '10.0.1.102',
      srcPort: 49830,
      dstPort: 8080,
      protocol: 'TCP'
    },
    features: {
      duration: 38.0,
      max_biat: 0.38,
      mean_fiat: 0.16,
      mean_biat: 0.021,
      flowBytesPerSecond: 245000,
      min_flowiat: 0.00038,
      max_flowiat: 0.40,
      mean_flowiat: 0.024,
      std_flowiat: 0.042,
      flowPktsPerSecond: 210.0,
      totalFwdPackets: 390,
      totalBwdPackets: 7590
    },
    predictedClass: 'Streaming',
    actualClass: 'Streaming',
    confidence: 0.932,
    probabilities: {
      'Web Browsing': 0.035,
      'VoIP': 0.002,
      'Streaming': 0.932,
      'File Transfer': 0.031
    },
    packetCount: 7980,
    byteCount: 9310000,
    decisionPath: [
      'duration > 20.0s [Pass]',
      'mean_biat < 0.05s [Pass]',
      'flowBytesPerSecond between 100K and 600K [Pass]',
      'Class Leaf: Streaming (Purity: 93.2%)'
    ]
  }
];
