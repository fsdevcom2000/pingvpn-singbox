# PingVPN for sing-box

Auto-fetch free PingVPN proxies and generate sing-box config with automatic fastest node selection.

## Features

- Completely free (uses PingVPN free tier)
    
- Auto-selects fastest proxy via urltest
    
- Always up-to-date server list
    
- Full TUN routing
    

## Requirements

- Linux with systemd
    
- Python 3.7+
    
- sing-box installed
    
- `pip install requests pyyaml`
    

## Quick Start

```bash
git clone https://github.com/fsdevcom2000/pingvpn-singbox.git
cd pingvpn-singbox
```

```bash
chmod +x pingvpn-singbox-fetcher.py
python3 pingvpn-singbox-fetcher.py
```

#### Edit `config.yaml` with your paths
## Config Example

```yaml

paths:
  config: "/etc/sing-box/config.json"
  log: "/var/log/singbox-updater.log"
service: "sing-box"
dns:
  - { tag: "dns-local", type: "udp", server: "10.10.100.10" }
  - { tag: "dns-backup", type: "udp", server: "10.10.100.11" }
tun:
  interface_name: "singbox0"
  address: ["172.19.0.1/30"]
  route_address: ["0.0.0.0/1", "128.0.0.0/1"]  # routes all traffic

```

## Auto-update with Cron

```bash
0 * * * * /usr/bin/python3 /path/to/pingvpn-singbox-fetcher.py
```

# View logs

```
/var/log/singbox-updater.log
```
# Test tunnel

```
curl --interface singbox0 ifconfig.me
```

## Troubleshooting

**`sing-box: command not found`** → Install sing-box or add to PATH

**No internet** > Check TUN interface: `ip addr show singbox0`

## Disclaimer

Not affiliated with PingVPN. For educational purposes. May violate PingVPN ToS.

---

**⭐ Star if useful!**

---


# PingVPN для sing-box

Автоматически получает бесплатные прокси PingVPN и генерирует конфиг для sing-box с авто-выбором самого быстрого узла.

## Возможности

- Полностью бесплатно
    
- Автовыбор самого быстрого узла через urltest
    
- Актуальный список серверов
    
- Полная TUN-маршрутизация
    

## Требования

- Linux с systemd
    
- Python 3.7+
    
- Установленный sing-box
    
- `pip install requests pyyaml`
    

## Быстрый старт

```bash
git clone https://github.com/yourusername/pingvpn-singbox.git
cd pingvpn-singbox
```

```bash
chmod +x pingvpn-singbox-fetcher.py
python3 pingvpn-singbox-fetcher.py
```

#### Отредактируйте `config.yaml`
## Пример конфига

```yaml
paths:
  config: "/etc/sing-box/config.json"
  log: "/var/log/singbox-updater.log"
service: "sing-box"
dns:
  - { tag: "dns-local", type: "udp", server: "10.10.100.10" }
  - { tag: "dns-backup", type: "udp", server: "10.10.100.11" }
tun:
  interface_name: "singbox0"
  address: ["172.19.0.1/30"]
  route_address: ["0.0.0.0/1", "128.0.0.0/1"]  # весь трафик через VPN
```

## Автообновление (cron)

```bash
0 * * * * /usr/bin/python3 /path/to/pingvpn-singbox-fetcher.py
```

# Логи

```
/var/log/singbox-updater.log
```
# Тест TUN

```bash
curl --interface singbox0 ifconfig.me
```

## Проблемы

**`sing-box: command not found`** → Установите sing-box

**Нет интернета** > Проверьте: `ip addr show singbox0`

## Дисклеймер

Не связан с PingVPN. В образовательных целях. Может нарушать условия сервиса.

---

**⭐ Поставьте звезду, если пригодилось!**

