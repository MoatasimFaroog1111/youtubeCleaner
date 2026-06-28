# youtubeCleaner

مشروع Python Worker لتنظيف محتوى YouTube غير المناسب للأطفال وتشجيع المحتوى التعليمي.

## النشر على Railway

### 1) تجهيز OAuth محليًا (مرة واحدة)
- شغّل الملف:
  - `python auth_google.py`
- أكمل تسجيل الدخول بحساب Google.
- بعد النجاح سيتولد ملف `token.json`.
- **مهم:** لا تعتمد على تسجيل دخول تفاعلي داخل Railway.

### 2) إنشاء الخدمة على Railway
- New Project → Deploy from GitHub
- اختر المستودع: `MoatasimFaroog1111/youtubeCleaner`
- اختر نوع الخدمة: **Worker / Background service** (ليست Web API).

### 3) Environment Variables المطلوبة
- `LOG_PATH=/tmp/kids_guardian.log`
- `CLEAN_LOG_PATH=/tmp/cleaning_log.json`
- `EDU_LOG_PATH=/tmp/educational_log.json`
- `GOOGLE_CREDENTIALS_FILE=credentials.json`
- `GOOGLE_TOKEN_FILE=token.json`
- `YT_PLAYLIST_ID=...` (اختياري)

### 4) تمرير محتوى ملفات OAuth عبر Variables
- أضف متغيرًا مثل `GOOGLE_CREDENTIALS_JSON` وضع فيه محتوى `credentials.json`.
- أضف متغيرًا مثل `GOOGLE_TOKEN_JSON` وضع فيه محتوى `token.json`.

### 5) Start Command على Railway
استخدم:

```bash
printf "%s" "$GOOGLE_CREDENTIALS_JSON" > credentials.json && printf "%s" "$GOOGLE_TOKEN_JSON" > token.json && touch .env && python main_guardian.py
```

أو اترك Railway يقرأ نفس الأمر من ملف `Procfile` الموجود بالمشروع.

### 6) التحقق بعد النشر
- راقب Logs بعد Deploy.
- تأكد من ظهور بدء الدورة اليومية ونتائج `cleaner` و `educator` بدون أخطاء OAuth.

## ملاحظة مهمة
تخزين Railway غالبًا **ephemeral**، لذلك ملفات `/tmp` (اللوجات والتقارير) قد تضيع بعد إعادة التشغيل، وهذا متوقع.
