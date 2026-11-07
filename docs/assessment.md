# Finding what needs changing

Start with a problem you can reproduce: calls dropping upstairs, an IoT device losing contact, or WiFi running much slower than Ethernet. A configuration snapshot helps narrow it down, but you still need to test where the problem happens.

## Describe the house and the problem

Record floors, AP positions, wired or wireless backhaul, ISP plan, affected devices/rooms, and when it happens. Note which devices belong on trusted, IoT, or guest networks, including printers, speakers, and casting devices that need to remain reachable.

Start with reads. Agree on active tests and configuration changes separately. Before a change that could disconnect you, save the original settings and check that you can recover access to the console.

## Collect the relevant data

| Question | Look at | Follow-up needed |
| --- | --- | --- |
| What's installed? | Models, versions, topology, uplink speeds | Check support/advisories for those versions if relevant |
| Are guests and IoT separated? | SSID/network mapping, VLANs, isolation, ordered IPv4/IPv6 rules | Test intended allowed and blocked connections |
| What's exposed? | Port forwards, UPnP, VPN, remote management | Check reachability from another network if needed |
| Is IPv6 in use? | WAN address/prefix, LAN interface type, IPv6 policy | Check client connectivity |
| Why is WiFi unreliable? | Client signal, AP/band, retries, airtime, interference | Repeat tests in affected rooms |
| Is backhaul a bottleneck? | Negotiated link speed, errors, mesh links | Compare against a wired baseline |

For missing data, distinguish **not exposed**, **permission denied**, and **not tested**. A successful empty list is different from a failed endpoint; check the collector manifest. Legacy firewall API errors often need a UI check using the [console map](console-map.md).

## Read WiFi statistics in context

- Retries aren't end-to-end packet loss. Keep the observation window and traffic volume with the number.
- Average signal can hide one weak client. Compare the same device in the same place before judging bands or APs.
- PHY rates and experience scores aren't measured throughput or call quality.
- A quiet or idle band can still have poor coverage. Client counts alone don't show airtime demand.
- Check each metric's time window; a nearby “24 hours” label may apply only to traffic usage.
- One AP can't roam clients to another AP. Placement, walls, floors, and the client's own radio all matter.

## Test in the rooms you use

1. Pick a near-AP location and the problem locations. Use the same client for comparisons.
2. Record time/timezone, client model, AP/band, signal, VPN state, and background traffic.
3. Get an Ethernet baseline, including negotiated link speed.
4. Compare internet tests with local throughput to a wired LAN server, if you've agreed to run one. Keep that server's port off the internet.
5. Repeat at a busy time. Record latency under load, disconnects, and call quality as well as speed.

WiFiman Mobile can help with location-specific measurements where supported; the desktop app has different capabilities. See [Using WiFiman](https://help.ui.com/hc/en-us/articles/205204150-Using-WiFiman).

| Time/location | Client | AP/band | Signal (dBm) | LAN down/up (Mbps) | Internet down/up (Mbps) | Latency/loss and destination | Conditions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

With several APs, walk the same route and record handoffs. Skip roaming tests if there's only one AP.

## Change one thing, then retest

For each proposed change, write down the reason, expected benefit, devices that might break, likely interruption, original value, and rollback. Retest with the same client, location, and workload.

For example, if an affected client sticks to weak 6 GHz across several floors, try disabling that band on the client where supported, or trial an SSID band change. Keep other radio/security settings fixed. Restore the setting if it doesn't help; band selection won't fix missing AP coverage.

For IoT separation, inventory devices across all SSIDs. Two WiFi names can share one LAN, and same-subnet traffic may never reach the gateway firewall. Plan VLANs, discovery/control exceptions, and IPv4/IPv6 rules together, then test both allowed and blocked paths.

Use the [report template](../examples/report-template.md) to record findings and unresolved questions. Keep evidence references with each finding and label guesses as guesses. After changes, check the household devices that depend on discovery or local control. Revisit the setup after moving APs, changing cabling, or making major software changes.
