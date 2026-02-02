# OctoDNS GUI

Web-basierte GUI zur Verwaltung von DNS-Zonen mit OctoDNS.

## Vorinstallierte Provider

Folgende OctoDNS-Provider sind vorinstalliert und können über die Konfiguration aktiviert werden:

| Provider | Typ | Dokumentation |
|----------|-----|---------------|
| Cloudflare | Source + Target | [octodns-cloudflare](https://github.com/octodns/octodns-cloudflare) |
| OVH | Target | [octodns-ovh](https://github.com/octodns/octodns-ovh) |
| Pi-hole | Target | [octodns-pihole](https://github.com/jvoss/octodns-pihole) |
| NetBox DNS | Source | [octodns-netbox-dns](https://github.com/octodns/octodns-netbox-dns) |
| NetBox | Source | [octodns-netbox](https://github.com/octodns/octodns-netbox) |
| BIND | Source + Target | [octodns-bind](https://github.com/octodns/octodns-bind) |

## Konfiguration

### enabled_providers

Liste der zu aktivierenden Provider. Wähle nur die Provider, die du tatsächlich verwendest.

**Mögliche Werte:** `cloudflare`, `ovh`, `pihole`, `netbox-dns`, `netbox`, `bind`

**Beispiel:**
```yaml
enabled_providers:
  - netbox-dns
  - pihole
```

### zone_file_path

Pfad zum Verzeichnis, in dem Zone-Dateien gespeichert werden. Dieses Verzeichnis wird automatisch erstellt.

**Standard:** `/config/octodns`

## Zone-Format

Zone-Dateien folgen dem [OctoDNS YAML Format](https://github.com/octodns/octodns):

```yaml
'':
  type: A
  value: 1.2.3.4

www:
  type: CNAME
  value: example.com.

mail:
  type: MX
  values:
    - priority: 10
      value: mail1.example.com.
```

## Typische Anwendungsfälle

### NetBox DNS → Pi-hole

DNS-Einträge aus NetBox auslesen und zu Pi-hole synchronisieren:

1. **enabled_providers:** `netbox-dns`, `pihole`
2. NetBox DNS als Source konfigurieren
3. Pi-hole als Target konfigurieren
4. Sync ausführen

### NetBox DNS → Cloudflare

DNS-Einträge aus NetBox zu Cloudflare synchronisieren:

1. **enabled_providers:** `netbox-dns`, `cloudflare`
2. NetBox DNS als Source konfigurieren
3. Cloudflare API Token hinterlegen
4. Sync ausführen

## Support

- [GitHub Issues](https://github.com/helix-git/haos-octodns-gui/issues)
- [OctoDNS Dokumentation](https://github.com/octodns/octodns)
