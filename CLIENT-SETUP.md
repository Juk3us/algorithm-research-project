# راهنمای راه‌اندازی کلاینت WireGuard

این راهنما نحوه اتصال کلاینت‌ها به سرور WireGuard را توضیح می‌دهد.

## فایل‌های موجود

- **client1.conf** - فایل کانفیگ کلاینت اول (برای استفاده دستی)
- **client1-qrcode.png** - QR Code کلاینت اول (برای موبایل)

## روش اول: استفاده از QR Code (موبایل)

### Android

1. اپلیکیشن WireGuard را از Google Play نصب کنید
2. اپ را باز کنید
3. روی دکمه **+** کلیک کنید
4. گزینه **"Scan from QR code"** را انتخاب کنید
5. فایل `client1-qrcode.png` را نمایش دهید و اسکن کنید
6. نام دلخواه برای tunnel وارد کنید (مثلاً "VPN Server")
7. روی **Create Tunnel** کلیک کنید
8. برای اتصال، سوییچ را فعال کنید

### iOS (iPhone/iPad)

1. اپلیکیشن WireGuard را از App Store نصب کنید
2. اپ را باز کنید
3. روی دکمه **+** کلیک کنید
4. گزینه **"Create from QR code"** را انتخاب کنید
5. دوربین باز می‌شود، فایل `client1-qrcode.png` را اسکن کنید
6. نام دلخواه برای tunnel وارد کنید
7. روی **Save** کلیک کنید
8. برای اتصال، سوییچ را فعال کنید

## روش دوم: استفاده از فایل کانفیگ (دسکتاپ)

### Windows

1. [WireGuard for Windows](https://www.wireguard.com/install/) را دانلود و نصب کنید
2. برنامه را اجرا کنید
3. روی **Import tunnel(s) from file** کلیک کنید
4. فایل `client1.conf` را انتخاب کنید
5. برای اتصال، روی **Activate** کلیک کنید

### macOS

1. [WireGuard for macOS](https://www.wireguard.com/install/) را از App Store نصب کنید
2. برنامه را اجرا کنید
3. روی **Import tunnel(s) from file** کلیک کنید
4. فایل `client1.conf` را انتخاب کنید
5. برای اتصال، سوییچ را فعال کنید

### Linux

```bash
# نصب WireGuard
sudo apt update
sudo apt install wireguard

# کپی فایل کانفیگ
sudo cp client1.conf /etc/wireguard/wg0.conf

# فعال کردن VPN
sudo wg-quick up wg0

# بررسی وضعیت
sudo wg show

# غیرفعال کردن VPN
sudo wg-quick down wg0

# فعال کردن خودکار هنگام بوت
sudo systemctl enable wg-quick@wg0
```

## تست اتصال

بعد از اتصال به VPN، می‌توانید اتصال را تست کنید:

### تست 1: Ping به Gateway VPN

```bash
ping 192.168.200.1
```

باید پاسخ دریافت کنید.

### تست 2: بررسی IP عمومی

```bash
curl https://ifconfig.me
```

یا از سایت [https://whatismyipaddress.com](https://whatismyipaddress.com) استفاده کنید.

اگر VPN درست کار کند، باید IP سرور (2.187.7.240) را ببینید.

### تست 3: بررسی DNS

```bash
nslookup google.com
```

باید از DNS سرور VPN (8.8.8.8) استفاده شود.

## مشکلات رایج و راه‌حل

### اتصال برقرار نمی‌شود

1. **بررسی فایروال**: مطمئن شوید پورت 13231/UDP باز است
2. **بررسی اینترنت**: اطمینان حاصل کنید که به اینترنت دسترسی دارید
3. **بررسی endpoint**: آدرس `2.187.7.240:13231` باید قابل دسترسی باشد

```bash
# تست دسترسی به پورت
nc -zvu 2.187.7.240 13231
```

### اتصال برقرار می‌شود اما اینترنت کار نمی‌کند

1. بررسی کنید که `AllowedIPs = 0.0.0.0/0` در کانفیگ تنظیم شده باشد
2. از سرور مطمئن شوید که NAT فعال است:

```bash
/ip firewall nat print
```

### سرعت کند است

1. MTU را کاهش دهید (در فایل کانفیگ):

```ini
[Interface]
MTU = 1380
```

2. از سرور نزدیک‌تر استفاده کنید

## مشخصات Client 1

```
IP Address: 192.168.200.2/24
Private Key: Z7LG524rwRtsllL9V4rbFwFHoRQBajCv5TYmTup0YAw=
Public Key: HRnO/GFu1WFeYWkmsU65riEUPJrDvWnU//Q69bTKmQA=
DNS: 8.8.8.8, 1.1.1.1
```

## مشخصات Server

```
Endpoint: 2.187.7.240:13231
Public Key: OkMrWI423O6h0Fgvg40RRvzWBLv1bC4CEfNi9INlph0=
Allowed IPs: 0.0.0.0/0
```

## افزودن کلاینت جدید

برای افزودن کلاینت‌های بیشتر، به راهنمای [INSTALLATION-GUIDE.md](INSTALLATION-GUIDE.md) مراجعه کنید.

## امنیت

⚠️ **هشدار امنیتی**:
- کلید خصوصی (`PrivateKey`) را با کسی به اشتراک نگذارید
- فایل `client1.conf` حاوی کلید خصوصی است و باید محرمانه نگه داشته شود
- QR code را فقط یک بار استفاده کنید و از اشتراک آن خودداری کنید

## پشتیبانی

برای اطلاعات بیشتر:
- [مستندات رسمی WireGuard](https://www.wireguard.com/)
- [راهنمای نصب سرور](INSTALLATION-GUIDE.md)
- [README اصلی](README.md)
