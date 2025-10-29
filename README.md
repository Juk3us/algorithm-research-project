# MikroTik VPN Server Configuration

پیکربندی کامل یک MikroTik Router به عنوان VPN Server با قابلیت Failover و WireGuard VPN

## توضیحات پروژه

این پروژه شامل پیکربندی کامل یک روتر MikroTik است که به عنوان یک VPN Server با استفاده از پروتکل WireGuard عمل می‌کند. این پیکربندی شامل:

- اتصال چندگانه WAN با قابلیت Failover
- سرور WireGuard VPN
- NAT و Routing پیشرفته
- فایروال و امنیت
- پشتیبانی از VLAN و PPPoE

## معماری شبکه

```
                                    ┌─────────────────┐
                                    │   Internet      │
                                    └────────┬────────┘
                                             │ Port 5
                    ┌────────────────────────┴────────────────────────┐
                    │                  MikroTik Router                │
                    │            WireGuard VPN Server: 13231          │
                    └───┬────────┬──────────────┬─────────────────────┘
                  Port 1    Port 2          Port 3-4
                    │         │                 │
        ┌───────────┴─┐   ┌───┴──────────┐     │
        │   ISP 1     │   │   ISP 2      │     │
        │  (PPPoE)    │   │   (VDSL)     │     │
        └──────┬──────┘   └──────┬───────┘     │
               │                 │              │
        اینترانت کشور      اینترانت کشور      LAN
               │                 │              │
          ┌────┴─────────────────┴────┐    ┌────┴────┐
          │   VPN Clients             │    │  Local  │
          │   192.168.200.0/24        │    │ Clients │
          └───────────────────────────┘    └─────────┘
```

**جریان ترافیک:**
- کلاینت‌های VPN از اینترانت → Port 1/2 → MikroTik → Port 5 → اینترنت

### اینترفیس‌ها

- **Port 1**: دریافت ترافیک VPN از اینترانت (PPPoE via Radio) - اولویت 1
- **Port 2**: دریافت ترافیک VPN از اینترانت (VDSL Backup) - اولویت 2
- **Port 3-4**: پورت‌های LAN محلی (Bridge)
- **Port 5**: ارسال ترافیک VPN به اینترنت

### شبکه‌ها

- **LAN**: 192.168.100.0/24
- **VPN (WireGuard)**: 192.168.200.0/24
- **VDSL Backup**: 192.168.10.0/24
- **Internet**: 192.168.1.0/24

## فایل‌های پروژه

### فایل‌های سرور
- **mikrotik-vpn-config.rsc**: فایل کانفیگ اصلی MikroTik
- **INSTALLATION-GUIDE.md**: راهنمای کامل نصب و پیکربندی (فارسی)
- **README.md**: این فایل

### فایل‌های کلاینت
- **client1.conf**: فایل کانفیگ کلاینت اول (برای import دستی)
- **client1-qrcode.png**: QR Code کلاینت اول (برای اسکن با موبایل)
- **CLIENT-SETUP.md**: راهنمای کامل راه‌اندازی کلاینت
- **CLIENT-CONFIG-GUIDE.md**: راهنمای جامع کانفیگ کلاینت (همه پلتفرم‌ها)

### راهنماها و عیب‌یابی
- **TROUBLESHOOTING.md**: راهنمای کامل رفع مشکل "اتصال برقرار اما receive صفر"
- **FIX-NO-RECEIVE.txt**: دستورات رفع مشکل با توضیحات (آماده کپی)
- **QUICK-FIX.txt**: دستورات رفع سریع بدون توضیح (فقط کپی-پیست)

## نصب سریع

### پیش‌نیازها

1. یک روتر MikroTik با حداقل 5 پورت Ethernet
2. RouterOS نسخه 7.x یا بالاتر (برای پشتیبانی WireGuard)
3. دسترسی به روتر از طریق WinBox، SSH، یا WebFig

### مراحل نصب

1. **تولید کلید خصوصی WireGuard**:
   ```bash
   # در لینوکس/Mac
   wg genkey
   ```

2. **ویرایش فایل کانفیگ**:
   - فایل `mikrotik-vpn-config.rsc` را باز کنید
   - کلید خصوصی را در قسمت WireGuard جایگزین کنید

3. **آپلود به MikroTik**:
   ```bash
   scp mikrotik-vpn-config.rsc admin@192.168.88.1:/
   ```

4. **اعمال کانفیگ**:
   ```bash
   ssh admin@192.168.88.1
   /import mikrotik-vpn-config.rsc
   ```

5. **تست و راه‌اندازی**:
   ```bash
   /interface print
   /ip route print
   /interface wireguard print
   ```

برای جزئیات بیشتر، فایل [INSTALLATION-GUIDE.md](INSTALLATION-GUIDE.md) را مطالعه کنید.

## راه‌اندازی سریع کلاینت

### روش 1: استفاده از QR Code (موبایل) 📱

1. اپلیکیشن WireGuard را نصب کنید (Android/iOS)
2. روی **+** بزنید
3. گزینه **"Scan from QR code"** را انتخاب کنید
4. فایل `client1-qrcode.png` را اسکن کنید
5. نام بدهید و سوییچ را فعال کنید
6. ✅ آماده!

### روش 2: استفاده از فایل کانفیگ (دسکتاپ) 💻

**Windows/macOS:**
1. WireGuard را نصب کنید
2. **Import tunnel from file** → فایل `client1.conf`
3. **Activate** کنید

**Linux:**
```bash
sudo apt install wireguard
sudo cp client1.conf /etc/wireguard/wg0.conf
sudo wg-quick up wg0
```

برای راهنمای کامل، فایل [CLIENT-CONFIG-GUIDE.md](CLIENT-CONFIG-GUIDE.md) را مطالعه کنید.

## ویژگی‌های کلیدی

### 1. Multi-WAN با Failover خودکار
- اتصال اصلی: PPPoE از طریق لینک رادیویی (Distance=1)
- اتصال بکاپ: VDSL DHCP (Distance=2)
- تعویض خودکار در صورت قطعی

### 2. WireGuard VPN Server
- پروتکل مدرن و سریع WireGuard
- رمزنگاری قوی
- پشتیبانی از چند کلاینت همزمان
- IP استاتیک برای هر کلاینت

### 3. NAT و مسیریابی هوشمند
- NAT Masquerade برای کلاینت‌های LAN و VPN
- مسیریابی بر اساس منبع (Source-based routing)
- ترافیک VPN از طریق اینترنت اختصاصی

### 4. امنیت و فایروال
- فایروال پیکربندی شده و آماده
- محدودیت دسترسی به مدیریت
- Logging برای WireGuard و Firewall
- غیرفعال کردن سرویس‌های غیرضروری

### 5. VLAN Support
- پشتیبانی از VLAN 1787 برای PPPoE
- قابل توسعه برای VLAN های بیشتر

## مستندات تکمیلی

### تست اتصال

```bash
# بررسی وضعیت اینترفیس‌ها
/interface print stats

# بررسی مسیرها
/ip route print where active

# بررسی WireGuard
/interface wireguard peers print

# بررسی اتصالات فعال
/ip firewall connection print
```

### افزودن کلاینت VPN جدید

```bash
# 1. تولید کلید برای کلاینت جدید
wg genkey | tee client_private.key | wg pubkey > client_public.key

# 2. افزودن peer به سرور
/interface wireguard peers add \
    allowed-address=192.168.200.X/32 \
    interface=wireguard-vpn \
    public-key="CLIENT_PUBLIC_KEY" \
    comment="New Client"
```

### گرفتن Backup

```bash
# Backup باینری
/system backup save name=backup-$(date +%Y%m%d)

# Export متنی (قابل ویرایش)
/export file=config-$(date +%Y%m%d)
```

## عیب‌یابی

### مشکلات رایج

**PPPoE متصل نمی‌شود:**
- بررسی VLAN ID: باید 1787 باشد
- بررسی username و password
- بررسی کابل و اتصال فیزیکی

**VPN متصل می‌شود اما اینترنت ندارد:**
- بررسی NAT: `/ip firewall nat print`
- بررسی مسیرها: `/ip route print`
- بررسی DNS: `/ip dns print`

**Failover کار نمی‌کند:**
- بررسی distance مسیرها
- تست با غیرفعال کردن دستی: `/interface pppoe-client disable`

### مشاهده لاگ‌ها

```bash
# لاگ WireGuard
/log print where topics~"wireguard"

# لاگ PPPoE
/log print where topics~"pppoe"

# لاگ Firewall
/log print where topics~"firewall"
```

## اطلاعات تماس و پشتیبانی

- [مستندات رسمی MikroTik](https://wiki.mikrotik.com)
- [راهنمای WireGuard](https://www.wireguard.com/quickstart/)
- [انجمن MikroTik](https://forum.mikrotik.com)

## مجوز

این پیکربندی برای استفاده شخصی و آموزشی ارائه شده است.

## نکات امنیتی

1. **حتماً** پسورد پیش‌فرض admin را تغییر دهید
2. پورت‌های مدیریتی (SSH, WinBox) را تغییر دهید
3. دسترسی مدیریتی را فقط از LAN فعال کنید
4. بک‌آپ منظم از کانفیگ بگیرید
5. RouterOS را به‌روز نگه دارید

## به‌روزرسانی‌ها

- **v1.0** (2025-10-29): نسخه اولیه
  - پیکربندی پایه Multi-WAN
  - سرور WireGuard VPN
  - فایروال و امنیت
  - مستندات کامل فارسی

---

**نکته**: این پیکربندی برای سناریوی خاص ارائه شده است. در صورت نیاز به تغییرات، لطفاً مستندات را با دقت مطالعه کنید یا با یک متخصص شبکه مشورت کنید.
