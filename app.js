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

function renderTabs(){
  const tabs = $("tabs");
  if (!tabs || pageCat !== "") return;
  tabs.querySelectorAll(".tab.extra").forEach(n => n.remove());
  const extra = [];
  if (favs.length) extra.push(`<a class="tab extra" href="/#izbrannoe" data-mode="fav">★ Избранное · ${favs.length}</a>`);
  if (mine.length) extra.push(`<a class="tab extra" href="/#moi" data-mode="mine">Мои · ${mine.length}</a>`);
  tabs.children[0].insertAdjacentHTML("afterend", extra.join(""));
  for (const t of tabs.querySelectorAll(".tab")) {
    const cur = t === tabs.children[0] ? mode() === "" : t.dataset.mode === mode();
    if (t.dataset.mode || t === tabs.children[0]) cur ? t.setAttribute("aria-current", "page") : t.removeAttribute("aria-current");
  }
}

// ───────── Поиск
const q = $("q"), count = $("count"), empty = $("empty"), picks = $("picks");
function filter(){
  if (!list) return;
  const s = q ? q.value.trim().toLowerCase() : "", m = mode();
  let n = 0;
  for (const el of list.querySelectorAll(".item")) {
    const inMode = m === "mine" ? el.classList.contains("own") : m === "fav" ? favs.includes(el.dataset.path) : true;
    const show = inMode && (!s || el.textContent.toLowerCase().includes(s));
    el.hidden = !show; if (show) n++;
  }
  if (count) count.textContent = n ? `Найдено: ${n}` : "";
  if (picks) picks.hidden = !!(s || m);
  if (empty) {
    empty.hidden = n > 0;
    empty.textContent = s ? "Ничего не найдено. Попробуйте другое слово или раздел «Все»."
      : m === "mine" ? "Здесь появятся ваши промты. Нажмите «Добавить свой промт» выше."
      : m === "fav" ? "Здесь появятся промты, отмеченные звёздочкой ☆." : "Ничего не найдено.";
  }
}
const refresh = () => { renderMine(); renderTabs(); paintFavs(); filter(); };
q?.addEventListener("input", filter);
addEventListener("hashchange", refresh);

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
function copy(text, btn, label){
  const ok = () => { if (!btn) return; btn.textContent = "Скопировано"; btn.classList.add("done");
    setTimeout(() => { btn.textContent = label; btn.classList.remove("done"); }, 1500); };
  try { return navigator.clipboard.writeText(text).then(ok, () => false); } catch(e){ return Promise.resolve(false); }
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
    note("Сохранено. Промт появился в разделе «Мои».");
    refresh();
  });
}

refresh();
})();
