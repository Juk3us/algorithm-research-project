# راهنمای نصب و پیکربندی MikroTik VPN Server

## معماری شبکه

```
                                    ┌─────────────────┐
                                    │   Internet      │
                                    │   Modem         │
                                    │  192.168.1.1    │
                                    └────────┬────────┘
                                             │
                                         Port 5
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │                  MikroTik Router                │
                    │                 192.168.100.1                   │
                    │            WireGuard VPN Server: 13231          │
                    └───┬────────┬──────────────┬─────────────────────┘
                  Port 1    Port 2          Port 3-4
                    │         │              (LAN Bridge)
                    │         │              192.168.100/24
        ┌───────────┴─┐   ┌───┴──────────┐      │
        │   ISP 1     │   │   ISP 2      │      │
        │  (Radio)    │   │   (VDSL)     │      │
        │  PPPoE      │   │   Modem      │      │
        │  VLAN 1787  │   │ 192.168.10.1 │      │
        └──────┬──────┘   └──────┬───────┘      │
               │                 │               │
        اینترانت کشور      اینترانت کشور    ┌────┴────┐
               │                 │          │  Local  │
               │                 │          │   LAN   │
          ┌────┴─────────────────┴────┐     │ Clients │
          │   VPN Clients             │     └─────────┘
          │   (از طریق اینترانت)      │
          │   192.168.200.0/24        │
          │   Connect to:             │
          │   2.187.7.240:13231       │
          └───────────────────────────┘
```

**توضیح جریان ترافیک:**
1. کلاینت‌های VPN از طریق اینترانت کشور (ISP 1 یا ISP 2) به میکروتیک متصل می‌شوند
2. میکروتیک ترافیک VPN را از پورت 5 به اینترنت می‌فرستد
3. پورت 1 (اصلی) و پورت 2 (بکاپ) برای دریافت ترافیک از کلاینت‌های VPN استفاده می‌شوند

## مشخصات شبکه

### اینترفیس‌ها
- **Port 1 (ether1)**: اتصال به ISP از طریق لینک رادیویی + PPPoE
  - VLAN ID: 1787
  - Username: 1331626494
  - Password: 351598
  - Priority: 1 (اصلی)

- **Port 2 (ether2)**: اتصال بکاپ به VDSL
  - DHCP Client فعال
  - شبکه VDSL: 192.168.10.0/24
  - Gateway: 192.168.10.1
  - Priority: 2 (بکاپ)

- **Port 3-4 (ether3-4)**: پورت‌های LAN (در یک Bridge)
  - شبکه: 192.168.100.0/24
  - Gateway: 192.168.100.1

- **Port 5 (ether5)**: اتصال به اینترنت
  - DHCP Client فعال
  - شبکه: 192.168.1.0/24
  - Gateway: 192.168.1.1
  - Priority: 3 (برای ترافیک VPN)

### WireGuard VPN
- **آدرس سرور**: 2.187.7.240:13231
- **شبکه VPN**: 192.168.200.0/24
- **IP سرور**: 192.168.200.1/24
- **Server Public Key**: `OkMrWI423O6h0Fgvg40RRvzWBLv1bC4CEfNi9INlph0=`
- **Client 1 Public Key**: `HRnO/GFu1WFeYWkmsU65riEUPJrDvWnU//Q69bTKmQA=`
- **Client 1 Private Key**: `Z7LG524rwRtsllL9V4rbFwFHoRQBajCv5TYmTup0YAw=`

## مراحل نصب

### مرحله 1: تولید کلید خصوصی WireGuard

قبل از اعمال کانفیگ، باید کلید خصوصی سرور را تولید کنید:

```bash
# در MikroTik، کلید خصوصی را تولید کنید:
/interface wireguard
add listen-port=13231 name=wireguard-vpn

# کلید عمومی را مشاهده کنید (باید با مقدار داده شده مطابقت کند)
print
```

یا می‌توانید از ابزار `wg` در لینوکس استفاده کنید:

```bash
# تولید کلید خصوصی
wg genkey

# برای بدست آوردن کلید عمومی از روی کلید خصوصی:
echo "YOUR_PRIVATE_KEY" | wg pubkey
```

### مرحله 2: ویرایش فایل کانفیگ

1. فایل `mikrotik-vpn-config.rsc` را باز کنید
2. خط زیر را پیدا کنید:
   ```
   private-key="YOUR_SERVER_PRIVATE_KEY_HERE"
   ```
3. `YOUR_SERVER_PRIVATE_KEY_HERE` را با کلید خصوصی واقعی جایگزین کنید

### مرحله 3: آپلود فایل به MikroTik

#### روش 1: از طریق WinBox
1. به MikroTik متصل شوید
2. Files → Upload → فایل `mikrotik-vpn-config.rsc` را آپلود کنید

#### روش 2: از طریق SCP/SFTP
```bash
scp mikrotik-vpn-config.rsc admin@192.168.88.1:/
```

#### روش 3: از طریق FTP
از نرم‌افزار FileZilla یا WinSCP استفاده کنید

### مرحله 4: اعمال کانفیگ

```bash
# اتصال به MikroTik از طریق SSH
ssh admin@192.168.88.1

# اعمال کانفیگ
/import mikrotik-vpn-config.rsc

# بررسی وضعیت
/interface print
/ip address print
/ip route print
/interface wireguard print
```

### مرحله 5: تنظیم IP استاتیک برای Port 5 (اختیاری)

اگر می‌خواهید IP استاتیک برای Port 5 تنظیم کنید:

```bash
/ip dhcp-client remove [find interface=ether5-internet]
/ip address add address=192.168.1.2/24 interface=ether5-internet
/ip route add dst-address=0.0.0.0/0 gateway=192.168.1.1 distance=3
```

## راه‌اندازی کلاینت WireGuard

### کانفیگ کلاینت نمونه (Client 1)

```ini
[Interface]
PrivateKey = Z7LG524rwRtsllL9V4rbFwFHoRQBajCv5TYmTup0YAw=
Address = 192.168.200.2/24
DNS = 8.8.8.8, 1.1.1.1

[Peer]
PublicKey = OkMrWI423O6h0Fgvg40RRvzWBLv1bC4CEfNi9INlph0=
Endpoint = 2.187.7.240:13231
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

**نکته مهم**: این کلیدها برای Client 1 از قبل تولید شده‌اند. QR code این کانفیگ در انتهای فایل `mikrotik-vpn-config.rsc` موجود است.

### نحوه تولید کلید کلاینت جدید

```bash
# تولید کلید خصوصی کلاینت
wg genkey > client2_private.key

# تولید کلید عمومی کلاینت
cat client2_private.key | wg pubkey > client2_public.key

# نمایش کلیدها
cat client2_private.key
cat client2_public.key
```

**مثال کلیدهای Client 1** (از قبل تولید شده):
- Private Key: `Z7LG524rwRtsllL9V4rbFwFHoRQBajCv5TYmTup0YAw=`
- Public Key: `HRnO/GFu1WFeYWkmsU65riEUPJrDvWnU//Q69bTKmQA=`

## افزودن کلاینت جدید

برای افزودن کلاینت جدید به سرور:

```bash
# در MikroTik
/interface wireguard peers
add allowed-address=192.168.200.3/32 \
    interface=wireguard-vpn \
    public-key="NEW_CLIENT_PUBLIC_KEY" \
    comment="WireGuard Client 2"
```

## تست و عیب‌یابی

### بررسی وضعیت اتصالات

```bash
# بررسی اینترفیس‌ها
/interface print stats

# بررسی آدرس‌های IP
/ip address print

# بررسی مسیرها (Routing)
/ip route print

# بررسی WireGuard
/interface wireguard print
/interface wireguard peers print

# بررسی فایروال
/ip firewall filter print stats
/ip firewall nat print

# بررسی اتصالات فعال
/ip firewall connection print
```

### تست اتصال PPPoE

```bash
# بررسی وضعیت PPPoE
/interface pppoe-client print detail

# در صورت مشکل، فعال/غیرفعال کردن
/interface pppoe-client disable pppoe-intranet
/interface pppoe-client enable pppoe-intranet

# مشاهده لاگ
/log print where topics~"pppoe"
```

### تست Failover

```bash
# غیرفعال کردن PPPoE برای تست فیل‌اور
/interface pppoe-client disable pppoe-intranet

# بررسی مسیر پیش‌فرض (باید به VDSL تغییر کند)
/ip route print where dst-address=0.0.0.0/0

# فعال کردن مجدد
/interface pppoe-client enable pppoe-intranet
```

### تست VPN از کلاینت

```bash
# از کلاینت، ping به سرور VPN
ping 192.168.200.1

# تست اتصال به اینترنت
ping 8.8.8.8
curl https://ifconfig.me

# بررسی مسیر
traceroute 8.8.8.8
```

### مشاهده لاگ‌ها

```bash
# لاگ‌های WireGuard
/log print where topics~"wireguard"

# لاگ‌های فایروال
/log print where topics~"firewall"

# همه لاگ‌ها
/log print
```

## مسیریابی ترافیک

### جریان ترافیک

1. **کلاینت‌های LAN به اینترانت**:
   - LAN (192.168.100.0/24) → Port 1 (PPPoE - اصلی)
   - در صورت قطعی Port 1 → Port 2 (VDSL - بکاپ)

2. **کلاینت‌های VPN به اینترنت**:
   - VPN (192.168.200.0/24) → Port 5 (Internet)
   - NAT Masquerade فعال

3. **اولویت مسیرها**:
   - Distance 1: PPPoE (اصلی)
   - Distance 2: VDSL (بکاپ)
   - Distance 3: Internet (برای VPN)

## امنیت

### تغییر پورت‌های پیش‌فرض

```bash
# تغییر پورت SSH
/ip service set ssh port=22222

# تغییر پورت Winbox
/ip service set winbox port=8291
```

### محدود کردن دسترسی به مدیریت

```bash
# فقط از LAN
/ip service
set ssh address=192.168.100.0/24
set winbox address=192.168.100.0/24
```

### فعال کردن فایروال برای محافظت بیشتر

قوانین فایروال پیشرفته در فایل کانفیگ گنجانده شده‌اند.

## پشتیبانی و بازیابی

### گرفتن Backup

```bash
# Backup کامل
/system backup save name=backup-$(date +%Y%m%d)

# Export کانفیگ
/export file=config-$(date +%Y%m%d)
```

### بازیابی از Backup

```bash
# بازیابی از فایل backup
/system backup load name=backup-20250129

# اعمال فایل export
/import config-20250129.rsc
```

## مشکلات رایج و راه‌حل‌ها

### 1. PPPoE متصل نمی‌شود
- بررسی VLAN ID صحیح باشد
- بررسی username و password
- بررسی اتصال فیزیکی پورت 1

### 2. VPN متصل می‌شود اما اینترنت ندارد
- بررسی NAT فعال باشد
- بررسی مسیرها با `/ip route print`
- بررسی فایروال forward rules

### 3. Failover کار نمی‌کند
- بررسی distance مسیرها
- تست با غیرفعال کردن دستی اتصال اصلی

### 4. کلاینت‌های VPN به هم دسترسی ندارند
- بررسی allowed-address برای هر peer
- بررسی فایروال forward rules

## پشتیبانی

برای مشکلات و سوالات:
- مستندات MikroTik: https://wiki.mikrotik.com
- WireGuard Documentation: https://www.wireguard.com

## نسخه و تاریخچه

- Version 1.0 - 2025-10-29: نسخه اولیه
