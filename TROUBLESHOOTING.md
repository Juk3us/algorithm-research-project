# راهنمای عیب‌یابی: کلاینت متصل می‌شود اما ترافیک دریافت نمی‌کند

این راهنما به حل مشکل "اتصال برقرار است اما Receive صفر است" کمک می‌کند.

## علائم مشکل

- کلاینت به VPN متصل می‌شود
- Handshake موفق است
- ترافیک ارسالی (TX/Sent) افزایش می‌یابد
- **ترافیک دریافتی (RX/Received) صفر است**
- پینگ به سرور جواب نمی‌دهد

## علل احتمالی و راه‌حل

### 1. بررسی اتصال WireGuard در سرور

ابتدا وضعیت WireGuard را در MikroTik بررسی کنید:

```bash
# اتصال به MikroTik
ssh admin@YOUR_MIKROTIK_IP

# بررسی interface WireGuard
/interface wireguard print

# بررسی peers
/interface wireguard peers print detail

# بررسی آخرین handshake
/interface wireguard peers print stats
```

**چیزهایی که باید ببینید:**
- Interface باید `running` باشد
- Peer باید `current-endpoint-address` داشته باشد
- `last-handshake` باید کمتر از 3 دقیقه پیش باشد
- `rx` و `tx` هر دو باید مقداری داشته باشند

### 2. بررسی Allowed Address در Peer

**مشکل**: اگر `allowed-address` در peer محدود باشد، سرور نمی‌تواند به کلاینت پاسخ دهد.

**راه‌حل**: Allowed address باید شامل IP کلاینت باشد:

```bash
# بررسی allowed-address
/interface wireguard peers print

# اگر فقط IP خاص کلاینت را می‌بینید، درست است:
# allowed-address=192.168.200.2/32

# اگر نیاز به دسترسی به شبکه‌های دیگر دارید:
/interface wireguard peers set [find public-key="HRnO/GFu1WFeYWkmsU65riEUPJrDvWnU//Q69bTKmQA="] allowed-address=192.168.200.2/32
```

### 3. بررسی و تصحیح Firewall Rules

**مشکل شایع**: Firewall ترافیک برگشتی به کلاینت را بلاک می‌کند.

```bash
# بررسی firewall rules
/ip firewall filter print

# بررسی آمار drop ها
/ip firewall filter print stats

# غیرفعال موقت firewall برای تست (فقط برای تست!)
/ip firewall filter disable [find]

# اگر بعد از غیرفعال کردن کار کرد، firewall مشکل دارد
```

**راه‌حل**: اضافه کردن قوانین مناسب:

```bash
# اطمینان از accept شدن ترافیک از WireGuard interface
/ip firewall filter
add action=accept chain=output out-interface=wireguard-vpn place-before=0 comment="Allow output to VPN"
add action=accept chain=input in-interface=wireguard-vpn place-before=0 comment="Allow input from VPN"
add action=accept chain=forward in-interface=wireguard-vpn place-before=0 comment="Allow forward from VPN"
add action=accept chain=forward out-interface=wireguard-vpn connection-state=established,related place-before=0 comment="Allow return traffic to VPN"
```

### 4. بررسی NAT

**مشکل**: NAT برای کلاینت‌های VPN کار نمی‌کند.

```bash
# بررسی NAT rules
/ip firewall nat print

# بررسی connections
/ip firewall connection print where src-address~"192.168.200"
```

**باید این rule را ببینید:**
```
action=masquerade chain=srcnat src-address=192.168.200.0/24 out-interface=ether5-internet
```

**اگر نیست، اضافه کنید:**
```bash
/ip firewall nat
add action=masquerade chain=srcnat src-address=192.168.200.0/24 out-interface=ether5-internet comment="NAT: VPN to Internet"
```

### 5. بررسی Routing

**مشکل**: مسیر برگشت به کلاینت VPN مشکل دارد.

```bash
# بررسی routing table
/ip route print detail where dst-address=0.0.0.0/0

# بررسی routing برای شبکه VPN
/ip route print where dst-address~"192.168.200"
```

**راه‌حل**: اطمینان از وجود مسیر به شبکه VPN:

```bash
# این مسیر باید به صورت خودکار ایجاد شود، اما اگر نبود:
/ip route
add dst-address=192.168.200.0/24 gateway=wireguard-vpn
```

### 6. بررسی Interface ether5 (Internet)

**مشکل**: پورت 5 که برای خروجی اینترنت VPN است، IP ندارد یا down است.

```bash
# بررسی وضعیت interface
/interface print stats where name=ether5-internet

# بررسی IP address
/ip address print where interface=ether5-internet

# بررسی DHCP client
/ip dhcp-client print detail where interface=ether5-internet
```

**راه‌حل**:
- اطمینان از اتصال فیزیکی کابل
- اطمینان از دریافت IP از DHCP
- در صورت نیاز، IP استاتیک تنظیم کنید

### 7. تست با ابزار داخلی MikroTik

```bash
# از سرور MikroTik به IP کلاینت VPN پینگ کنید
/ping 192.168.200.2 count=10

# اگر پینگ جواب داد، مشکل در routing یا firewall forward است
# اگر پینگ جواب نداد، مشکل در WireGuard یا peer configuration است
```

### 8. بررسی MTU

**مشکل**: MTU بزرگ باعث drop شدن پکت‌ها می‌شود.

```bash
# کاهش MTU در WireGuard interface
/interface wireguard set wireguard-vpn mtu=1380
```

در سمت کلاینت هم MTU را کاهش دهید (در فایل conf):
```ini
[Interface]
MTU = 1380
```

### 9. کانفیگ کامل پیشنهادی برای رفع مشکل

اگر همه چیز درست است اما باز هم کار نمی‌کند، این کانفیگ را امتحان کنید:

```bash
# 1. ریست کردن WireGuard peer
/interface wireguard peers remove [find interface=wireguard-vpn]
/interface wireguard peers add \
    interface=wireguard-vpn \
    public-key="HRnO/GFu1WFeYWkmsU65riEUPJrDvWnU//Q69bTKmQA=" \
    allowed-address=192.168.200.2/32 \
    comment="Client 1"

# 2. اضافه کردن Firewall rules در اولویت بالا
/ip firewall filter
add action=accept chain=input in-interface=wireguard-vpn place-before=0 comment="Accept from VPN"
add action=accept chain=forward connection-state=established,related place-before=0 comment="Accept established"
add action=accept chain=forward in-interface=wireguard-vpn place-before=0 comment="Forward from VPN"
add action=accept chain=forward out-interface=wireguard-vpn place-before=0 comment="Forward to VPN"

# 3. اطمینان از NAT
/ip firewall nat
add action=masquerade chain=srcnat out-interface=ether5-internet comment="Masquerade all to Internet"

# 4. اضافه کردن Mangle برای mark routing (اختیاری)
/ip firewall mangle
add action=mark-routing chain=prerouting src-address=192.168.200.0/24 new-routing-mark=vpn-traffic comment="Mark VPN traffic"

/ip route
add dst-address=0.0.0.0/0 gateway=ether5-internet routing-mark=vpn-traffic comment="VPN traffic via Internet"
```

## 10. لاگ‌های مفید

```bash
# فعال کردن debug logging برای WireGuard
/system logging
add topics=wireguard action=memory
add topics=firewall,info action=memory

# مشاهده لاگ‌ها
/log print where topics~"wireguard"
/log print where topics~"firewall"
```

## 11. تست نهایی

بعد از اعمال تغییرات:

```bash
# از سرور
/ping 192.168.200.2 src-address=192.168.200.1

# از کلاینت
ping 192.168.200.1
ping 8.8.8.8
curl https://ifconfig.me
```

## خلاصه مراحل عیب‌یابی

1. ✅ بررسی handshake موفق است
2. ✅ بررسی allowed-address شامل IP کلاینت است
3. ✅ بررسی firewall ترافیک را بلاک نمی‌کند
4. ✅ بررسی NAT فعال است
5. ✅ بررسی routing درست است
6. ✅ بررسی interface ether5 up و دارای IP است
7. ✅ تست ping از سرور به کلاینت
8. ✅ کاهش MTU در صورت نیاز

## توجه

اگر همچنان مشکل حل نشد، این اطلاعات را جمع‌آوری و بررسی کنید:

```bash
/interface wireguard print detail
/interface wireguard peers print detail
/ip firewall filter print
/ip firewall nat print
/ip route print detail
/ip address print
/interface print stats
/log print where topics~"wireguard"
```

این خروجی‌ها به تشخیص دقیق‌تر مشکل کمک می‌کنند.
