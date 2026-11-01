# Where to find console settings

These paths were checked on a UCG Max running UniFi OS 5.1.34 and Network 10.6.109. They describe that layout, not a required version. Menus vary by release, hosting type, and account role.

## Start in the right place

Site Manager (`unifi.ui.com`) lists sites. Select your home site, then open Network.

Network has two separate navigation areas: the main toolbar and the Settings sidebar. **Integrations is the plug icon in the main toolbar**, outside Settings. This is easy to miss when looking for API keys.

Before setup, note the console model, installed UniFi OS and Network versions, and local HTTPS origin. A custom site name such as “Home” isn't the model. A traditional self-hosted Network Server has no UniFi OS version; record its hosting type instead.

## Useful paths

| Setting | Path in the tested layout | What to record |
| --- | --- | --- |
| Installed versions | Settings → Updates, under the console-model heading | Installed console and Network versions, rather than offered updates |
| Backups / remote access / SSH | Settings → Management → General | Selected states and latest backup |
| API setup | Main toolbar → Integrations (plug icon) | Network API, API Request Format, Create New API Key |
| Legacy firewall | Settings → Policy Engine → second icon (table/grid) → Traffic & Firewall Rules → Advanced | Ordered rules and conditions in each category |
| Port forwards / NAT | Settings → Policy Engine → first icon → Policy Table | All Policies, with filters cleared |
| UPnP / WAN IPv6 | Settings → Internet → active WAN | UPnP, address settings, prefix delegation |
| LAN IPv6 / DHCP | Settings → Networks → network row | IPv6 Interface Type, subnet, DHCP, isolation |
| Threat prevention | Settings → CyberSecure → Threat Management | Selected Intrusion Prevention state |
| Radio health | Main toolbar → Radios (waveform icon) | Signal, interference, airtime, retries, clients, uplink |
| Client connection | Main toolbar → Client Devices | AP, SSID, band/channel, rates, signal where available |
| Administrators | Main toolbar → People/Admins | Visible roles and access scope |

Some releases put updates under **Settings → Control Plane → Updates**. Follow the labels on your console; see [UniFi Updates](https://help.ui.com/hc/en-us/articles/7605005245975-UniFi-Updates).

## Legacy firewall

Select **Traffic & Firewall Rules**, then **Advanced** at the upper right. Simple view may show only simplified rules or a blank creation form. Advanced changes the view without migrating the firewall.

Review **Internet**, **LAN**, **Guest**, **Internet v6**, **LAN v6**, and **Guest v6**, including any active filters. Record order, action, protocol, source/destination, ports, and connection-state conditions. Leave creation forms and any **Click to upgrade** banner alone during inspection.

| Term | Meaning |
| --- | --- |
| Internet / LAN / Guest | Rule groups for those sides of the network |
| v6 | IPv6 rules, reviewed separately |
| In | Traffic entering the interface for another network |
| Local | Traffic destined for the gateway |
| Out | Traffic exiting toward the named network |
| Established/Related | Matches existing or related connections |
| Invalid | Connections classified as invalid by connection tracking |
| Accept / Drop | Permit / discard matching traffic |
| Lock icon | Predefined or locked rule |

Read the conditions, not just “Any → Any.” An Established/Related allow doesn't permit every new inbound connection. IPv6 neighbor-discovery and DHCPv6 exceptions also need their protocol details considered. See [Advanced Firewall Rules](https://help.ui.com/hc/en-us/articles/27699646208279-UniFi-Gateway-Advanced-Firewall-Rules) for terminology; zone-based setups use a different layout.

## Things worth double-checking

- A subscription tier or signature count doesn't tell you whether intrusion prevention is on.
- An unnamed form with an Add button may show new-policy defaults rather than saved settings.
- Two SSIDs can share one LAN. Check their network assignments before assuming IoT isolation.
- IPv6 rules can exist while LAN IPv6 is disabled. Check WAN and LAN settings together.
- Client tables can include offline devices or load only visible rows. Check filters and scroll before counting.
- Auto transmit power isn't a measured dBm value. Check the actual radio data where available.
- Site Manager access doesn't establish that your computer can reach the local console address.

If a path differs, record the working path in your notes. Keep screenshots focused and private; see [privacy](privacy.md).
