# Fictional example: one AP covering several floors

**All names and observations here are invented for teaching. This is not the original household report or a claim about your network.**

## Situation

A three-floor house has one AP, with wired AP expansion planned. Clients near the AP work well, but calls fail in an upstairs office. The owner names one SSID `Home-IoT` and another `Home`.

## Evidence and conclusions

| Observation | Supported conclusion | Not established |
| --- | --- | --- |
| Both SSIDs map to the same native LAN; isolation is disabled | The SSID name does not create a separate VLAN boundary | Actual access to every local service |
| Firewall API says zone-based firewall not configured | That API cannot supply this site's legacy rules | Firewall disabled or absent |
| Advanced UI shows allow-established/drop-invalid/drop-other Internet rules | Displayed inbound policy is stateful default deny | External reachability, port forwards, UPnP exceptions |
| Radio table has weak average 6 GHz signal | Measure affected clients and rooms; investigate band choice | All 6 GHz clients are failing or should be moved |
| Near-AP speed is high, office calls fail | A single near-AP speed result does not validate coverage | A particular radio setting caused the failure |

## Proposed next steps

1. Confirm which SSIDs all IoT devices actually use, and list required casting/printer/control access.
2. Review UPnP, port forwards, WAN/LAN IPv6, and administrator access through the console.
3. Compare the same laptop in the office and near the AP, recording band, signal, latency, and task performance.
4. If weak 6 GHz attachment correlates with symptoms, propose a reversible band-choice trial. Record the original setting, make one authorized change, and repeat the same measurements.
5. Design wired AP placement from the layout and survey. Revisit band choices after coverage improves.

No configuration change is justified merely by an SSID name, a missing API endpoint, or one average metric.
