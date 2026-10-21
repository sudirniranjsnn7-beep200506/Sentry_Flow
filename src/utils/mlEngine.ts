import { FlowFeatures, TrafficClass, NetworkFlow, FiveTuple } from '../types';

/**
 * FlowSentry Decision Tree Inference Engine
 * Replicates the production decision logic of model: decision_tree_20261014_011743
 * Uses 9 selected statistical flow features (no payload inspection).
 */
export function classifyFlow(features: FlowFeatures, fiveTuple: FiveTuple): {
  predictedClass: TrafficClass;
  confidence: number;
  probabilities: Record<TrafficClass, number>;
  decisionPath: string[];
} {
  const {
    duration,
    mean_fiat,
    mean_biat,
    max_biat,
    flowBytesPerSecond,
    std_flowiat,
    mean_flowiat
  } = features;

  const decisionPath: string[] = [];
  let probs: Record<TrafficClass, number> = {
    'Web Browsing': 0.05,
    'VoIP': 0.05,
    'Streaming': 0.05,
    'File Transfer': 0.05
  };

  // Branch 1: High Throughput vs Low/Moderate Throughput
  if (flowBytesPerSecond > 500000) {
    decisionPath.push(`flowBytesPerSecond (${(flowBytesPerSecond / 1000).toFixed(1)} KB/s) > 500 KB/s: High-throughput branch`);
    
    if (mean_biat < 0.015) {
      decisionPath.push(`mean_biat (${(mean_biat * 1000).toFixed(2)} ms) < 15ms: Saturating bulk file transfer`);
      probs = { 'File Transfer': 0.97, 'Streaming': 0.02, 'Web Browsing': 0.01, 'VoIP': 0.00 };
    } else {
      decisionPath.push(`mean_biat >= 15ms: High-rate adaptive video chunk or large media asset`);
      if (duration > 25) {
        probs = { 'Streaming': 0.88, 'File Transfer': 0.10, 'Web Browsing': 0.02, 'VoIP': 0.00 };
      } else {
        probs = { 'File Transfer': 0.91, 'Web Browsing': 0.06, 'Streaming': 0.03, 'VoIP': 0.00 };
      }
    }
  } else if (flowBytesPerSecond < 35000 && mean_fiat < 0.035 && std_flowiat < 0.01) {
    // Branch 2: VoIP Signature (Isochronous, low rate, ultra-low jitter ~20ms RTP codec)
    decisionPath.push(`mean_fiat (${(mean_fiat * 1000).toFixed(1)} ms) < 35ms & std_flowiat (${(std_flowiat * 1000).toFixed(1)} ms) < 10ms: Isochronous regular cadence`);
    decisionPath.push(`flowBytesPerSecond (${(flowBytesPerSecond / 1000).toFixed(1)} KB/s) < 35 KB/s: Narrowband audio bitrate`);
    probs = { 'VoIP': 0.99, 'Web Browsing': 0.005, 'Streaming': 0.005, 'File Transfer': 0.00 };
  } else if (duration > 20 && mean_biat < 0.08 && flowBytesPerSecond >= 80000) {
    // Branch 3: Sustained Streaming (Long duration, regular continuous server push)
    decisionPath.push(`duration (${duration.toFixed(1)}s) > 20s: Long-lived persistent connection`);
    decisionPath.push(`mean_biat (${(mean_biat * 1000).toFixed(1)} ms) < 80ms: Continuous server delivery`);
    decisionPath.push(`flowBytesPerSecond (${(flowBytesPerSecond / 1000).toFixed(1)} KB/s) in streaming range`);
    probs = { 'Streaming': 0.93, 'File Transfer': 0.04, 'Web Browsing': 0.025, 'VoIP': 0.005 };
  } else {
    // Branch 4: Web Browsing (Bursty DOM request-response cycles, variable IAT, moderate rates)
    decisionPath.push(`Bursty inter-arrival times (std_flowiat=${(std_flowiat * 1000).toFixed(1)}ms)`);
    decisionPath.push(`duration (${duration.toFixed(1)}s) and rate (${(flowBytesPerSecond / 1000).toFixed(1)} KB/s) match Web HTTP/TLS sessions`);
    probs = { 'Web Browsing': 0.96, 'File Transfer': 0.02, 'Streaming': 0.015, 'VoIP': 0.005 };
  }

  // Find argmax class
  let bestClass: TrafficClass = 'Web Browsing';
  let maxP = -1;
  (Object.keys(probs) as TrafficClass[]).forEach((cls) => {
    if (probs[cls] > maxP) {
      maxP = probs[cls];
      bestClass = cls;
    }
  });

  return {
    predictedClass: bestClass,
    confidence: maxP,
    probabilities: probs,
    decisionPath
  };
}

/**
 * Generate a new synthetic flow for interactive testing
 */
export function generateSyntheticFlow(targetCategory?: TrafficClass): NetworkFlow {
  const categories: TrafficClass[] = ['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'];
  const chosenClass = targetCategory || categories[Math.floor(Math.random() * categories.length)];
  const id = `flow-${Math.floor(100 + Math.random() * 900)}`;
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  let fiveTuple: FiveTuple;
  let features: FlowFeatures;
  let packetCount = 0;
  let byteCount = 0;

  switch (chosenClass) {
    case 'VoIP': {
      fiveTuple = {
        srcIp: '10.0.0.11',
        dstIp: '10.0.1.101',
        srcPort: 16000 + Math.floor(Math.random() * 2000),
        dstPort: 5060,
        protocol: 'UDP'
      };
      const duration = 10 + Math.random() * 30;
      features = {
        duration,
        max_biat: 0.022 + Math.random() * 0.008,
        mean_fiat: 0.0195 + Math.random() * 0.002,
        mean_biat: 0.0198 + Math.random() * 0.002,
        flowBytesPerSecond: 8000 + Math.random() * 5000,
        min_flowiat: 0.009 + Math.random() * 0.002,
        max_flowiat: 0.024 + Math.random() * 0.006,
        mean_flowiat: 0.0199 + Math.random() * 0.001,
        std_flowiat: 0.0015 + Math.random() * 0.0015,
        flowPktsPerSecond: 98 + Math.random() * 6
      };
      packetCount = Math.round(duration * 100);
      byteCount = Math.round(features.flowBytesPerSecond * duration);
      break;
    }

    case 'File Transfer': {
      fiveTuple = {
        srcIp: '10.0.0.13',
        dstIp: '10.0.1.103',
        srcPort: 50000 + Math.floor(Math.random() * 10000),
        dstPort: Math.random() > 0.5 ? 20 : 21,
        protocol: 'TCP'
      };
      const duration = 5 + Math.random() * 25;
      features = {
        duration,
        max_biat: 0.05 + Math.random() * 0.15,
        mean_fiat: 0.005 + Math.random() * 0.01,
        mean_biat: 0.002 + Math.random() * 0.003,
        flowBytesPerSecond: 650000 + Math.random() * 550000,
        min_flowiat: 0.00001 + Math.random() * 0.00005,
        max_flowiat: 0.08 + Math.random() * 0.08,
        mean_flowiat: 0.0025 + Math.random() * 0.002,
        std_flowiat: 0.006 + Math.random() * 0.006,
        flowPktsPerSecond: 600 + Math.random() * 400
      };
      packetCount = Math.round(duration * 750);
      byteCount = Math.round(features.flowBytesPerSecond * duration);
      break;
    }

    case 'Streaming': {
      fiveTuple = {
        srcIp: '10.0.0.12',
        dstIp: '10.0.1.102',
        srcPort: 48000 + Math.floor(Math.random() * 10000),
        dstPort: Math.random() > 0.5 ? 554 : 8080,
        protocol: 'TCP'
      };
      const duration = 25 + Math.random() * 40;
      features = {
        duration,
        max_biat: 0.25 + Math.random() * 0.35,
        mean_fiat: 0.12 + Math.random() * 0.1,
        mean_biat: 0.015 + Math.random() * 0.02,
        flowBytesPerSecond: 180000 + Math.random() * 220000,
        min_flowiat: 0.0002 + Math.random() * 0.0005,
        max_flowiat: 0.35 + Math.random() * 0.2,
        mean_flowiat: 0.02 + Math.random() * 0.01,
        std_flowiat: 0.035 + Math.random() * 0.02,
        flowPktsPerSecond: 180 + Math.random() * 80
      };
      packetCount = Math.round(duration * 220);
      byteCount = Math.round(features.flowBytesPerSecond * duration);
      break;
    }

    case 'Web Browsing':
    default: {
      fiveTuple = {
        srcIp: '10.0.0.10',
        dstIp: '10.0.1.100',
        srcPort: 52000 + Math.floor(Math.random() * 10000),
        dstPort: Math.random() > 0.5 ? 443 : 80,
        protocol: 'TCP'
      };
      const duration = 1.2 + Math.random() * 6.0;
      features = {
        duration,
        max_biat: 0.4 + Math.random() * 0.7,
        mean_fiat: 0.07 + Math.random() * 0.09,
        mean_biat: 0.06 + Math.random() * 0.08,
        flowBytesPerSecond: 35000 + Math.random() * 55000,
        min_flowiat: 0.0001 + Math.random() * 0.0003,
        max_flowiat: 0.5 + Math.random() * 0.6,
        mean_flowiat: 0.05 + Math.random() * 0.05,
        std_flowiat: 0.09 + Math.random() * 0.1,
        flowPktsPerSecond: 70 + Math.random() * 40
      };
      packetCount = Math.round(duration * 85);
      byteCount = Math.round(features.flowBytesPerSecond * duration);
      break;
    }
  }

  const { predictedClass, confidence, probabilities, decisionPath } = classifyFlow(features, fiveTuple);

  return {
    id,
    timestamp: now,
    fiveTuple,
    features,
    predictedClass,
    actualClass: chosenClass,
    confidence,
    probabilities,
    packetCount,
    byteCount,
    decisionPath
  };
}
