#!/usr/bin/env python3
"""Собирает статический сайт из папки data/.

Запуск: python3 build.py
Создаёт главную, страницы разделов и промтов, гайды, страницы под нейросети, 404, sitemap.xml и robots.txt.
"""
import datetime
import glob
import html
import json
import os
import re
import shutil
from urllib.parse import quote

SITE = "https://promoteka.tech"
NAME = "Промтотека"
ROOT = os.path.dirname(os.path.abspath(__file__))
GUIDES_DIR = "gaydy"

# Раздел → адрес, заголовок страницы, вступление и как называть промт в <title>
CATS = {
    "Тексты": ("teksty", "Промты для текстов", "Сократить, исправить, переписать, придумать заголовки и написать статью — готовые промты для работы с текстом.", "промт для нейросети"),
    "Работа": ("rabota", "Промты для работы", "Деловые письма, резюме, собеседования, отчёты, встречи и таблицы — промты, которые экономят рабочее время.", "промт для нейросети"),
    "Маркетинг": ("marketing", "Промты для маркетинга", "Посты, контент-план, описания товаров, реклама, рассылки и анализ конкурентов.", "промт для маркетинга"),
    "Код": ("kod", "Промты для программистов", "Объяснить код, найти баг, написать тесты, провести ревью, составить SQL-запрос или регулярное выражение.", "промт для программиста"),
    "Задачи": ("zadachi", "Промты для задач по программированию", "Решить задачу с объяснением, получить подсказку, найти ошибку в решении, ускорить код, придумать тесты — для школы, вуза, олимпиад и собеседований.", "промт для задач"),
    "Учёба": ("ucheba", "Промты для учёбы", "Нейросеть как репетитор: планы изучения, карточки, тесты, конспекты и практика языка.", "промт для учёбы"),
    "Перевод": ("perevod", "Промты для перевода", "Точный перевод, локализация и глоссарий терминов.", "промт для перевода"),
    "Жизнь": ("zhizn", "Промты на каждый день", "Меню, рецепты, поездки, подарки, бюджет и сложные разговоры.", "промт для нейросети"),
    "Изображения": ("izobrazheniya", "Промты для картинок", "Шаблоны для Midjourney, DALL·E, Stable Diffusion и Кандинского: портреты, логотипы, предметное фото, интерьеры.", "промт для генерации картинок"),
    "Видео": ("video", "Промты для видео", "Шаблоны для Sora, Veo, Runway и Kling, сценарии роликов и описания для YouTube.", "промт для видео"),
    "Музыка": ("muzyka", "Промты для музыки", "Промты для Suno и Udio, тексты песен и подготовка текста к озвучке.", "промт для музыки"),
    "Системные": ("sistemnye", "Системные промты", "Готовые инструкции для поля «системный промт»: эксперт, краткие ответы, бот поддержки, ответ в JSON.", "системный промт"),
    "Приёмы": ("priemy", "Приёмы составления промтов", "Как писать промты, чтобы нейросеть отвечала лучше: формулы, примеры, рассуждение по шагам, самопроверка.", "приём промтинга"),
    "API": ("api", "Шпаргалки по API нейросетей", "Готовые запросы к API OpenAI, Claude, Gemini, Mistral, DeepSeek, YandexGPT, GigaChat, Ollama и других: curl, Python, JavaScript.", "пример запроса к API"),
}

# Значок и короткое описание раздела для карточки на главной
CAT_CARD = {
    "Тексты": ("✍️", "Сократить, исправить, переписать, придумать"),
    "Работа": ("💼", "Письма, резюме, отчёты, встречи"),
    "Маркетинг": ("📈", "Посты, реклама, рассылки, описания"),
    "Перевод": ("🌍", "Перевод, локализация, проверка"),
    "Учёба": ("🎓", "Репетитор, конспекты, экзамены"),
    "Код": ("👨‍💻", "Объяснить, отладить, протестировать"),
    "Задачи": ("🧮", "Решения, подсказки, тесты, алгоритмы"),
    "API": ("🔌", "Запросы к OpenAI, Claude, GigaChat"),
    "Изображения": ("🎨", "Midjourney, Stable Diffusion, Кандинский"),
    "Видео": ("🎬", "Сценарии, ролики, Sora и Kling"),
    "Музыка": ("🎵", "Песни для Suno, тексты, озвучка"),
    "Жизнь": ("🏡", "Меню, поездки, покупки, дела"),
    "Приёмы": ("🧠", "Как писать промты, чтобы работало"),
    "Системные": ("⚙️", "Готовые инструкции для нейросети"),
}

# Однотонные значки разделов (24×24, линии цветом текста)
ICONS = {
    "Тексты": '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4z"/><path d="M13.5 6.5l4 4"/>',
    "Работа": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
    "Маркетинг": '<path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1z"/><path d="M15 9a4 4 0 0 1 0 6M18 6a8 8 0 0 1 0 12"/>',
    "Перевод": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3z"/>',
    "Учёба": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5M22 9v6"/>',
    "Код": '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "Задачи": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M14 11h2M8 15h2M14 15h2M8 18h2M14 18h2"/>',
    "API": '<path d="M9 7V3M15 7V3M7 7h10v4a5 5 0 0 1-10 0z"/><path d="M12 16v5"/>',
    "Изображения": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5-5-9 9"/>',
    "Видео": '<rect x="3" y="5" width="13" height="14" rx="2"/><path d="M16 10l5-3v10l-5-3z"/>',
    "Музыка": '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    "Жизнь": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10M10 20v-6h4v6"/>',
    "Приёмы": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
    "Системные": '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
}


def icon(c):
    return f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[c]}</svg>'


# Полки на главной: какие разделы рядом
SHELVES = [
    ("Тексты и работа", ["Тексты", "Работа", "Маркетинг", "Перевод"]),
    ("Учёба и код", ["Учёба", "Код", "Задачи", "API"]),
    ("Творчество и быт", ["Изображения", "Видео", "Музыка", "Жизнь"]),
    ("Мастерство промтов", ["Приёмы", "Системные"]),
]

# Разделы, где текст — код или параметры, а не промт для чата
NO_CHAT = {"API"}

TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"]))

# Поля, куда обычно вставляют длинный текст, — многострочные
LONG = re.compile(r"вставьте|текст|код|список|описани|заметк|данн|расшифров|план|услови|решени|письм|отзыв|вакан|резюме|материал|документ|стать|изменени|стек|запрос|сценари|рецепт|расход|правила|субтитр|строки|мнение|объяснение|идея|оригинал|перевод|diff", re.I)

# Заполняемое место: [в скобках], с буквами и без кавычек и фигурных скобок (чтобы не ловить массивы в коде).
# В разделах с кодом (NO_CHAT) полями считаем только места с кириллицей — иначе поймаем [0], [DONE] и т. п.
FIELD = re.compile(r"\[([^\[\]\n\"{}]*[a-zа-яё][^\[\]\n\"{}]*)\]", re.I)
FIELD_CODE = re.compile(r"\[([^\[\]\n\"{}]*[а-яё][^\[\]\n\"{}]*)\]", re.I)


def slugify(s):
    s = "".join(TRANSLIT.get(c, c) for c in s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def e(s):
    return html.escape(str(s or ""), quote=True)


def cut(s, n=155):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(".,:;—- ") + "…"


def load_json(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


CFG = load_json("site.json")


def metrika():
    """Код счётчика Яндекс Метрики (в <head>) и запасной пиксель для браузеров без JS (в <body>)."""
    i = str(CFG.get("metrika_id") or "").strip()
    if not i:
        return "", ""
    head = f"""
<script>(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){{if(document.scripts[j].src===r){{return;}}}}k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})(window,document,"script","https://mc.yandex.ru/metrika/tag.js?id={i}","ym");
ym({i},"init",{{ssr:true,webvisor:true,clickmap:true,ecommerce:"dataLayer",referrer:document.referrer,url:location.href,accurateTrackBounce:true,trackLinks:true}});</script>"""
    body = f'<noscript><div><img src="https://mc.yandex.ru/watch/{i}" style="position:absolute;left:-9999px" alt=""></div></noscript>\n'
    return head, body


def footer(ai_pages, guides):
    def col(title, links):
        return f'<div><h3>{title}</h3><ul>' + "".join(f'<li><a href="{h}"{x}>{e(t)}</a></li>' for t, h, x in links) + "</ul></div>"
    cats = [(c, f"/{v[0]}/", "") for c, v in CATS.items()]
    ai = [(a["name"], f"/{a['slug']}/", "") for a in ai_pages]
    gd = [(g["h1"], f"/{GUIDES_DIR}/{g['slug']}/", "") for g in guides]
    ext = ' target="_blank" rel="noopener"'
    proj = [("Все разделы", "/#razdely", ""), ("Избранное", "/#izbrannoe", ""), ("Мои промты", "/#moi", "")]
    if CFG.get("telegram_channel"):
        proj.append(("Telegram-канал", CFG["telegram_channel"], ext))
    if CFG.get("suggest_url"):
        proj.append(("Предложить промт", CFG["suggest_url"], ext))
    return f"""<footer>
<div class="fcols">{col("Разделы", cats)}{col("Нейросети", ai)}{col("Гайды", gd)}{col("Проект", proj)}</div>
<p>Слова в [квадратных скобках] замените на свои. Названия моделей меняются часто — актуальные смотрите в документации по ссылке. · © {NAME}</p>
</footer>"""


FOOTER = ""  # заполняется в main()
TOP_CTA = (f'<a class="btn primary sm" href="{e(CFG["telegram_channel"])}" target="_blank" rel="noopener">Промт дня</a>'
           if CFG.get("telegram_channel") else "")

# Вопросы и ответы на главной (и разметка FAQPage для поиска)
FAQ = [
    ("Это бесплатно?", "Да. Все промты открыты, регистрация не нужна. Платить нужно только самим нейросетям, если вы пользуетесь их платными тарифами."),
    ("Для каких нейросетей подходят промты?", "Для любых чат-нейросетей: ChatGPT, Claude, GigaChat, Алиса с YandexGPT, DeepSeek, Gemini. Отдельно есть шаблоны для Midjourney, Stable Diffusion, Suno и шпаргалки по API."),
    ("Что значат слова в [квадратных скобках]?", "Это места, которые нужно заменить своими данными: тему, аудиторию, текст. На странице промта для каждого такого места есть поле — заполните его, и текст обновится сам."),
    ("Как отправить промт в нейросеть?", "Нажмите «Копировать» и вставьте текст в чат. Или нажмите «Открыть в ChatGPT» или «Открыть в Claude» — чат откроется сразу с заполненным промтом. Для Алисы текст копируется, его остаётся вставить."),
    ("Где хранятся мои промты и избранное?", "Только в вашем браузере, на сервер ничего не отправляется. Если очистить данные сайта или открыть его на другом устройстве, списка там не будет."),
]


def page(*, title, desc, path, body, ld=None, og_type="website"):
    url = SITE + path
    if len(title) > 70 and title.endswith(f" | {NAME}"):   # длинный заголовок обрезается в выдаче — убираем хвост
        title = title[: -len(f" | {NAME}")]
    site_js = json.dumps({"cats": {c: f"/{v[0]}/" for c, v in CATS.items()}, "metrika": str(CFG.get("metrika_id") or "")}, ensure_ascii=False)
    m_head, m_body = metrika()
    lds = "".join(f'\n<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png?v=3">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg?v=3" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png?v=3" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=3">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=Unbounded:wght@500;600;700&family=JetBrains+Mono:wght@400&display=swap">
<link rel="stylesheet" href="/style.css?v=17">{lds}
<script>window.SITE={site_js}</script>
<script src="/app.js?v=10" defer></script>{m_head}
</head>
<body>
{m_body}<div class="wrap">
<div class="top"><a class="logo" href="/"><img src="/favicon.svg?v=3" width="24" height="24" alt="">{NAME}</a>
<nav><a href="/#razdely">Разделы</a><a href="/{GUIDES_DIR}/">Гайды</a>{TOP_CTA}<a href="/#izbrannoe" aria-label="Избранное" title="Избранное">★</a><button class="theme" id="theme" type="button" aria-label="Сменить тему" title="Сменить тему"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.75a6.25 6.25 0 0 1 0 12.5z" fill="currentColor"/></svg></button></nav></div>
{body}
{FOOTER}
</div>
</body>
</html>
"""


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + p} for i, (n, p) in enumerate(items)]}


def crumbs_html(items):
    lis = "".join(f'<li><a href="{p}">{e(n)}</a></li>' if p else f"<li>{e(n)}</li>" for n, p in items)
    return f'<ol class="crumbs" aria-label="Навигация">{lis}</ol>'


def tabs(prompts, current):
    out = ['<a class="tab" href="/#razdely">← Все разделы</a>']
    for c, v in CATS.items():
        n = sum(1 for p in prompts if p["cat"] == c)
        cur = ' aria-current="page"' if c == current else ""
        out.append(f'<a class="tab" href="/{v[0]}/"{cur}>{e(c)} · {n}</a>')
    return '<nav class="tabs" id="tabs" aria-label="Разделы">' + "".join(out) + "</nav>"


def fav_btn(p):
    return f'<button class="star" type="button" data-fav="{p["path"]}" aria-pressed="false" title="В избранное" aria-label="В избранное">☆</button>'


def card(p, show_cat=True):
    tag = f'<a class="tag" href="/{CATS[p["cat"]][0]}/">{e(p["cat"])}</a>' if show_cat else ""
    link = f'<a class="link" href="{e(p["link"])}" target="_blank" rel="noopener">Документация →</a>' if p.get("link") else ""
    fill = f'<a class="link" href="{p["path"]}">Заполнить →</a>' if p["fields"] else ""
    desc = f'<p class="desc">{e(p["desc"])}</p>' if p.get("desc") else ""
    more = '<button class="expand" type="button" data-expand hidden aria-label="Показать полностью">Полностью ↓</button>'  # app.js покажет, если текст не влез
    return f"""<article class="item" data-path="{p["path"]}">
<div class="head"><h2><a href="{p["path"]}">{e(p["title"])}</a></h2>{tag}</div>
{desc}<div class="pw"><pre class="clamp">{e(p["text"])}</pre>{more}</div>
<div class="row"><button class="btn" data-copy>Копировать</button>{fill}{link}{fav_btn(p)}</div>
</article>"""


def link_list(items):
    return '<ul class="links">' + "".join(
        f'<li><a href="{p["path"]}">{e(p["title"])}<span>{e(p.get("desc", ""))}</span></a></li>' for p in items) + "</ul>"


def listing(prompts, items, cat=None, search_hint="Поиск: «резюме», «код», «API»…", add="", picks=""):
    return f"""<input id="q" class="search" type="search" placeholder="{e(search_hint)}" aria-label="Поиск">
{tabs(prompts, cat)}
{picks}{add}<p class="count" id="count">Найдено: {len(items)}</p>
<main class="list" id="list" data-cat="{e(cat or "")}">
{"".join(card(p, cat is None) for p in items)}
</main>
<p class="empty" id="empty" hidden></p>"""


ADD_FORM = """<details class="add" id="add">
<summary>Добавить свой промт</summary>
<form id="form" autocomplete="off">
<div class="field"><label for="f-title">Название</label><input id="f-title" required maxlength="120" placeholder="Например: Ответ на отзыв клиента"></div>
<div class="grid2">
<div class="field"><label for="f-cat">Раздел</label><select id="f-cat">{options}</select></div>
<div class="field"><label for="f-desc">Коротко, для чего (необязательно)</label><input id="f-desc" maxlength="200" placeholder="Одна строка"></div>
</div>
<div class="field"><label for="f-text">Текст промта</label><textarea id="f-text" required maxlength="8000" placeholder="Заменяемые места пишите в [квадратных скобках]"></textarea></div>
<div class="row">
<button class="btn primary" type="submit">Сохранить</button>
<p class="note" id="f-note">Ваши промты сохраняются только в этом браузере.</p>
</div>
</form>
</details>
"""


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_guides():
    guides = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "guides", "*.html"))):
        with open(path, encoding="utf-8") as f:
            head, body = f.read().split("\n---\n", 1)
        meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
        guides.append({"slug": os.path.splitext(os.path.basename(path))[0], "body": body.strip(), **meta})
    order = ["kak-pisat-promty", "kakuyu-neyroset-vybrat", "promty-dlya-kartinok", "kak-nachat-rabotat-s-api"]
    guides.sort(key=lambda g: order.index(g["slug"]) if g["slug"] in order else 99)
    return guides


def round_robin(items, key):
    """Чередует элементы по ключу, чтобы в подборке были разные разделы."""
    groups = {}
    for x in items:
        groups.setdefault(key(x), []).append(x)
    out, lists = [], list(groups.values())
    while any(lists):
        for l in lists:
            if l:
                out.append(l.pop(0))
    return out


def check_links(urls):
    """Проверяет, что все внутренние ссылки ведут на существующие страницы."""
    bad = []
    for path in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(path, ROOT)
        if rel.startswith(("data", ".git")):
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for href in re.findall(r'href="(/[^"#?]*)', text):
            ok = href in urls if href.endswith("/") else os.path.exists(os.path.join(ROOT, href.lstrip("/")))
            if not ok:
                bad.append((rel, href))
    if bad:
        raise SystemExit("Битые ссылки:\n" + "\n".join(f"  {p}: {h}" for p, h in sorted(set(bad))))


def main():
    global FOOTER
    prompts = load_json("prompts.json")
    ai_pages = load_json("ai.json")
    guides = load_guides()
    FOOTER = footer(ai_pages, guides)

    seen = set()
    by_title = {}
    for p in prompts:
        if p["cat"] not in CATS:
            raise SystemExit(f"Неизвестный раздел «{p['cat']}» у промта «{p['title']}» — добавьте его в CATS в build.py")
        base = slug = slugify(p["title"])
        i = 2
        while (p["cat"], slug) in seen:
            slug = f"{base}-{i}"; i += 1
        seen.add((p["cat"], slug))
        p["path"] = f"/{CATS[p['cat']][0]}/{slug}/"
        p["fields"] = list(dict.fromkeys((FIELD_CODE if p["cat"] in NO_CHAT else FIELD).findall(p["text"])))
        by_title[p["title"]] = p

    def by_titles(titles, where):
        missing = [t for t in titles if t not in by_title]
        if missing:
            raise SystemExit(f"В {where} нет таких промтов: {missing}")
        return [by_title[t] for t in titles]

    # Убираем старые сгенерированные страницы, чтобы не оставались удалённые
    for d in [v[0] for v in CATS.values()] + [GUIDES_DIR] + [a["slug"] for a in ai_pages]:
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)

    urls = ["/"]

    # Главная
    new = sorted((p for p in prompts if p.get("added")), key=lambda p: p["added"], reverse=True)
    new = round_robin(new, lambda p: p["cat"])[:6]
    start = by_titles(CFG.get("start_here", []), "site.json → start_here")[:6]
    picks = f"""<section class="panel picks" id="picks">
<div><span class="label">[с чего начать]</span>{link_list(start)}</div>
<div><span class="label">[новое на сайте]</span>{link_list(new)}</div>
</section>
""" if new and start else ""
    options = "".join(f"<option>{e(c)}</option>" for c in ["Мои", *CATS])
    count = {c: sum(1 for p in prompts if p["cat"] == c) for c in CATS}
    missing = (set(CATS) - {c for _, cs in SHELVES for c in cs}) | (set(CATS) - set(ICONS))
    if missing:
        raise SystemExit(f"Разделам не хватает полки (SHELVES) или значка (ICONS) в build.py: {missing}")
    shelves = "".join(
        f'<section class="shelf"><h3>{e(t)}</h3><div class="cats">' + "".join(
            f'<a class="cat" href="/{CATS[c][0]}/"><span class="ico">{icon(c)}</span><span class="txt"><b>{e(c)}</b>'
            f'<span>{e(CAT_CARD[c][1])}</span></span><span class="num">{count[c]}</span></a>' for c in cs) + "</div></section>"
        for t, cs in SHELVES)
    ai_chips = "".join(f'<a class="chip" href="/{a["slug"]}/">{e(a["name"])}</a>' for a in ai_pages)
    guide_cards = "".join(f'<a class="gcard" href="/{GUIDES_DIR}/{g["slug"]}/"><b>{e(g["h1"])}</b><span>{e(cut(g["description"], 90))}</span><i>Читать →</i></a>' for g in guides)
    faq = "".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQ)
    tg = CFG.get("telegram_channel")
    band = f"""<section class="band"><div><span class="label">[telegram-канал]</span><h2 class="h2">Промт дня в Telegram</h2>
<p>Каждый день — один полезный промт с подсказкой, когда он пригодится.</p></div>
<a class="btn dark" href="{e(tg)}" target="_blank" rel="noopener">Подписаться →</a></section>""" if tg else ""
    body = f"""<section class="hero">
<span class="label">[библиотека промтов]</span>
<h1 class="display">Промтотека</h1>
<p class="lead">Готовые промты для нейросетей на русском. Выберите задачу, заполните поля — и откройте промт в ChatGPT, Claude или Алисе одной кнопкой.</p>
<input id="q" class="search" type="search" placeholder="Найти промт: резюме, пост, SQL…" aria-label="Поиск">
<div class="stats"><div><b>{len(prompts)}</b><span>промтов</span></div><div><b>{len(CATS)}</b><span>разделов</span></div><div><b>{len(ai_pages)}</b><span>нейросетей</span></div><div><b>0 ₽</b><span>без регистрации</span></div></div>
</section>
<div class="quick" id="quick"></div>
<section class="results" id="results" hidden>
<p class="count" id="count"></p>
<main class="list" id="list" data-cat="">
{"".join(card(p) for p in prompts)}
</main>
<p class="empty" id="empty" hidden></p>
</section>
<div class="home" id="home">
<section class="panel" id="razdely"><span class="label">[разделы]</span><h2 class="h2">Всё по полкам</h2><div class="shelves">{shelves}</div></section>
<section class="panel alt steps-panel"><span class="label">[как это работает]</span><h2 class="h2">Три шага до ответа</h2>
<ol class="steps">
<li><b>01</b><h3>Выберите промт</h3><p>Найдите задачу поиском или в разделах: письмо, пост, код, картинка.</p></li>
<li><b>02</b><h3>Заполните поля</h3><p>Впишите своё в места <mark>[в скобках]</mark> — текст промта обновится сразу.</p></li>
<li><b>03</b><h3>Откройте в чате</h3><p>Скопируйте или откройте одной кнопкой в ChatGPT, Claude или Алисе.</p></li>
</ol></section>
{picks}<section class="panel"><span class="label">[нейросети]</span><h2 class="h2">Под вашу нейросеть</h2><div class="chips">{ai_chips}</div>
<span class="label gap">[гайды]</span><div class="gcards">{guide_cards}</div></section>
<section class="panel alt faq-panel"><div><span class="label">[вопросы]</span><h2 class="h2">Отвечаем на вопросы</h2><p class="muted">Не нашли ответ — напишите в наш Telegram-канал.</p></div><div class="faqs">{faq}</div></section>
{band}
{ADD_FORM.format(options=options)}</div>"""
    write("index.html", page(
        title=f"{NAME} — готовые промты для ChatGPT, Claude и других нейросетей",
        desc=f"{len(prompts)} готовых промтов на русском для ChatGPT, Claude, Gemini, YandexGPT и GigaChat: тексты, работа, код, учёба, картинки, видео, а также шпаргалки по API нейросетей.",
        path="/", body=body,
        ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/", "inLanguage": "ru"},
            {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}]))

    # Разделы
    for c, (slug, h1, intro, kind) in CATS.items():
        items = [p for p in prompts if p["cat"] == c]
        path = f"/{slug}/"
        urls.append(path)
        body = f"""<header>
{crumbs_html([(NAME, "/"), (c, None)])}
<h1>{e(h1)}</h1>
<p>{e(intro)}</p>
</header>
""" + listing(prompts, items, c, "Поиск в разделе")
        write(f"{slug}/index.html", page(
            title=f"{h1} — {len(items)} готовых шаблонов | {NAME}",
            desc=cut(intro + " Скопируйте и вставьте в ChatGPT, Claude или другую нейросеть."),
            path=path, body=body, ld=[crumbs_ld([(NAME, "/"), (c, path)])]))

        # Страницы промтов
        for i, p in enumerate(items):
            urls.append(p["path"])
            others = (items[i + 1:] + items[:i])[:8]
            link = f'<a class="link" href="{e(p["link"])}" target="_blank" rel="noopener">Документация →</a>' if p.get("link") else ""
            chat = "" if c in NO_CHAT else ('<button class="btn" type="button" data-open="chatgpt">Открыть в ChatGPT</button>'
                                            '<button class="btn" type="button" data-open="claude">Открыть в Claude</button>'
                                            '<button class="btn" type="button" data-open="alice">Открыть в Алисе</button>')
            hint = ("Подставьте свой ключ и название модели из документации."
                    if c in NO_CHAT else
                    "Заполните поля — текст обновится сразу. Затем скопируйте его или откройте в нейросети.")
            fields = ""
            if p["fields"]:
                inputs = []
                for j, f in enumerate(p["fields"]):
                    opts = [o.strip() for o in f.split("/") if o.strip()] if " / " in f else []
                    dl = (f' list="o{j}"><datalist id="o{j}">' + "".join(f"<option>{e(o)}</option>" for o in opts) + "</datalist>") if opts else ">"
                    if LONG.search(f) and not opts:
                        ctl = f'<textarea id="v{j}" data-field="{e(f)}" rows="3"></textarea>'
                    else:
                        ctl = f'<input id="v{j}" data-field="{e(f)}" autocomplete="off"{dl}'
                    inputs.append(f'<div class="field{" wide" if ctl.startswith("<textarea") else ""}"><label for="v{j}">{e(f)}</label>{ctl}</div>')
                fields = (f'<details class="fill" open><summary>Заполнить поля · {len(p["fields"])}</summary>'
                          f'<div class="fill-grid">{"".join(inputs)}</div><button class="del" type="button" data-reset>Очистить поля</button></details>')
            share_url = SITE + p["path"]
            share = (f'<details class="share"><summary class="btn">Поделиться</summary><div>'
                     f'<a href="https://t.me/share/url?url={quote(share_url)}&amp;text={quote(p["title"])}" target="_blank" rel="noopener">Telegram</a>'
                     f'<a href="https://vk.com/share.php?url={quote(share_url)}" target="_blank" rel="noopener">ВКонтакте</a>'
                     f'<button type="button" data-copylink="{share_url}">Скопировать ссылку</button></div></details>')
            body = f"""<header>
{crumbs_html([(NAME, "/"), (c, f"/{slug}/"), (p["title"], None)])}
<h1>{e(p["title"])}</h1>
</header>
<main class="prompt" data-path="{p["path"]}">
{f'<p class="desc">{e(p["desc"])}</p>' if p.get("desc") else ""}
{fields}
<pre data-src="{e(p["text"])}">{e(p["text"])}</pre>
<div class="row"><button class="btn primary" type="button" data-copy>Копировать</button>{chat}{share}{link}{fav_btn(p)}</div>
<p class="hint">{hint}</p>
</main>
<section class="related">
<h2>Ещё в разделе «{e(c)}»</h2>
{link_list(others)}
<p class="hint more"><a class="link" href="/{slug}/">Все промты раздела →</a> · <a class="link" href="/">Все разделы →</a></p>
</section>"""
            write(p["path"].strip("/") + "/index.html", page(
                title=f"{p['title']} — {kind} | {NAME}",
                desc=cut(f"{p.get('desc', '')} {p['text']}"),
                path=p["path"], body=body,
                ld=[crumbs_ld([(NAME, "/"), (c, f"/{slug}/"), (p["title"], p["path"])])]))

    # Гайды
    def guide_list(items):
        return '<ul class="links">' + "".join(
            f'<li><a href="/{GUIDES_DIR}/{g["slug"]}/">{e(g["h1"])}<span>{e(g["description"])}</span></a></li>' for g in items) + "</ul>"
    urls.append(f"/{GUIDES_DIR}/")
    body = f"""<header>
{crumbs_html([(NAME, "/"), ("Гайды", None)])}
<h1>Гайды</h1>
<p>Как писать промты, какую нейросеть выбрать и как начать работать с API — коротко и по делу.</p>
</header>
{guide_list(guides)}"""
    write(f"{GUIDES_DIR}/index.html", page(title=f"Гайды по нейросетям и промтам | {NAME}",
        desc="Как писать промты, какую нейросеть выбрать, как писать промты для картинок и как начать работать с API нейросетей.",
        path=f"/{GUIDES_DIR}/", body=body, ld=[crumbs_ld([(NAME, "/"), ("Гайды", f"/{GUIDES_DIR}/")])]))
    for g in guides:
        path = f"/{GUIDES_DIR}/{g['slug']}/"
        urls.append(path)
        body = f"""<header>
{crumbs_html([(NAME, "/"), ("Гайды", f"/{GUIDES_DIR}/"), (g["h1"], None)])}
<h1>{e(g["h1"])}</h1>
</header>
<article class="article">
{g["body"]}
</article>
<section class="related"><h2>Другие гайды</h2>{guide_list([o for o in guides if o is not g])}</section>"""
        write(path.strip("/") + "/index.html", page(title=f"{g['title']} | {NAME}", desc=g["description"], path=path, body=body, og_type="article",
            ld=[crumbs_ld([(NAME, "/"), ("Гайды", f"/{GUIDES_DIR}/"), (g["h1"], path)]),
                {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["description"],
                 "inLanguage": "ru", "mainEntityOfPage": SITE + path, "publisher": {"@type": "Organization", "name": NAME}}]))

    # Страницы под нейросети
    for a in ai_pages:
        path = f"/{a['slug']}/"
        urls.append(path)
        blocks = []
        for c in a["cats"]:
            all_in = [p for p in prompts if p["cat"] == c]
            blocks.append(f'<section class="related"><h2>{e(CATS[c][1])}</h2>{link_list(all_in[:6])}'
                          f'<p class="hint more"><a class="link" href="/{CATS[c][0]}/">Все {len(all_in)} в разделе «{e(c)}» →</a></p></section>')
        if a["api"]:
            blocks.append(f'<section class="related"><h2>API {e(a["name"])}</h2>{link_list(by_titles(a["api"], "ai.json"))}</section>')
        body = f"""<header>
{crumbs_html([(NAME, "/"), (f"Промты для {a['name']}", None)])}
<h1>Промты для {e(a["name"])}</h1>
</header>
<div class="article">{a["intro"]}</div>
{"".join(blocks)}"""
        write(f"{a['slug']}/index.html", page(
            title=f"Промты для {a['name']} на русском — готовые шаблоны | {NAME}",
            desc=cut(f"Готовые промты для {a['name']} на русском: " + ", ".join(CATS[c][1].lower().replace("промты для ", "").replace("промты на ", "") for c in a["cats"]) + ". Скопируйте, заполните поля и вставьте."),
            path=path, body=body, ld=[crumbs_ld([(NAME, "/"), (f"Промты для {a['name']}", path)])]))

    # 404
    write("404.html", page(title=f"Страница не найдена — {NAME}", desc="Такой страницы нет.", path="/404.html",
        body=f'<header><h1>Страница не найдена</h1><p>Возможно, промт переехал. Посмотрите <a class="link" href="/">все промты</a>.</p></header>\n{tabs(prompts, "")}'))

    today = datetime.date.today().isoformat()
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    check_links(set(urls))
    print(f"Готово: {len(urls)} страниц")


if __name__ == "__main__":
    main()
