# راهنمای کانفیگ کلاینت WireGuard

## دو روش راه‌اندازی کلاینت:

### روش 1️⃣: استفاده از QR Code (موبایل) ⚡
### روش 2️⃣: استفاده از فایل کانفیگ (دسکتاپ و موبایل) 📄

---

## روش 1️⃣: استفاده از QR Code (آسان‌ترین روش برای موبایل)

### Android:

1. **نصب اپلیکیشن**
   - از Google Play اپلیکیشن "WireGuard" را نصب کنید
   - لینک: https://play.google.com/store/apps/details?id=com.wireguard.android

2. **اسکن QR Code**
   - اپلیکیشن WireGuard را باز کنید
   - روی دکمه **+** (پایین سمت راست) بزنید
   - گزینه **"Scan from QR code"** را انتخاب کنید
   - فایل `client1-qrcode.png` را نمایش دهید و اسکن کنید

3. **نام‌گذاری**
   - یک نام دلخواه وارد کنید (مثلاً "My VPN Server")
   - روی **Create Tunnel** بزنید

4. **اتصال**
   - روی سوییچ کنار نام tunnel بزنید
   - وضعیت به "Connected" تغییر می‌کند
   - ✅ آماده است!

### iOS (iPhone/iPad):

1. **نصب اپلیکیشن**
   - از App Store اپلیکیشن "WireGuard" را نصب کنید

2. **اسکن QR Code**
   - اپلیکیشن را باز کنید
   - روی دکمه **+** بزنید
   - گزینه **"Create from QR code"** را انتخاب کنید
   - دوربین باز می‌شود
   - فایل `client1-qrcode.png` را با دوربین اسکن کنید

3. **ذخیره و اتصال**
   - نام دلخواه وارد کنید
   - **Save** را بزنید
   - سوییچ را فعال کنید
   - ✅ متصل شدید!

---

## روش 2️⃣: استفاده از فایل کانفیگ

### ساختار فایل کانفیگ (client1.conf):

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

### توضیح هر قسمت:

#### بخش [Interface] (تنظیمات کلاینت):

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `PrivateKey` | کلید خصوصی کلاینت | **نگه دارید محرمانه!** |
| `Address` | 192.168.200.2/24 | IP اختصاصی کلاینت در شبکه VPN |
| `DNS` | 8.8.8.8, 1.1.1.1 | DNS سرورها (Google و Cloudflare) |

#### بخش [Peer] (تنظیمات سرور):

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `PublicKey` | کلید عمومی سرور | کلید عمومی MikroTik VPN Server |
| `Endpoint` | 2.187.7.240:13231 | آدرس و پورت سرور |
| `AllowedIPs` | 0.0.0.0/0 | تمام ترافیک از VPN عبور کند |
| `PersistentKeepalive` | 25 | هر 25 ثانیه پینگ برای نگه داشتن اتصال |

---

## راه‌اندازی روی پلتفرم‌های مختلف:

### 🪟 Windows

1. **دانلود و نصب**
   ```
   https://www.wireguard.com/install/
   ```
   یا از Microsoft Store نصب کنید

2. **Import کانفیگ**
   - برنامه WireGuard را باز کنید
   - روی **Import tunnel(s) from file** کلیک کنید
   - فایل `client1.conf` را انتخاب کنید
   - یا محتوای کانفیگ را کپی کنید و **Add empty tunnel** بزنید

3. **اتصال**
   - روی **Activate** کلیک کنید
   - وضعیت به "Active" تغییر می‌کند
   - ✅ متصل شدید!

### 🍎 macOS

1. **نصب از App Store**
   - اپلیکیشن "WireGuard" را نصب کنید

2. **Import کانفیگ**
   - برنامه را باز کنید
   - روی **Import tunnel(s) from file** کلیک کنید
   - فایل `client1.conf` را انتخاب کنید

3. **اتصال**
   - سوییچ را فعال کنید
   - ✅ آماده!

### 🐧 Linux (Ubuntu/Debian)

#### روش 1: استفاده از Terminal

```bash
# نصب WireGuard
sudo apt update
sudo apt install wireguard

# کپی فایل کانفیگ
sudo cp client1.conf /etc/wireguard/wg0.conf

# تنظیم دسترسی‌ها
sudo chmod 600 /etc/wireguard/wg0.conf

# اتصال به VPN
sudo wg-quick up wg0

# بررسی وضعیت
sudo wg show

# قطع اتصال
sudo wg-quick down wg0

# فعال کردن خودکار در بوت
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

#### روش 2: استفاده از GUI (NetworkManager)

```bash
# نصب پلاگین NetworkManager
sudo apt install network-manager-gnome network-manager-wireguard

# کپی فایل کانفیگ
mkdir -p ~/.config/wireguard
cp client1.conf ~/.config/wireguard/

# از تنظیمات شبکه، Add VPN → Import from file
# فایل client1.conf را انتخاب کنید
```

### 📱 Android (با فایل کانفیگ)

1. فایل `client1.conf` را روی گوشی کپی کنید
2. اپلیکیشن WireGuard را باز کنید
3. روی **+** بزنید
4. گزینه **"Create from file or archive"** را انتخاب کنید
5. فایل `client1.conf` را انتخاب کنید
6. سوییچ را فعال کنید

### 🍎 iOS (با فایل کانفیگ)

iOS مستقیماً import فایل را ساپورت نمی‌کند. باید از QR Code یا AirDrop استفاده کنید:

**روش AirDrop:**
1. فایل `client1.conf` را از Mac با AirDrop بفرستید
2. روی فایل بزنید
3. گزینه "Share" → "WireGuard" را انتخاب کنید

**یا از QR Code استفاده کنید (راحت‌تر)**

---

## تنظیمات اختیاری و پیشرفته:

### کاهش MTU (برای شبکه‌های ضعیف):

اگر اتصال قطع و وصل می‌شود، MTU را کاهش دهید:

```ini
[Interface]
PrivateKey = Z7LG524rwRtsllL9V4rbFwFHoRQBajCv5TYmTup0YAw=
Address = 192.168.200.2/24
DNS = 8.8.8.8, 1.1.1.1
MTU = 1380                    # اضافه کنید
```

### استفاده از DNS دلخواه:

```ini
DNS = 10.202.10.202, 10.202.10.102    # شکن DNS
DNS = 403.online, 403.online          # سرور DNS ایرانی
DNS = 1.1.1.1, 1.0.0.1               # Cloudflare
```

### فقط ترافیک خاص از VPN عبور کند:

اگر می‌خواهید فقط ترافیک خاص از VPN عبور کند، نه همه:

```ini
# به جای 0.0.0.0/0 بنویسید:
AllowedIPs = 192.168.200.0/24, 8.8.8.8/32

# این فقط ترافیک به شبکه VPN و 8.8.8.8 را از VPN می‌فرستد
```

### افزودن چند سرور:

می‌توانید چند کانفیگ مختلف داشته باشید:

1. فایل‌های جدا بسازید: `server1.conf`, `server2.conf`
2. هر کدام را جداگانه import کنید
3. بین آن‌ها سوییچ کنید

---

## تست اتصال:

بعد از اتصال، این تست‌ها را انجام دهید:

### 1. Ping به Gateway VPN:

```bash
ping 192.168.200.1
```

**باید پاسخ دریافت کنید:**
```
PING 192.168.200.1: 56 data bytes
64 bytes from 192.168.200.1: icmp_seq=0 ttl=64 time=15 ms
```

### 2. بررسی IP عمومی:

```bash
curl https://ifconfig.me
# یا
curl https://api.ipify.org
```

**باید IP سرور (2.187.7.240) را ببینید**

### 3. تست DNS:

```bash
nslookup google.com
```

**باید از DNS سرور VPN استفاده کند**

### 4. تست سرعت:

از سایت‌های زیر:
- https://fast.com
- https://speedtest.net

---

## مشکلات رایج و راه‌حل:

### ❌ اتصال برقرار نمی‌شود

**علل احتمالی:**
1. Endpoint اشتباه است
2. فایروال کلاینت پورت UDP را بلاک می‌کند
3. سرور down است

**راه‌حل:**
```bash
# بررسی دسترسی به سرور
ping 2.187.7.240

# اگر ping جواب نداد، سرور یا شبکه مشکل دارد
```

### ❌ اتصال برقرار می‌شود اما اینترنت ندارد

**علل احتمالی:**
1. AllowedIPs اشتباه است
2. DNS کار نمی‌کند
3. NAT سرور مشکل دارد

**راه‌حل:**
```bash
# تست با IP مستقیم
ping 8.8.8.8

# اگر جواب داد، DNS مشکل دارد
# DNS را به 1.1.1.1 تغییر دهید

# اگر جواب نداد، مشکل از سرور است
```

### ❌ سرعت خیلی کند است

**راه‌حل:**
1. MTU را کاهش دهید (1380 یا 1280)
2. سرور نزدیک‌تر انتخاب کنید
3. PersistentKeepalive را به 15 کاهش دهید

### ❌ اتصال قطع و وصل می‌شود

**راه‌حل:**
```ini
# در کانفیگ اضافه کنید:
PersistentKeepalive = 15    # کاهش به 15 ثانیه
MTU = 1280                  # کاهش MTU
```

---

## نکات امنیتی مهم:

⚠️ **کلید خصوصی را با کسی به اشتراک نگذارید**
⚠️ **فایل conf حاوی کلید خصوصی است - محرمانه نگه دارید**
⚠️ **QR code را پس از استفاده حذف کنید**
⚠️ **از VPN عمومی برای کارهای حساس استفاده نکنید**

---

## خلاصه دستورات مفید:

### Windows:
```powershell
# در PowerShell
wireguard.exe /installtunnelservice "C:\path\to\client1.conf"
```

### Linux:
```bash
# اتصال
sudo wg-quick up wg0

# قطع
sudo wg-quick down wg0

# وضعیت
sudo wg show

# لاگ
sudo journalctl -u wg-quick@wg0 -f
```

### macOS:
```bash
# اتصال از Terminal
wg-quick up client1

# قطع
wg-quick down client1
```

---

## پشتیبانی:

اگر مشکل داشتید:
1. **CLIENT-SETUP.md** را مطالعه کنید
2. **TROUBLESHOOTING.md** را بررسی کنید
3. لاگ‌های WireGuard را چک کنید

---

**نکته:** برای کلاینت دوم باید کانفیگ جدیدی با IP متفاوت (192.168.200.3) و کلیدهای جدید ایجاد کنید.

راهنمای افزودن کلاینت جدید در **INSTALLATION-GUIDE.md** موجود است.

✅ **حالا آماده استفاده هستید!**
