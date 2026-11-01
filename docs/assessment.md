# Assessment method

The useful output is an evidence-backed explanation of the network, its limitations, and specific next actions. Collecting data alone is not an assessment, and a configuration review is not proof of effective security or coverage.

## 1. Record purpose and constraints

Ask for floors/layout, AP positions, wired/wireless backhaul, ISP plan, important applications, affected rooms/devices/times, and planned changes. Identify which devices are trusted, IoT, or guests, and what printers/speakers/casting/control services must remain reachable.

State the authorized scope. Start read-only. Separately authorize load tests, client-to-client probing, external exposure checks, RF scans, restarts, updates, and configuration changes. Confirm backup/recovery access before changes that can disconnect management.

## 2. Map evidence to questions

| Question | Useful evidence | What it doesn't prove |
| --- | --- | --- |
| What is installed? | Models, versions, topology, supported states | Complete lifecycle/advisory status |
| Are IoT/guests separated? | SSID-to-network mapping, VLANs, isolation, ordered firewall/ACL policies | Actual allowed/blocked communication |
| What is exposed? | WAN rules, forwards, UPnP, VPN, remote-management settings | External reachability from a different network |
| Is IPv6 active and protected? | WAN address/prefix settings, LAN interface type, IPv6 rules | Per-client reachability or absence of link-local IPv6 |
| Is the radio healthy? | Per-band interference, airtime, retries, client signal and rates | Every room's usable service |
| Is backhaul limiting performance? | Negotiated AP/switch link speed, errors, mesh topology | Measured end-to-end capacity |
| Are clients stable? | Time-bounded associations/disconnections and application symptoms | Weeks of reliability from a brief snapshot |

Keep a coverage matrix: **observed**, **not exposed**, **permission denied**, **not tested**, or **not applicable with evidence**. Treat empty successful lists differently from failed endpoints. The collector manifests preserve that distinction.

## 3. Interpret WiFi measurements carefully

- Radio retries are not end-to-end packet loss. Percentages without the observation window and traffic denominator cannot be combined into a household failure rate.
- Average signal across different clients is not a same-client comparison between bands. Weak outliers may be hidden by a reasonable average.
- “Excellent” experience and advertised PHY rates are clues, not measured throughput or proof of good calls.
- Zero utilization/retries may reflect an idle band. A quiet band can still have weak coverage.
- Client counts alone do not establish capacity overload. Devices differ in airtime demand and capability.
- Determine which metric actually covers 24 hours; a traffic-usage column's label does not necessarily apply to adjacent averages.
- One AP can have multiple bands but cannot provide inter-AP roaming. Floors, walls, placement, and client transmit capability matter.

See [UniFi's connectivity guidance](https://help.ui.com/hc/en-us/articles/221029967-Optimizing-WiFi-Connectivity-and-Reducing-Latency) and [WiFi troubleshooting](https://help.ui.com/hc/en-us/articles/32064585817495-WiFi-Troubleshooting-Guide).

## 4. Measure real performance

1. Choose representative clients and locations, including near-AP and problem areas.
2. Record time/timezone, client model, SSID/AP/band, signal, VPN state, background load, and test destination.
3. Obtain a wired baseline if possible, recording the Ethernet link speed.
4. Compare internet performance and, after authorization, local throughput against a wired LAN test server. Do not expose its port to the internet.
5. Use WiFiman Mobile for location-specific latency/speed/signal evidence where supported. Desktop WiFiman does not offer the same survey features. See [Using WiFiman](https://help.ui.com/hc/en-us/articles/205204150-Using-WiFiman).
6. Repeat comparable tests, including a busy period. Record ranges, disconnects, call quality, and latency under load—not just the best speed result.

| Time/timezone | Location | Client | AP/band | Signal | LAN down/up | Internet down/up | Latency/loss destination | Conditions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pending | | | | | | | | |

Use explicit units: dBm, Mbps, ms, and percent. If an inter-AP roam test applies, walk the same route and record transitions. If only one AP exists, mark that test not applicable.

## 5. Turn evidence into changes

For each proposal, state the trigger, expected benefit, compatibility concern, possible interruption, original settings, rollback, and a repeatable retest. Avoid changing channel, width, power, security, and VLAN assignments together; that obscures which change helped.

Example: if a single AP covers several floors and clients remain on weak 6 GHz, propose a reversible trial removing 6 GHz from the primary SSID or disabling it on an affected client where supported. Keep security and other radio settings unchanged, compare the same locations before/after, and restore if worse. This does not increase 5 GHz range or solve missing AP coverage. [Ubiquiti notes client preference for weak 6 GHz](https://help.ui.com/hc/en-us/articles/20407971377815-Getting-Started-with-6-GHz).

For IoT segmentation, inventory all devices rather than only the “IoT” SSID. Same-subnet traffic may not traverse the gateway's routed firewall. Plan VLAN boundaries, approved control/discovery paths, and IPv4/IPv6 policy together. Verify intended access with scoped tests after authorization.

## 6. Finish and maintain the report

Use the [template](../examples/report-template.md). Every finding should reference evidence and distinguish fact from inference. Mark remaining work explicitly. A useful final report includes both risk reduction and functionality/compatibility consequences.

Revoke temporary credentials, stop temporary test servers, and record what changed. No recurring collection or automatic tuning is needed to complete a one-time review. Reassess when cabling, AP count/placement, major firmware, or the household device mix changes.
