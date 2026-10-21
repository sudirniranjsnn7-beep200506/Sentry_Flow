export type TrafficClass = 'Web Browsing' | 'VoIP' | 'Streaming' | 'File Transfer';

export interface FiveTuple {
  srcIp: string;
  dstIp: string;
  srcPort: number;
  dstPort: number;
  protocol: 'TCP' | 'UDP';
}

export interface FlowFeatures {
  // 9 selected features used by active Decision Tree model
  duration: number; // seconds
  max_biat: number; // maximum backward inter-arrival time (s)
  mean_fiat: number; // mean forward inter-arrival time (s)
  mean_biat: number; // mean backward inter-arrival time (s)
  flowBytesPerSecond: number; // throughput in bytes/s
  min_flowiat: number; // minimum flow inter-arrival time (s)
  max_flowiat: number; // maximum flow inter-arrival time (s)
  mean_flowiat: number; // mean flow inter-arrival time (s)
  std_flowiat: number; // standard deviation of flow IAT (s)

  // Additional canonical features from the 21 schema features
  total_fiat?: number;
  total_biat?: number;
  min_fiat?: number;
  min_biat?: number;
  std_fiat?: number;
  std_biat?: number;
  min_active?: number;
  mean_active?: number;
  max_active?: number;
  std_active?: number;
  flowPktsPerSecond?: number;
  totalFwdPackets?: number;
  totalBwdPackets?: number;
}

export interface NetworkFlow {
  id: string;
  timestamp: string;
  fiveTuple: FiveTuple;
  features: FlowFeatures;
  predictedClass: TrafficClass;
  confidence: number; // 0-1
  probabilities: Record<TrafficClass, number>;
  actualClass?: TrafficClass;
  packetCount: number;
  byteCount: number;
  decisionPath?: string[];
}

export interface ModelMetric {
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface ModelEvaluation {
  modelId: string;
  modelName: string;
  status: 'Selected' | 'Evaluated' | 'Pending';
  cvMacroF1: number;
  testAccuracy: number;
  testMacroPrecision: number;
  testMacroRecall: number;
  testMacroF1: number;
  testWeightedF1: number;
  inferenceTimeMs: number;
  trainTimeSeconds: number;
  modelSizeMb: number;
  trainSamples: number;
  testSamples: number;
  treeNodes?: number;
  treeLeaves?: number;
  treeMaxDepth?: number;
  perClass: Record<TrafficClass, ModelMetric>;
  confusionMatrix: {
    labels: TrafficClass[];
    matrix: number[][]; // [true][pred]
  };
}

export interface PacketTracerNode {
  id: string;
  name: string;
  role: 'client' | 'switch' | 'router' | 'server';
  ip?: string;
  port?: number | string;
  service?: string;
  trafficType?: TrafficClass;
  x: number;
  y: number;
}

export interface SimulatedPacket {
  id: string;
  sourceId: string;
  targetId: string;
  progress: number; // 0 to 1
  trafficType: TrafficClass;
  bytes: number;
  protocol: 'TCP' | 'UDP';
  port: number;
  flowId: string;
}

export interface LabelMappingEntry {
  originalLabel: string;
  targetClass: TrafficClass | 'DROP';
  category: string;
  notes?: string;
  sampleCount?: number;
}
