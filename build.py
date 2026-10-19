#!/usr/bin/env python3
"""Собирает статический сайт из data/prompts.json.

Запуск: python3 build.py
Создаёт index.html, 404.html, страницу на каждый раздел и каждый промт, sitemap.xml и robots.txt.
"""
import datetime
import html
import json
import os
import re
import shutil

SITE = "https://promoteka.tech"
NAME = "Промтотека"
ROOT = os.path.dirname(os.path.abspath(__file__))

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

TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"]))


def slugify(s):
    s = "".join(TRANSLIT.get(c, c) for c in s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def e(s):
    return html.escape(str(s or ""), quote=True)


def cut(s, n=155):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(".,:;—- ") + "…"


def page(*, title, desc, path, body, ld=None, scripts=True):
    url = SITE + path
    cats_js = json.dumps({c: f"/{v[0]}/" for c, v in CATS.items()}, ensure_ascii=False)
    lds = "".join(f'\n<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    js = f'\n<script>window.CATS={cats_js}</script>\n<script src="/app.js" defer></script>' if scripts else ""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<link rel="stylesheet" href="/style.css">{lds}{js}
</head>
<body>
<div class="wrap">
{body}
<footer>Слова в [квадратных скобках] замените на свои. Названия моделей меняются часто — актуальные смотрите в документации по ссылке. · <a href="/">{NAME}</a></footer>
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


def card(p, show_cat=True):
    tag = f'<a class="tag" href="/{CATS[p["cat"]][0]}/">{e(p["cat"])}</a>' if show_cat else ""
    link = f'<a class="link" href="{e(p["link"])}" target="_blank" rel="noopener">Документация →</a>' if p.get("link") else ""
    desc = f'<p class="desc">{e(p["desc"])}</p>' if p.get("desc") else ""
    return f"""<article class="item">
<div class="head"><h2><a href="{p["path"]}">{e(p["title"])}</a></h2>{tag}</div>
{desc}<pre>{e(p["text"])}</pre>
<div class="row"><button class="btn" data-copy>Копировать</button>{link}</div>
</article>"""


def listing(prompts, items, cat=None, search_hint="Поиск: «резюме», «код», «API»…"):
    return f"""<input id="q" class="search" type="search" placeholder="{e(search_hint)}" aria-label="Поиск">
{tabs(prompts, cat)}
{{ADD}}<p class="count" id="count">Найдено: {len(items)}</p>
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


def main():
    with open(os.path.join(ROOT, "data", "prompts.json"), encoding="utf-8") as f:
        prompts = json.load(f)

    seen = set()
    for p in prompts:
        if p["cat"] not in CATS:
            raise SystemExit(f"Неизвестный раздел «{p['cat']}» у промта «{p['title']}» — добавьте его в CATS в build.py")
        base = slug = slugify(p["title"])
        i = 2
        while (p["cat"], slug) in seen:
            slug = f"{base}-{i}"; i += 1
        seen.add((p["cat"], slug))
        p["path"] = f"/{CATS[p['cat']][0]}/{slug}/"

    # Убираем старые страницы разделов, чтобы не оставались удалённые промты
    for v in CATS.values():
        shutil.rmtree(os.path.join(ROOT, v[0]), ignore_errors=True)

    urls = ["/"]

    # Главная
    options = "".join(f"<option>{e(c)}</option>" for c in ["Мои", *CATS])
    body = f"""<header>
<h1>{NAME}</h1>
<p>Готовые промты для ChatGPT, Claude, Gemini, YandexGPT, GigaChat и других нейросетей, а также шпаргалки по их API. Найдите нужное, скопируйте и вставьте.</p>
</header>
""" + listing(prompts, prompts).replace("{ADD}", ADD_FORM.format(options=options))
    write("index.html", page(
        title=f"{NAME} — готовые промты для ChatGPT, Claude и других нейросетей",
        desc=f"{len(prompts)} готовых промтов на русском для ChatGPT, Claude, Gemini, YandexGPT и GigaChat: тексты, работа, код, учёба, картинки, видео, а также шпаргалки по API нейросетей.",
        path="/", body=body,
        ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/", "inLanguage": "ru"}]))

    # Разделы
    for c, (slug, h1, intro, _) in CATS.items():
        items = [p for p in prompts if p["cat"] == c]
        path = f"/{slug}/"
        urls.append(path)
        cr = [(NAME, "/"), (c, None)]
        body = f"""<header>
{crumbs_html(cr)}
<h1>{e(h1)}</h1>
<p>{e(intro)}</p>
</header>
""" + listing(prompts, items, c, "Поиск в разделе").replace("{ADD}", "")
        write(f"{slug}/index.html", page(
            title=f"{h1} — {len(items)} готовых шаблонов | {NAME}",
            desc=cut(intro + " Скопируйте и вставьте в ChatGPT, Claude или другую нейросеть."),
            path=path, body=body, ld=[crumbs_ld([(NAME, "/"), (c, path)])]))

        # Страницы промтов
        for i, p in enumerate(items):
            urls.append(p["path"])
            kind = CATS[c][3]
            others = (items[i + 1:] + items[:i])[:8]
            rel = "".join(f'<li><a href="{o["path"]}">{e(o["title"])}<span>{e(o.get("desc", ""))}</span></a></li>' for o in others)
            link = f'<a class="link" href="{e(p["link"])}" target="_blank" rel="noopener">Документация →</a>' if p.get("link") else ""
            hint = ("Подставьте свой ключ и название модели из документации."
                    if c == "API" else
                    "Скопируйте текст, замените слова в [квадратных скобках] на свои и отправьте нейросети.")
            body = f"""<header>
{crumbs_html([(NAME, "/"), (c, f"/{slug}/"), (p["title"], None)])}
<h1>{e(p["title"])}</h1>
</header>
<main class="prompt" style="display:flex;flex-direction:column;gap:14px">
{f'<p class="desc">{e(p["desc"])}</p>' if p.get("desc") else ""}
<pre>{e(p["text"])}</pre>
<div class="row"><button class="btn primary" data-copy>Копировать</button>{link}</div>
<p class="hint">{hint}</p>
</main>
<section class="related">
<h2>Ещё в разделе «{e(c)}»</h2>
<ul>{rel}</ul>
<p class="hint" style="margin-top:14px"><a class="link" href="/{slug}/">Все промты раздела →</a> · <a class="link" href="/">Все разделы →</a></p>
</section>"""
            write(p["path"].strip("/") + "/index.html", page(
                title=f"{p['title']} — {kind} | {NAME}",
                desc=cut(f"{p.get('desc', '')} {p['text']}"),
                path=p["path"], body=body,
                ld=[crumbs_ld([(NAME, "/"), (c, f"/{slug}/"), (p["title"], p["path"])])]))

    # 404
    write("404.html", page(title=f"Страница не найдена — {NAME}", desc="Такой страницы нет.", path="/404.html", scripts=False,
        body=f'<header><h1>Страница не найдена</h1><p>Возможно, промт переехал. Посмотрите <a class="link" href="/">все промты</a>.</p></header>\n{tabs(prompts, "")}'))

    today = datetime.date.today().isoformat()
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"Готово: {len(urls)} страниц")


if __name__ == "__main__":
    main()
