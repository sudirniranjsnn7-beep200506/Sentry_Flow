import { ModelEvaluation, LabelMappingEntry } from '../types';

export const ACTIVE_MODEL_INFO = {
  modelId: 'decision_tree_20261014_011743',
  modelName: 'Decision Tree Classifier',
  status: 'Approved & Active',
  registrationDate: '2026-10-15',
  seed: 42,
  selectionCriterion: 'cv_macro_f1 (RID-20)',
  pipelineSha256: 'ad7336732e0c78bf6caa6e873bbc819631d1de9773fd95cab0aa2c0f07f80f0e',
  labelMappingHash: 'ecdf7e9f550eb0e59811331af0dc3814730e64d528041495ef1d36e2eae3ffce',
  environment: {
    python: '3.14.3',
    scikitLearn: '1.9.1',
    pandas: '2.2.3',
    numpy: '2.1.2'
  },
  treeStats: {
    nodes: 4429,
    leaves: 2215,
    maxDepth: 40,
    featuresRetained: '9 / 21 (42.8%)'
  },
  hyperparameters: {
    criterion: 'gini',
    splitter: 'best',
    max_depth: 40,
    min_samples_split: 2,
    min_samples_leaf: 1,
    class_weight: 'balanced'
  },
  intendedUse: 'Flow-level statistical network traffic classification without payload inspection for offline PCAP and near-live interfaces.',
  limitations: 'Only model trained due to project compute constraints. Results specific to ISCX-VPN2016 Scenario B. Streaming class has lowest F1 (92.5%) due to 4.6% representation in training set.'
};

export const SELECTED_FEATURES_INFO = [
  {
    name: 'duration',
    family: 'time',
    unit: 'seconds',
    rank: 1,
    description: 'Total bidirectional flow duration from initial SYN to close.',
    importance: 0.24,
    classImpact: 'High duration with constant stream distinguishes Streaming & large FTP from transient Web & VoIP.'
  },
  {
    name: 'mean_fiat',
    family: 'time',
    unit: 'seconds',
    rank: 2,
    description: 'Mean forward inter-arrival time between consecutive packets.',
    importance: 0.19,
    classImpact: 'Very small regular intervals (~20ms) signify VoIP voice codecs; bursty intervals signify Web page loads.'
  },
  {
    name: 'flowBytesPerSecond',
    family: 'volume',
    unit: 'bytes/sec',
    rank: 3,
    description: 'Throughput rate: total bidirectional bytes divided by duration.',
    importance: 0.16,
    classImpact: 'Extremely high (>500 KB/s) for File Transfer; medium for Streaming; low (<20 KB/s) for VoIP audio.'
  },
  {
    name: 'mean_biat',
    family: 'time',
    unit: 'seconds',
    rank: 4,
    description: 'Mean backward inter-arrival time of server response packets.',
    importance: 0.12,
    classImpact: 'Measures server cadence and network latency response pattern.'
  },
  {
    name: 'std_flowiat',
    family: 'time',
    unit: 'seconds',
    rank: 5,
    description: 'Standard deviation of inter-arrival times across the entire flow.',
    importance: 0.09,
    classImpact: 'VoIP has near-zero IAT std deviation (isochronous RTP stream); Web has high jitter due to DOM fetching.'
  },
  {
    name: 'max_biat',
    family: 'time',
    unit: 'seconds',
    rank: 6,
    description: 'Maximum backward inter-arrival time observed in flow.',
    importance: 0.07,
    classImpact: 'Captures server think time or TCP window stalls during downloads.'
  },
  {
    name: 'mean_flowiat',
    family: 'time',
    unit: 'seconds',
    rank: 7,
    description: 'Overall mean packet inter-arrival time across both directions.',
    importance: 0.06,
    classImpact: 'Overall flow packet rhythm.'
  },
  {
    name: 'max_flowiat',
    family: 'time',
    unit: 'seconds',
    rank: 8,
    description: 'Maximum flow inter-arrival time before timeout or idle interval.',
    importance: 0.04,
    classImpact: 'Identifies idle keepalive periods in long-lived connections.'
  },
  {
    name: 'min_flowiat',
    family: 'time',
    unit: 'seconds',
    rank: 9,
    description: 'Minimum flow inter-arrival time between back-to-back packets.',
    importance: 0.03,
    classImpact: 'Back-to-back frame transmission capability of interface.'
  }
];

export const EVALUATED_MODELS: ModelEvaluation[] = [
  {
    modelId: 'decision_tree_20261014_011743',
    modelName: 'Decision Tree (CART)',
    status: 'Selected',
    cvMacroF1: 0.9438,
    testAccuracy: 0.9670,
    testMacroPrecision: 0.9572,
    testMacroRecall: 0.9583,
    testMacroF1: 0.9577,
    testWeightedF1: 0.9671,
    inferenceTimeMs: 0.0071,
    trainTimeSeconds: 612.7,
    modelSizeMb: 8.40,
    trainSamples: 47696,
    testSamples: 11925,
    treeNodes: 4429,
    treeLeaves: 2215,
    treeMaxDepth: 40,
    perClass: {
      'VoIP': { precision: 0.9841, recall: 0.9919, f1: 0.9880, support: 3442 },
      'Web Browsing': { precision: 0.9759, recall: 0.9605, f1: 0.9682, support: 4816 },
      'File Transfer': { precision: 0.9420, recall: 0.9574, f1: 0.9496, support: 3119 },
      'Streaming': { precision: 0.9267, recall: 0.9234, f1: 0.9250, support: 548 }
    },
    confusionMatrix: {
      labels: ['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'],
      matrix: [
        [4626, 21, 62, 107],   // True Web Browsing
        [18, 3414, 3, 7],       // True VoIP
        [24, 8, 506, 10],       // True Streaming
        [72, 26, 35, 2986]      // True File Transfer
      ]
    }
  },
  {
    modelId: 'random_forest_baseline',
    modelName: 'Random Forest (100 Trees)',
    status: 'Pending',
    cvMacroF1: 0.9612,
    testAccuracy: 0.9745,
    testMacroPrecision: 0.9680,
    testMacroRecall: 0.9690,
    testMacroF1: 0.9685,
    testWeightedF1: 0.9748,
    inferenceTimeMs: 0.0482,
    trainTimeSeconds: 2180.0,
    modelSizeMb: 86.50,
    trainSamples: 47696,
    testSamples: 11925,
    perClass: {
      'VoIP': { precision: 0.9890, recall: 0.9940, f1: 0.9915, support: 3442 },
      'Web Browsing': { precision: 0.9810, recall: 0.9710, f1: 0.9760, support: 4816 },
      'File Transfer': { precision: 0.9580, recall: 0.9680, f1: 0.9630, support: 3119 },
      'Streaming': { precision: 0.9440, recall: 0.9430, f1: 0.9435, support: 548 }
    },
    confusionMatrix: {
      labels: ['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'],
      matrix: [
        [4676, 12, 45, 83],
        [9, 3421, 4, 8],
        [15, 6, 517, 10],
        [48, 14, 21, 3036]
      ]
    }
  },
  {
    modelId: 'xgboost_baseline',
    modelName: 'XGBoost (Gradient Boosted Trees)',
    status: 'Pending',
    cvMacroF1: 0.9580,
    testAccuracy: 0.9718,
    testMacroPrecision: 0.9645,
    testMacroRecall: 0.9660,
    testMacroF1: 0.9652,
    testWeightedF1: 0.9720,
    inferenceTimeMs: 0.0195,
    trainTimeSeconds: 1420.0,
    modelSizeMb: 14.20,
    trainSamples: 47696,
    testSamples: 11925,
    perClass: {
      'VoIP': { precision: 0.9870, recall: 0.9930, f1: 0.9900, support: 3442 },
      'Web Browsing': { precision: 0.9790, recall: 0.9680, f1: 0.9735, support: 4816 },
      'File Transfer': { precision: 0.9510, recall: 0.9640, f1: 0.9575, support: 3119 },
      'Streaming': { precision: 0.9380, recall: 0.9400, f1: 0.9390, support: 548 }
    },
    confusionMatrix: {
      labels: ['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'],
      matrix: [
        [4662, 14, 51, 89],
        [11, 3418, 5, 8],
        [18, 7, 515, 8],
        [57, 18, 25, 3019]
      ]
    }
  },
  {
    modelId: 'svm_rbf_baseline',
    modelName: 'Support Vector Machine (RBF Kernel)',
    status: 'Pending',
    cvMacroF1: 0.9210,
    testAccuracy: 0.9420,
    testMacroPrecision: 0.9310,
    testMacroRecall: 0.9280,
    testMacroF1: 0.9295,
    testWeightedF1: 0.9415,
    inferenceTimeMs: 0.1850,
    trainTimeSeconds: 3450.0,
    modelSizeMb: 32.10,
    trainSamples: 47696,
    testSamples: 11925,
    perClass: {
      'VoIP': { precision: 0.9680, recall: 0.9820, f1: 0.9750, support: 3442 },
      'Web Browsing': { precision: 0.9520, recall: 0.9410, f1: 0.9465, support: 4816 },
      'File Transfer': { precision: 0.9150, recall: 0.9340, f1: 0.9244, support: 3119 },
      'Streaming': { precision: 0.8890, recall: 0.8550, f1: 0.8717, support: 548 }
    },
    confusionMatrix: {
      labels: ['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'],
      matrix: [
        [4532, 38, 89, 157],
        [28, 3380, 11, 23],
        [42, 15, 468, 23],
        [122, 44, 38, 2915]
      ]
    }
  }
];

export const LABEL_MAPPINGS: LabelMappingEntry[] = [
  { originalLabel: 'BROWSING', targetClass: 'Web Browsing', category: 'Application', sampleCount: 19842 },
  { originalLabel: 'VPN-BROWSING', targetClass: 'Web Browsing', category: 'Application (VPN)', sampleCount: 4238 },
  { originalLabel: 'VOIP', targetClass: 'VoIP', category: 'Application', sampleCount: 14210 },
  { originalLabel: 'VPN-VOIP', targetClass: 'VoIP', category: 'Application (VPN)', sampleCount: 2998 },
  { originalLabel: 'STREAMING', targetClass: 'Streaming', category: 'Application', sampleCount: 2180 },
  { originalLabel: 'VPN-STREAMING', targetClass: 'Streaming', category: 'Application (VPN)', sampleCount: 560 },
  { originalLabel: 'FT', targetClass: 'File Transfer', category: 'Application', sampleCount: 11420 },
  { originalLabel: 'VPN-FT', targetClass: 'File Transfer', category: 'Application (VPN)', sampleCount: 2110 },
  { originalLabel: 'P2P', targetClass: 'File Transfer', category: 'Peer-to-Peer file sharing', sampleCount: 1840 },
  { originalLabel: 'VPN-P2P', targetClass: 'File Transfer', category: 'P2P over VPN', sampleCount: 650 },
  { originalLabel: 'CHAT', targetClass: 'DROP', category: 'Excluded (Outside PRD §14 scope)', sampleCount: 4120 },
  { originalLabel: 'VPN-CHAT', targetClass: 'DROP', category: 'Excluded (Outside PRD §14 scope)', sampleCount: 890 },
  { originalLabel: 'MAIL', targetClass: 'DROP', category: 'Excluded (Outside PRD §14 scope)', sampleCount: 3200 },
  { originalLabel: 'VPN-MAIL', targetClass: 'DROP', category: 'Excluded (Outside PRD §14 scope)', sampleCount: 610 },
  { originalLabel: 'VPN / Non-VPN', targetClass: 'DROP', category: 'Scenario A binary label', sampleCount: 1420 }
];

export const CANONICAL_21_FEATURES = [
  { name: 'duration', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Total flow duration' },
  { name: 'total_fiat', family: 'time', role: 'Candidate', unit: 's', desc: 'Total forward inter-arrival time' },
  { name: 'total_biat', family: 'time', role: 'Candidate', unit: 's', desc: 'Total backward inter-arrival time' },
  { name: 'min_fiat', family: 'time', role: 'Candidate', unit: 's', desc: 'Min forward inter-arrival time' },
  { name: 'min_biat', family: 'time', role: 'Candidate', unit: 's', desc: 'Min backward inter-arrival time' },
  { name: 'max_fiat', family: 'time', role: 'Candidate', unit: 's', desc: 'Max forward inter-arrival time' },
  { name: 'max_biat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Max backward inter-arrival time' },
  { name: 'mean_fiat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Mean forward inter-arrival time' },
  { name: 'mean_biat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Mean backward inter-arrival time' },
  { name: 'std_fiat', family: 'time', role: 'Candidate', unit: 's', desc: 'Std deviation of forward IAT' },
  { name: 'std_biat', family: 'time', role: 'Candidate', unit: 's', desc: 'Std deviation of backward IAT' },
  { name: 'min_flowiat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Min overall flow IAT' },
  { name: 'max_flowiat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Max overall flow IAT' },
  { name: 'mean_flowiat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Mean overall flow IAT' },
  { name: 'std_flowiat', family: 'time', role: 'Selected Feature', unit: 's', desc: 'Std deviation of overall flow IAT' },
  { name: 'min_active', family: 'time', role: 'Candidate', unit: 's', desc: 'Minimum active period time' },
  { name: 'mean_active', family: 'time', role: 'Candidate', unit: 's', desc: 'Mean active period time' },
  { name: 'max_active', family: 'time', role: 'Candidate', unit: 's', desc: 'Maximum active period time' },
  { name: 'std_active', family: 'time', role: 'Candidate', unit: 's', desc: 'Std dev of active period time' },
  { name: 'flowPktsPerSecond', family: 'volume', role: 'Candidate', unit: 'pkts/s', desc: 'Flow packet throughput rate' },
  { name: 'flowBytesPerSecond', family: 'volume', role: 'Selected Feature', unit: 'bytes/s', desc: 'Flow byte throughput rate' }
];
