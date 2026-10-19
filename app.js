// Поиск, копирование и свои промты. Карточки базовых промтов уже есть в HTML (их собирает build.py).
(() => {
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const list = $("list");
const CATS = window.CATS || {};   // название раздела → адрес страницы

// Старые ссылки вида /#Код ведут на страницу раздела
const hash = (() => { try { return decodeURIComponent(location.hash.slice(1)); } catch(e){ return ""; } })();
if (CATS[hash]) { location.replace(CATS[hash]); return; }

// ───────── Свои промты (хранятся в браузере)
const KEY = "promtoteka:mine";
let mine = [];
try { mine = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch(e){ mine = []; }
const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(mine)); return true; } catch(e){ return false; } };

const pageCat = list ? list.dataset.cat : null;     // "" — главная, иначе название раздела
const onlyMine = () => pageCat === "" && location.hash === "#moi";

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
  const tabs = $("tabs");
  if (tabs && pageCat === "") {
    tabs.querySelector(".tab.mine")?.remove();
    if (mine.length) {
      tabs.children[0].insertAdjacentHTML("afterend", `<a class="tab mine" href="/#moi">Мои · ${mine.length}</a>`);
      const all = tabs.children[0], my = tabs.querySelector(".tab.mine");
      if (onlyMine()) { all.removeAttribute("aria-current"); my.setAttribute("aria-current", "page"); }
      else { all.setAttribute("aria-current", "page"); my.removeAttribute("aria-current"); }
    }
  }
}

// ───────── Поиск
const q = $("q"), count = $("count"), empty = $("empty");
function filter(){
  if (!list) return;
  const s = q ? q.value.trim().toLowerCase() : "";
  let n = 0;
  for (const el of list.querySelectorAll(".item")) {
    const show = (!onlyMine() || el.classList.contains("own")) && (!s || el.textContent.toLowerCase().includes(s));
    el.hidden = !show; if (show) n++;
  }
  if (count) count.textContent = n ? `Найдено: ${n}` : "";
  if (empty) {
    empty.hidden = n > 0;
    empty.textContent = onlyMine() && !s ? "Здесь появятся ваши промты. Нажмите «Добавить свой промт» выше." : "Ничего не найдено. Попробуйте другое слово или раздел «Все».";
  }
}
q?.addEventListener("input", filter);
addEventListener("hashchange", () => { renderMine(); filter(); });

// ───────── Копирование и удаление
document.addEventListener("click", e => {
  const c = e.target.closest("[data-copy]");
  if (c) {
    const pre = c.closest(".item, .prompt").querySelector("pre");
    const ok = () => { c.textContent = "Скопировано"; c.classList.add("done");
      setTimeout(() => { c.textContent = "Копировать"; c.classList.remove("done"); }, 1500); };
    const fallback = () => { const r = document.createRange(); r.selectNodeContents(pre);
      const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); c.textContent = "Выделено — нажмите Ctrl+C"; };
    try { navigator.clipboard.writeText(pre.textContent).then(ok, fallback); } catch(err){ fallback(); }
    return;
  }
  const d = e.target.closest("[data-del]");
  if (d) {
    if (!d.classList.contains("confirm")) {
      d.classList.add("confirm"); d.textContent = "Точно удалить?";
      setTimeout(() => { if (d.isConnected) { d.classList.remove("confirm"); d.textContent = "Удалить"; } }, 3000);
      return;
    }
    mine = mine.filter(m => m.id !== d.dataset.del);
    persist(); renderMine(); filter();
  }
});

// ───────── Форма добавления
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
    if (!persist()) { mine = mine.slice(1); note("Браузер не даёт сохранить (приватный режим?).", true); return; }
    $("f-title").value = ""; $("f-desc").value = ""; $("f-text").value = "";
    note("Сохранено. Промт появился в разделе «Мои».");
    renderMine(); filter();
  });
}

renderMine(); filter();
})();
