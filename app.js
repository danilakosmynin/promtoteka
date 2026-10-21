// Поиск, копирование, заполнение полей, избранное, тема и свои промты. Карточки уже есть в HTML (их собирает build.py).
(() => {
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const store = {
  get(k, d){ try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch(e){ return false; } },
};
const SITE = window.SITE || {cats:{}};
const goal = name => { try { if (SITE.metrika && window.ym) ym(+SITE.metrika, "reachGoal", name); } catch(e){} };

// Старые ссылки вида /#Код ведут на страницу раздела
const hash = (() => { try { return decodeURIComponent(location.hash.slice(1)); } catch(e){ return ""; } })();
if (SITE.cats[hash]) { location.replace(SITE.cats[hash]); return; }

// ───────── Тема
$("theme")?.addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  try { localStorage.setItem("theme", root.dataset.theme); } catch(e){}
});

// ───────── Избранное
let favs = store.get("promtoteka:fav", []);
function paintFavs(){
  for (const b of document.querySelectorAll("[data-fav]")) {
    const on = favs.includes(b.dataset.fav);
    b.setAttribute("aria-pressed", on); b.textContent = on ? "★" : "☆";
    b.title = on ? "Убрать из избранного" : "В избранное"; b.setAttribute("aria-label", b.title);
  }
}

// ───────── Свои промты
const KEY = "promtoteka:mine";
let mine = store.get(KEY, []);
const list = $("list");
const pageCat = list ? list.dataset.cat : null;   // "" — главная, иначе название раздела
const mode = () => pageCat === "" ? ({"#moi":"mine", "#izbrannoe":"fav"})[location.hash] || "" : "";

function renderMine(){
  if (!list) return;
  list.querySelectorAll(".item.own").forEach(n => n.remove());
  const items = mine.filter(m => pageCat === "" || m.cat === pageCat);
  list.insertAdjacentHTML("afterbegin", items.map(d => `<article class="item own">
      <div class="head"><h2>${esc(d.title)}</h2><span class="tag own">мой · ${esc(d.cat)}</span></div>
      ${d.desc ? `<p class="desc">${esc(d.desc)}</p>` : ""}
      <pre>${esc(d.text)}</pre>
      <div class="row"><button class="btn" data-copy>Копировать</button><button class="del" data-del="${esc(d.id)}">Удалить</button></div>
    </article>`).join(""));
}

// Быстрые ссылки на главной под поиском: избранное, свои промты и возврат к разделам
function renderTabs(){
  const quick = $("quick");
  if (!quick) return;
  const m = mode(), cur = x => m === x ? ' aria-current="page"' : "";
  const out = [];
  if (m) out.push(`<a class="tab" href="/">← Все разделы</a>`);
  if (favs.length || m === "fav") out.push(`<a class="tab" href="/#izbrannoe"${cur("fav")}>★ Избранное · ${favs.length}</a>`);
  if (mine.length || m === "mine") out.push(`<a class="tab" href="/#moi"${cur("mine")}>Мои промты · ${mine.length}</a>`);
  quick.innerHTML = out.join("");
  quick.hidden = !out.length;
}

// ───────── Поиск (по названию, описанию, тексту и разделу — без надписей на кнопках)
const searchText = el => el._s ??= [...el.querySelectorAll("h2, .desc, pre, .tag")].map(n => n.textContent).join(" ").toLowerCase();
const q = $("q"), count = $("count"), empty = $("empty"), results = $("results"), home = $("home");
function filter(){
  if (!list) return;
  const s = q ? q.value.trim().toLowerCase() : "", m = mode();
  let n = 0;
  for (const el of list.querySelectorAll(".item")) {
    const inMode = m === "mine" ? el.classList.contains("own") : m === "fav" ? favs.includes(el.dataset.path) : true;
    const show = inMode && (!s || searchText(el).includes(s));
    el.hidden = !show; if (show) n++;
  }
  if (count) count.textContent = n ? `Найдено: ${n}` : "";
  // На главной результаты показываются вместо полок с разделами
  if (results && home) { const active = !!(s || m); results.hidden = !active; home.hidden = active; }
  if (empty) {
    empty.hidden = n > 0;
    empty.textContent = s ? "Ничего не найдено. Попробуйте другое слово или откройте раздел."
      : m === "mine" ? "Здесь появятся ваши промты. Добавить свой — внизу главной страницы."
      : m === "fav" ? "Здесь появятся промты, отмеченные звёздочкой ☆." : "Ничего не найдено.";
  }
}
// Кнопку «Развернуть» показываем только у карточек, где текст обрезан
function markLong(){
  for (const b of document.querySelectorAll(".item [data-expand][hidden]")) {
    const box = b.closest(".item"), pre = box.querySelector("pre");
    if (box.hidden || !pre.clientHeight) continue;
    if (pre.scrollHeight > pre.clientHeight + 2) b.hidden = false;
  }
}
const refresh = () => { renderMine(); renderTabs(); paintFavs(); filter(); markLong(); };
q?.addEventListener("input", () => { filter(); markLong(); });
addEventListener("hashchange", () => {
  const h = (() => { try { return decodeURIComponent(location.hash.slice(1)); } catch(e){ return ""; } })();
  if (SITE.cats[h]) { location.replace(SITE.cats[h]); return; }
  refresh();
});
// На странице раздела прокручиваем ряд разделов к текущему
document.querySelector(".tabs [aria-current]")?.scrollIntoView({block: "nearest", inline: "center"});

// ───────── Заполнение полей на странице промта
const pre = document.querySelector(".prompt pre[data-src]");
const inputs = [...document.querySelectorAll("[data-field]")];
const fillKey = pre ? "promtoteka:fill:" + location.pathname : "";
function fillText(){
  let t = pre.dataset.src;
  for (const i of inputs) { const v = i.value.trim(); if (v) t = t.split(`[${i.dataset.field}]`).join(v); }
  return t;
}
function renderFill(){
  if (!pre) return;
  // Подсвечиваем ещё не заполненные места
  let h = esc(pre.dataset.src);
  for (const i of inputs) {
    const v = i.value.trim(), ph = esc(`[${i.dataset.field}]`);
    h = h.split(ph).join(v ? `<mark class="done">${esc(v)}</mark>` : `<mark>${ph}</mark>`);
  }
  pre.innerHTML = h;
  store.set(fillKey, Object.fromEntries(inputs.map(i => [i.dataset.field, i.value])));
}
if (pre && inputs.length) {
  const saved = store.get(fillKey, {});
  for (const i of inputs) { if (saved[i.dataset.field]) i.value = saved[i.dataset.field]; i.addEventListener("input", renderFill); }
  renderFill();
}
const textOf = el => el === pre ? fillText() : el.textContent;

// ───────── Клики: копирование, открыть в нейросети, избранное, ссылки, удаление
// Старый способ копирования: работает и на сайтах без HTTPS, где navigator.clipboard недоступен
function legacyCopy(text){
  const ta = document.createElement("textarea");
  ta.value = text; ta.setAttribute("readonly", "");
  ta.style.cssText = "position:fixed;top:0;left:0;width:1px;height:1px;opacity:0";
  document.body.appendChild(ta);
  ta.select(); ta.setSelectionRange(0, text.length);   // setSelectionRange нужен для iOS
  let ok = false;
  try { ok = document.execCommand("copy"); } catch(e){}
  ta.remove();
  return ok;
}
function copy(text, btn, label){
  const ok = () => { if (!btn) return; btn.textContent = "Скопировано"; btn.classList.add("done");
    setTimeout(() => { btn.textContent = label; btn.classList.remove("done"); }, 1500); };
  const fallback = () => legacyCopy(text) ? ok() : false;
  if (!navigator.clipboard || !window.isSecureContext) return Promise.resolve(fallback());
  try { return navigator.clipboard.writeText(text).then(ok, fallback); } catch(e){ return Promise.resolve(fallback()); }
}
const OPEN = {
  chatgpt: t => "https://chatgpt.com/?q=" + encodeURIComponent(t),
  claude: t => "https://claude.ai/new?q=" + encodeURIComponent(t),
  alice: () => "https://alice.yandex.ru/",   // текст из ссылки Алиса не подставляет — он уже в буфере обмена
};
const PASTE_ONLY = {alice: "Скопировано — вставьте в чат Алисы"};

document.addEventListener("click", e => {
  const c = e.target.closest("[data-copy]");
  if (c) {
    const box = c.closest(".item, .prompt").querySelector("pre");
    const text = textOf(box);
    copy(text, c, "Копировать").then(r => {
      if (r === false) { const rng = document.createRange(); rng.selectNodeContents(box);
        const sel = getSelection(); sel.removeAllRanges(); sel.addRange(rng); c.textContent = "Выделено — нажмите Ctrl+C"; }
    });
    goal("copy");
    return;
  }
  const o = e.target.closest("[data-open]");
  if (o) {
    const text = textOf(pre);
    copy(text);   // на случай, если сервис не подставит текст из ссылки
    window.open(OPEN[o.dataset.open](text), "_blank", "noopener");
    const hint = PASTE_ONLY[o.dataset.open];
    if (hint) { const label = o.textContent; o.textContent = hint; o.classList.add("done");
      setTimeout(() => { o.textContent = label; o.classList.remove("done"); }, 4000); }
    goal("open_" + o.dataset.open);
    return;
  }
  const x = e.target.closest("[data-expand]");
  if (x) { const open = x.closest(".item").classList.toggle("open"); x.textContent = open ? "Свернуть ↑" : "Полностью ↓"; return; }
  const f = e.target.closest("[data-fav]");
  if (f) {
    const p = f.dataset.fav;
    favs = favs.includes(p) ? favs.filter(x => x !== p) : [p, ...favs];
    store.set("promtoteka:fav", favs);
    refresh();
    return;
  }
  const l = e.target.closest("[data-copylink]");
  if (l) { copy(l.dataset.copylink, l, "Скопировать ссылку"); return; }
  if (e.target.closest("[data-reset]")) { inputs.forEach(i => i.value = ""); renderFill(); inputs[0]?.focus(); return; }
  const d = e.target.closest("[data-del]");
  if (d) {
    if (!d.classList.contains("confirm")) {
      d.classList.add("confirm"); d.textContent = "Точно удалить?";
      setTimeout(() => { if (d.isConnected) { d.classList.remove("confirm"); d.textContent = "Удалить"; } }, 3000);
      return;
    }
    mine = mine.filter(m => m.id !== d.dataset.del);
    store.set(KEY, mine); refresh();
  }
});

// ───────── Форма добавления своего промта
const form = $("form");
if (form) {
  const note = (t, err) => { $("f-note").textContent = t; $("f-note").classList.toggle("err", !!err); };
  form.addEventListener("submit", e => {
    e.preventDefault();
    const title = $("f-title").value.trim(), text = $("f-text").value.trim();
    if (!title || !text) { note("Заполните название и текст промта.", true); return; }
    const item = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
      title, text, cat: $("f-cat").value || "Мои",
      desc: $("f-desc").value.trim(), created: Date.now()
    };
    mine = [item, ...mine];
    if (!store.set(KEY, mine)) { mine = mine.slice(1); note("Браузер не даёт сохранить (приватный режим?).", true); return; }
    $("f-title").value = ""; $("f-desc").value = ""; $("f-text").value = "";
    note(`Сохранено. Промт появился во вкладке «Мои промты» под поиском${item.cat !== "Мои" ? ` и в разделе «${item.cat}»` : ""}.`);
    refresh();
  });
}

refresh();
})();
