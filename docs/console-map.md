# Finding your way around the UniFi console

The paths below were observed on **UCG Max / UniFi OS 5.1.34 / Network 10.6.109** during the original investigation. These versions identify a tested layout, not a required or latest release. Follow the labels in your actual interface. Owner/administrator roles, deployment types, and software releases affect available pages.

## The three navigation levels

1. **Site Manager** (`unifi.ui.com`): lists your sites. Select the intended home site before looking for site-specific configuration.
2. **Network's far-left main toolbar**: dashboard, topology, devices, clients, radios, Settings, Integrations, People, and other application tools.
3. **Settings' wider sidebar**: WiFi, Networks, Internet, VPN, CyberSecure, Policy Engine, System, and console-specific management.

This distinction matters: **Integrations lives in the main toolbar**, not necessarily in the Settings sidebar or Settings search.

## Initial discovery worksheet

```text
Date/time/timezone:
Console model (not custom site name) or controller hosting type:
Installed UniFi OS / OS Server version, N/A, or unknown:
Installed Network application version:
Local console origin:
Integrations found at:
Network API documentation and request format available:
Account role, if known:
```

To find the model, inspect the site/console product label, console details, or physical label without disconnecting equipment. A custom name such as “Home” is not a model. On self-hosted installations, describe the host; a traditional Network Server has no UniFi OS version. Do not confuse Network's version with AP firmware or the phone app version.

## Verified navigation

| Goal | Path in the tested layout | What to inspect |
| --- | --- | --- |
| Installed versions | Network → Settings (gear) → Updates under the console-model heading | Installed Version for the console and Network; not an available update |
| Backups / remote access / SSH | Settings → Management → General | Current checked states and backup timestamp |
| API setup | Network main toolbar → plug-shaped Integrations icon | Network API, API Request Format, Create New API Key |
| Legacy firewall | Settings → Policy Engine → second icon (table/grid), Traffic & Firewall Rules → Advanced | Category tabs and full rule table |
| Forwarding count / NAT | Settings → Policy Engine → first icon, Policy Table | All Policies, no active filters, Port Forwarding and NAT counts; include defaults |
| UPnP / WAN IP settings | Settings → Internet → select active WAN row | UPnP, DHCP/static settings, DNS, IPv6 configuration |
| LAN IPv6 / DHCP | Settings → Networks → select network row | IPv6 Interface Type, subnet, DHCP, isolation |
| Threat prevention | Settings → CyberSecure → Threat Management | Actual Intrusion Prevention Off/On selection and engine-update notices |
| Radio health | Network main toolbar → waveform/Radios icon | Signal, interference, airtime, retries, clients, uplink |
| Client connection | Network main toolbar → Client Devices | SSID, AP, band/channel, rates and signal if exposed |
| Administrator overview | Network main toolbar → People/Admins | Visible roles; don't infer MFA if not displayed |

On other releases, Ubiquiti documents **Settings → Control Plane → Updates**. If your sidebar instead has **Updates** directly beneath the console-model heading, use that. Repeating the Control Plane instruction will not make a missing menu appear. See [UniFi Updates](https://help.ui.com/hc/en-us/articles/7605005245975-UniFi-Updates).

## Reading the legacy firewall

1. Select **Traffic & Firewall Rules** using the second Policy Engine icon.
2. **Simple** may show only simplified traffic rules or a Create Entry panel.
3. Select **Advanced** at the upper right to reveal the rule table. This changes the view; it does not create a policy or upgrade the firewall.
4. Review **Internet**, **LAN**, **Guest**, **Internet v6**, **LAN v6**, and **Guest v6**. Include all nonempty categories and any applicable filters.
5. Capture rule order, action, type, protocol, source/destination, and ports. A count alone says nothing about what those rules permit.
6. Leave **Create Entry**, **Create List**, and any zone-based firewall **Click to upgrade** banner untouched during inspection.

| Term | Meaning |
| --- | --- |
| Internet | IPv4 rules on the internet-facing side |
| LAN | IPv4 LAN-side rules |
| v6 | IPv6 rules; review separately |
| In | Traffic entering that interface and destined for another network |
| Local | Traffic destined for the gateway itself |
| Out | Traffic exiting toward the named network |
| Established/Related | Conditions limiting traffic to existing/related connections |
| Invalid | Traffic classified as invalid by connection tracking |
| Accept / Drop | Permit / discard matching traffic |
| Lock icon | A locked/predefined rule in the table |

An **Allow Established/Related** row with Source Any and Destination Any is not unrestricted inbound access: its connection-state conditions matter. Similarly, IPv6 neighbor-discovery/DHCPv6 allows are not equivalent to allowing every application service. Read the actual rule conditions before judging an exception.

The legacy article remains useful for terminology: [UniFi Gateway — Advanced Firewall Rules](https://help.ui.com/hc/en-us/articles/27699646208279-UniFi-Gateway-Advanced-Firewall-Rules). Modern zone-based deployments use a different organization.

## Common traps

- **Subscription tier versus protection state:** “Standard,” a signature count, or an Enhanced offer does not establish that intrusion prevention is On.
- **Form defaults versus configuration:** an unnamed form with an Add button may be a new policy, not a saved one.
- **WiFi names versus isolation:** two SSIDs can use the same native LAN. A separate name or 2.4 GHz-only broadcast is not a VLAN boundary.
- **IPv6 rules versus IPv6 operation:** factory IPv6 rules can exist while the LAN has Interface Type None. Inspect WAN and LAN settings.
- **Client history versus connections:** a client table can include offline records. Its total footer may exceed the current connected count.
- **Virtualized rows:** a screenshot/DOM read may include only rendered rows. Do not claim an entire inventory from a partial view.
- **Automatic values:** TX Power Auto is not a measured dBm value; an offered update is not the installed version.
- **Cloud versus local access:** a `unifi.ui.com` screenshot proves cloud-console access, not direct reachability at the LAN address.

If labels differ, record what is visible and use the connected browser or a targeted screenshot to establish the next click. Document that actual path rather than accumulating guessed routes.
