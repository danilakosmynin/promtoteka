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

# Разделы, где текст — код или параметры, а не промт для чата
NO_CHAT = {"API"}

TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"]))

# Поля, куда обычно вставляют длинный текст, — многострочные
LONG = re.compile(r"вставьте|текст|код|список|описани|заметк|данн|расшифров|план|услови|решени|письм|отзыв|вакан|резюме|материал|документ|стать|изменени|стек|запрос|сценари|рецепт|расход|правила|субтитр|строки|мнение|объяснение|идея|оригинал|перевод", re.I)

# Заполняемое место: [в скобках], с кириллицей и без кавычек и фигурных скобок (чтобы не ловить массивы в коде)
FIELD = re.compile(r"\[([^\[\]\n\"{}]*[а-яё][^\[\]\n\"{}]*)\]", re.I)


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
    ai = " · ".join(f'<a href="/{a["slug"]}/">{e(a["name"])}</a>' for a in ai_pages)
    gd = " · ".join(f'<a href="/{GUIDES_DIR}/{g["slug"]}/">{e(g["h1"])}</a>' for g in guides)
    extra = []
    if CFG.get("telegram_channel"):
        extra.append(f'<a href="{e(CFG["telegram_channel"])}" target="_blank" rel="noopener">Наш Telegram-канал</a>')
    if CFG.get("suggest_url"):
        extra.append(f'<a href="{e(CFG["suggest_url"])}" target="_blank" rel="noopener">Предложить промт</a>')
    extra_html = f'<p>{" · ".join(extra)}</p>\n' if extra else ""
    return f"""<footer>
<p><b>Промты для нейросетей:</b> {ai}</p>
<p><b>Гайды:</b> {gd}</p>
{extra_html}<p>Слова в [квадратных скобках] замените на свои. Названия моделей меняются часто — актуальные смотрите в документации по ссылке. · <a href="/">{NAME}</a></p>
</footer>"""


FOOTER = ""  # заполняется в main()


def page(*, title, desc, path, body, ld=None, og_type="website"):
    url = SITE + path
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
<meta property="og:image" content="{SITE}/og.png?v=2">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg?v=2" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png?v=2" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<link rel="stylesheet" href="/style.css?v=3">{lds}
<script>window.SITE={site_js}</script>
<script src="/app.js?v=5" defer></script>{m_head}
</head>
<body>
{m_body}<div class="wrap">
<div class="top"><a class="logo" href="/"><img src="/favicon.svg?v=2" width="24" height="24" alt="">{NAME}</a>
<nav><a href="/{GUIDES_DIR}/">Гайды</a><button class="theme" id="theme" type="button" aria-label="Сменить тему" title="Сменить тему"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.75a6.25 6.25 0 0 1 0 12.5z" fill="currentColor"/></svg></button></nav></div>
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
    out = [f'<a class="tab" href="/"{" aria-current=\"page\"" if current is None else ""}>Все · {len(prompts)}</a>']
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
    fill = f'<a class="link" href="{p["path"]}">Заполнить поля →</a>' if p["fields"] else ""
    desc = f'<p class="desc">{e(p["desc"])}</p>' if p.get("desc") else ""
    return f"""<article class="item" data-path="{p["path"]}">
<div class="head"><h2><a href="{p["path"]}">{e(p["title"])}</a></h2>{tag}</div>
{desc}<pre>{e(p["text"])}</pre>
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
        p["fields"] = list(dict.fromkeys(FIELD.findall(p["text"])))
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
    picks = f"""<section class="picks" id="picks">
<div><h2>С чего начать</h2>{link_list(start)}</div>
<div><h2>Новое</h2>{link_list(new)}</div>
</section>
""" if new and start else ""
    options = "".join(f"<option>{e(c)}</option>" for c in ["Мои", *CATS])
    body = f"""<header>
<h1>{NAME}</h1>
<p>Готовые промты для ChatGPT, Claude, Gemini, YandexGPT, GigaChat и других нейросетей, а также шпаргалки по их API. Найдите нужное, заполните поля, скопируйте и вставьте.</p>
</header>
""" + listing(prompts, prompts, add=ADD_FORM.format(options=options), picks=picks)
    write("index.html", page(
        title=f"{NAME} — готовые промты для ChatGPT, Claude и других нейросетей",
        desc=f"{len(prompts)} готовых промтов на русском для ChatGPT, Claude, Gemini, YandexGPT и GigaChat: тексты, работа, код, учёба, картинки, видео, а также шпаргалки по API нейросетей.",
        path="/", body=body,
        ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/", "inLanguage": "ru"}]))

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
        total = sum(1 for p in prompts if p["cat"] in a["cats"])
        body = f"""<header>
{crumbs_html([(NAME, "/"), (f"Промты для {a['name']}", None)])}
<h1>Промты для {e(a["name"])}</h1>
</header>
<div class="article">{a["intro"]}</div>
{"".join(blocks)}"""
        write(f"{a['slug']}/index.html", page(
            title=f"Промты для {a['name']} на русском — {total} готовых шаблонов | {NAME}",
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
