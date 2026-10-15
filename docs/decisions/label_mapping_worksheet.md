# FlowSentry Label Mapping Worksheet

**Generated:** 2026-10-13T00:18:47.223343
**Purpose:** Map dataset labels to FlowSentry target classes

## Instructions

1. Review the original labels below (from real dataset files)
2. For each label, decide the target class or DROP:
   - **Web Browsing** (HTTP/HTTPS browsing traffic)
   - **VoIP** (Voice over IP: Skype, Hangouts, etc.)
   - **Streaming** (Video/audio streaming: YouTube, Vimeo, etc.)
   - **File Transfer** (FTP, SFTP, file sharing)
   - **DROP** (exclude this label from training)
3. Fill in the "Target Class" column
4. Update `config/label_mapping.yaml` with your decisions
5. Change `status: unresolved` to `status: approved` in the config

---

## Labels from: TimeBasedFeatures-Dataset-120s-VPN.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| VPN | 5631 | _[FILL IN]_ |
| Non-VPN | 5151 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-15s-VPN.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| VPN | 9793 | _[FILL IN]_ |
| Non-VPN | 8965 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-30s-VPN.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| VPN | 7734 | _[FILL IN]_ |
| Non-VPN | 6917 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-60s-VPN.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| Non-VPN | 8580 | _[FILL IN]_ |
| VPN | 6935 | _[FILL IN]_ |
|  | 1 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-120s-AllinOne.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| BROWSING | 5000 | _[FILL IN]_ |
| P2P | 1813 | _[FILL IN]_ |
| FT | 1340 | _[FILL IN]_ |
| MAIL | 907 | _[FILL IN]_ |
| VOIP | 778 | _[FILL IN]_ |
| CHAT | 591 | _[FILL IN]_ |
| STREAMING | 353 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-120s.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| BROWSING | 2500 | _[FILL IN]_ |
| VPN-BROWSING | 2500 | _[FILL IN]_ |
| P2P | 1000 | _[FILL IN]_ |
| VPN-P2P | 813 | _[FILL IN]_ |
| VPN-MAIL | 722 | _[FILL IN]_ |
| VPN-FT | 716 | _[FILL IN]_ |
| FT | 624 | _[FILL IN]_ |
| VOIP | 392 | _[FILL IN]_ |
| VPN-VOIP | 386 | _[FILL IN]_ |
| VPN-CHAT | 349 | _[FILL IN]_ |
| CHAT | 242 | _[FILL IN]_ |
| STREAMING | 208 | _[FILL IN]_ |
| MAIL | 185 | _[FILL IN]_ |
| VPN-STREAMING | 145 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-15s-AllinOne.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| VOIP | 5097 | _[FILL IN]_ |
| BROWSING | 5000 | _[FILL IN]_ |
| FT | 2950 | _[FILL IN]_ |
| CHAT | 2086 | _[FILL IN]_ |
| P2P | 1928 | _[FILL IN]_ |
| STREAMING | 957 | _[FILL IN]_ |
| MAIL | 740 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-15s.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| VOIP | 2826 | _[FILL IN]_ |
| BROWSING | 2500 | _[FILL IN]_ |
| VPN-BROWSING | 2500 | _[FILL IN]_ |
| VPN-VOIP | 2271 | _[FILL IN]_ |
| VPN-FT | 1932 | _[FILL IN]_ |
| VPN-CHAT | 1196 | _[FILL IN]_ |
| FT | 1018 | _[FILL IN]_ |
| P2P | 1000 | _[FILL IN]_ |
| VPN-P2P | 928 | _[FILL IN]_ |
| CHAT | 890 | _[FILL IN]_ |
| VPN-MAIL | 491 | _[FILL IN]_ |
| STREAMING | 482 | _[FILL IN]_ |
| VPN-STREAMING | 475 | _[FILL IN]_ |
| MAIL | 249 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-30s-AllinOne.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| BROWSING | 5000 | _[FILL IN]_ |
| VOIP | 2737 | _[FILL IN]_ |
| FT | 2119 | _[FILL IN]_ |
| P2P | 1851 | _[FILL IN]_ |
| CHAT | 1375 | _[FILL IN]_ |
| MAIL | 929 | _[FILL IN]_ |
| STREAMING | 640 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-30s.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| BROWSING | 2500 | _[FILL IN]_ |
| VPN-BROWSING | 2500 | _[FILL IN]_ |
| VOIP | 1438 | _[FILL IN]_ |
| VPN-VOIP | 1299 | _[FILL IN]_ |
| VPN-FT | 1158 | _[FILL IN]_ |
| P2P | 1000 | _[FILL IN]_ |
| FT | 961 | _[FILL IN]_ |
| VPN-P2P | 851 | _[FILL IN]_ |
| VPN-MAIL | 848 | _[FILL IN]_ |
| VPN-CHAT | 780 | _[FILL IN]_ |
| CHAT | 595 | _[FILL IN]_ |
| STREAMING | 342 | _[FILL IN]_ |
| VPN-STREAMING | 298 | _[FILL IN]_ |
| MAIL | 81 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-60s-AllinOne.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| BROWSING | 5000 | _[FILL IN]_ |
| VOIP | 3449 | _[FILL IN]_ |
| FT | 2270 | _[FILL IN]_ |
| P2P | 1823 | _[FILL IN]_ |
| CHAT | 1292 | _[FILL IN]_ |
| MAIL | 1232 | _[FILL IN]_ |
| STREAMING | 449 | _[FILL IN]_ |
|  | 1 | _[FILL IN]_ |

## Labels from: TimeBasedFeatures-Dataset-60s.arff (column: class1)

| Original Label | Count | Target Class |
|---|---|---|
| VPN-BROWSING | 2500 | _[FILL IN]_ |
| BROWSING | 2500 | _[FILL IN]_ |
| VOIP | 1829 | _[FILL IN]_ |
| VPN-VOIP | 1620 | _[FILL IN]_ |
| FT | 1372 | _[FILL IN]_ |
| P2P | 1000 | _[FILL IN]_ |
| VPN-FT | 898 | _[FILL IN]_ |
| MAIL | 849 | _[FILL IN]_ |
| VPN-P2P | 823 | _[FILL IN]_ |
| CHAT | 778 | _[FILL IN]_ |
| VPN-CHAT | 514 | _[FILL IN]_ |
| VPN-MAIL | 383 | _[FILL IN]_ |
| STREAMING | 252 | _[FILL IN]_ |
| VPN-STREAMING | 197 | _[FILL IN]_ |
|  | 1 | _[FILL IN]_ |

---

## Summary: All Unique Labels Across All Files

| Original Label | Total Count | Target Class |
|---|---|---|
| VPN | 30093 | _[FILL IN]_ |
| BROWSING | 30000 | _[FILL IN]_ |
| Non-VPN | 29613 | _[FILL IN]_ |
| VOIP | 18546 | _[FILL IN]_ |
| FT | 12654 | _[FILL IN]_ |
| P2P | 11415 | _[FILL IN]_ |
| VPN-BROWSING | 10000 | _[FILL IN]_ |
| CHAT | 7849 | _[FILL IN]_ |
| VPN-VOIP | 5576 | _[FILL IN]_ |
| MAIL | 5172 | _[FILL IN]_ |
| VPN-FT | 4704 | _[FILL IN]_ |
| STREAMING | 3683 | _[FILL IN]_ |
| VPN-P2P | 3415 | _[FILL IN]_ |
| VPN-CHAT | 2839 | _[FILL IN]_ |
| VPN-MAIL | 2444 | _[FILL IN]_ |
| VPN-STREAMING | 1115 | _[FILL IN]_ |
|  | 3 | _[FILL IN]_ |

---

## Next Steps

1. Complete the "Target Class" column above
2. Update `config/label_mapping.yaml` with mappings
3. Set `status: approved` in the config
4. Proceed to CN-004 (Preprocessing)
