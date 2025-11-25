# راهنمای دانلود تصاویر واقعی ساختمان‌های تویو ایتو

## ⚠️ توجه مهم
به دلیل محدودیت‌های شبکه در محیط فعلی، نمی‌توانم مستقیماً تصاویر را دانلود کنم. لطفاً از لینک‌های زیر تصاویر با کیفیت بالا را دانلود کنید.

---

## 📸 لینک‌های تصاویر واقعی (Wikimedia Commons - لایسنس آزاد)

### 1️⃣ Sendai Mediatheque (سندای مدیاتک)

**تصویر پیشنهادی:**
- **لینک مستقیم**: https://upload.wikimedia.org/wikipedia/commons/c/cb/Sendai_Mediatheque_2009.jpg
- **لینک صفحه**: https://commons.wikimedia.org/wiki/File:Sendai_Mediatheque_2009.jpg
- **کیفیت**: 857 × 1,280 پیکسل
- **لایسنس**: Creative Commons CC0 1.0 Universal Public Domain Dedication
- **ذخیره به عنوان**: `images/sendai-mediatheque.jpg`

**تصاویر جایگزین با کیفیت بالاتر:**
- https://commons.wikimedia.org/wiki/File:Sendai_Mediatheque_2022_(1).jpg (6,000 × 4,000 پیکسل)
- https://commons.wikimedia.org/wiki/File:Sendai_Mediatheque_taken_from_Jozenji_Street.jpg

---

### 2️⃣ Taichung Metropolitan Opera House (اپرا هاوس تایچونگ)

**تصویر پیشنهادی:**
- **لینک مستقیم**: https://upload.wikimedia.org/wikipedia/commons/f/f5/Taichung_Metropolitan_Opera_House.JPG
- **لینک صفحه**: https://commons.wikimedia.org/wiki/File:Taichung_Metropolitan_Opera_House.JPG
- **کیفیت**: 1,134 × 851 پیکسل
- **لایسنس**: Creative Commons Attribution-Share Alike 3.0 Unported
- **ذخیره به عنوان**: `images/taichung-opera.jpg`

**تصاویر جایگزین:**
- https://commons.wikimedia.org/wiki/File:National_Taichung_Theater,_Nov_2024_(5).jpg (4,080 × 3,072)
- https://commons.wikimedia.org/wiki/Category:National_Taichung_Theater (16 تصویر مختلف)

---

### 3️⃣ TOD'S Omotesando Building (ساختمان تودز اوموتساندو)

**تصویر پیشنهادی:**
- **لینک مستقیم**: https://upload.wikimedia.org/wikipedia/commons/a/ad/Tod%27s_at_Omotesando.jpg
- **لینک صفحه**: https://commons.wikimedia.org/wiki/File:Tod's_at_Omotesando.jpg
- **کیفیت**: 3,000 × 2,250 پیکسل
- **لایسنس**: Creative Commons Attribution-Share Alike 3.0 Unported
- **ذخیره به عنوان**: `images/tods-omotesando.jpg`

**دسته‌بندی تصاویر بیشتر:**
- https://commons.wikimedia.org/wiki/Category:Tod%27s_Omotesando_Building (4 تصویر)

---

## 🛠️ روش دانلود دستی

### گزینه 1: دانلود مستقیم از مرورگر
1. روی هر لینک مستقیم کلیک کنید
2. تصویر را با کلیک راست ذخیره کنید (Save Image As...)
3. در پوشه `images/` با نام مشخص شده ذخیره کنید

### گزینه 2: استفاده از wget (در ترمینال)
```bash
cd /home/user/algorithm-research-project

# Sendai Mediatheque
wget -O images/sendai-mediatheque.jpg "https://upload.wikimedia.org/wikipedia/commons/c/cb/Sendai_Mediatheque_2009.jpg"

# Taichung Opera House
wget -O images/taichung-opera.jpg "https://upload.wikimedia.org/wikipedia/commons/f/f5/Taichung_Metropolitan_Opera_House.JPG"

# TOD'S Omotesando
wget -O images/tods-omotesando.jpg "https://upload.wikimedia.org/wikipedia/commons/a/ad/Tod%27s_at_Omotesando.jpg"
```

### گزینه 3: استفاده از curl
```bash
cd /home/user/algorithm-research-project

# Sendai Mediatheque
curl -L -o images/sendai-mediatheque.jpg "https://upload.wikimedia.org/wikipedia/commons/c/cb/Sendai_Mediatheque_2009.jpg"

# Taichung Opera House
curl -L -o images/taichung-opera.jpg "https://upload.wikimedia.org/wikipedia/commons/f/f5/Taichung_Metropolitan_Opera_House.JPG"

# TOD'S Omotesando
curl -L -o images/tods-omotesando.jpg "https://upload.wikimedia.org/wikipedia/commons/a/ad/Tod%27s_at_Omotesando.jpg"
```

---

## ✅ پس از دانلود

بعد از دانلود تصاویر، برای بروزرسانی فایل PDF، دستور زیر را اجرا کنید:

```bash
cd /home/user/algorithm-research-project
python3 convert_to_pdf.py toyo-ito-structural-analysis.md
```

---

## 📝 اطلاعات لایسنس

همه تصاویر از Wikimedia Commons با لایسنس آزاد (Creative Commons) هستند:
- **CC0 1.0**: استفاده بدون محدودیت، نیازی به ذکر منبع نیست
- **CC BY-SA 3.0**: استفاده آزاد با ذکر منبع و انتشار مشابه

---

## 🔗 منابع بیشتر

- **ArchDaily**: https://www.archdaily.com (تصاویر با کیفیت بالا اما کپی‌رایت دارد)
- **Flickr Creative Commons**: https://www.flickr.com/creativecommons/
- **Unsplash**: https://unsplash.com/s/photos/sendai

---

**تاریخ آخرین بروزرسانی**: نوامبر 2025
