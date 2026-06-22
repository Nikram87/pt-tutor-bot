# 🚀 Как запустить бота на Railway

Railway — это облачная платформа, которая идеально подходит для Telegram-ботов с webhook.

## Что нужно:
- Аккаунт на [railway.app](https://railway.app) (бесплатно, но нужна карта для верификации)
- Telegram токен (от @BotFather)
- Anthropic API ключ (от console.anthropic.com)

---

## Шаг 1: Создай репозиторий на GitHub

1. На GitHub создай новый публичный репо: `pt-tutor-bot`

2. Загрузи туда файлы:
```
pt-tutor-bot/
├── pt_tutor_bot_railway.py
├── requirements.txt
├── Procfile
└── README.md (можно пропустить)
```

3. **Git команды:**
```bash
git init
git add .
git commit -m "Initial commit: Portuguese tutor bot"
git remote add origin https://github.com/ТВОЙ_НИК/pt-tutor-bot.git
git branch -M main
git push -u origin main
```

---

## Шаг 2: Подключи Railway

1. Зайди на [railway.app](https://railway.app)

2. Нажми **+ New Project** → **Deploy from GitHub**

3. Авторизуй GitHub и выбери репо `pt-tutor-bot`

4. Railway автоматически:
   - Найдёт `requirements.txt` и установит зависимости
   - Найдёт `Procfile` и запустит `gunicorn pt_tutor_bot_railway:app`

---

## Шаг 3: Установи переменные окружения

1. В Railway панели, перейди в **Variables**

2. Добавь три переменные:

```
TELEGRAM_TOKEN = 7123456789:AAH...  (твой токен от BotFather)
ANTHROPIC_API_KEY = sk-ant-...       (твой ключ от Anthropic)
WEBHOOK_URL = https://[ТВОЙ_ДОМЕН].up.railway.app
```

**Где найти WEBHOOK_URL:**
- В Railway панели найди **Settings** → **Domain**
- Там будет что-то типа: `pt-tutor-bot-production.up.railway.app`
- Этот домен = твой `WEBHOOK_URL`

---

## Шаг 4: Настрой Telegram webhook

Когда Railway дал тебе домен и развернул приложение, нужно сказать Telegram куда отправлять сообщения.

**Вариант А: Curl (в терминале)**
```bash
curl -F "url=https://ТВЙ_ДОМЕН.up.railway.app/webhook" \
  "https://api.telegram.org/botТВОЙ_TELEGRAM_TOKEN/setWebhook"
```

**Вариант Б: Python скрипт** (проще)

Создай файл `setup_webhook.py`:

```python
import requests

TELEGRAM_TOKEN = "7123456789:AAH..."  # Вставь свой
WEBHOOK_URL = "https://pt-tutor-bot-production.up.railway.app"  # Вставь свой домен

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
data = {"url": f"{WEBHOOK_URL}/webhook"}

response = requests.post(url, json=data)
print(response.json())
```

Запусти: `python setup_webhook.py`

Если всё работает, увидишь:
```json
{"ok": true, "result": true, "description": "Webhook was set"}
```

---

## ✅ Проверка

1. Найди своего бота в Telegram (по имени, которое дал @BotFather)

2. Напиши `/start` — должно показать меню с кнопками

3. Тестируй все команды: `/vocab`, `/grammar`, `/chat`, `/quiz`

4. В Railway панели смотри **Logs** (там видны все запросы и ошибки)

---

## 💰 Цена

Railway: **$5/месяц** (первые 100 часов бесплатно)

Это дешевле, чем PythonAnywhere!

---

## 🆘 Если что-то не работает

**Проверь Logs в Railway:**
- Ошибки обычно видны там
- Самые частые: неправильный TOKEN или WEBHOOK_URL

**Проверь webhook:**
```bash
curl https://api.telegram.org/botТВОЙ_TOKEN/getWebhookInfo
```

Должно показать что-то типа:
```json
{
  "ok": true,
  "result": {
    "url": "https://твой-домен.up.railway.app/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 🔄 Как обновить код

Когда захочешь изменить бота:

1. Измени файл локально
2. Git push:
```bash
git add .
git commit -m "Update bot"
git push
```

3. Railway автоматически перезагрузит приложение! 🚀

---

## Альтернативы Railway

### **Render** (бесплатно, но медленнее)
- Создай аккаунт на render.com
- Новый Web Service → GitHub
- Выбери репо
- Webhook работает, но фри версия может быть медленнее

### **PythonAnywhere** (если всё же выберешь)
- Нужен платный аккаунт для webhook ($7/мес)
- Сложнее с настройкой
- Я не рекомендую для этого проекта

---

**Готово!** Теперь твой бот живёт в облаке и работает 24/7 🎉
