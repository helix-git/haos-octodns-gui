# OctoDNS GUI

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

Web-basierte GUI zur Verwaltung von DNS-Zonen mit OctoDNS.

## Features

- Erstellen, Bearbeiten und Löschen von DNS-Zonen
- YAML-basierte Zone-Dateien (OctoDNS Format)
- Dark Mode Unterstützung
- Home Assistant Authentifizierung

## Installation

Dieses Add-on ist Teil des [haos-apps](https://github.com/helix-git/haos-apps) Repositories.

1. Repository in Home Assistant hinzufügen
2. Add-on "OctoDNS GUI" installieren
3. Add-on konfigurieren und starten

## Konfiguration

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `dns_provider` | DNS Provider Name | - |
| `zone_file_path` | Pfad zu den Zone-Dateien | `/config/octodns` |

## Verwendung

1. Öffne das Add-on über die Sidebar in Home Assistant
2. Erstelle eine neue Zone oder bearbeite existierende
3. Zone-Dateien werden im konfigurierten Verzeichnis gespeichert

## Zone-Format

Die Zonen folgen dem [OctoDNS YAML Format](https://github.com/octodns/octodns):

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

## Support

Bei Problemen bitte ein Issue erstellen.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
