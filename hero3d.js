// 3D-логотип на главной: скобки и «печатающиеся» строчки. Загружается из app.js только на главной.
(() => {
const box = document.getElementById("hero3d");
const THREE = window.THREE;
if (!box || !THREE) return;
const still = matchMedia("(prefers-reduced-motion: reduce)").matches;

let renderer;
try { renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: "low-power"}); }
catch (e) { return; }   // нет WebGL — просто без 3D
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.82;
box.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 200);
camera.position.set(0, 0, 78);

// Свет: мягкий общий, тёплый ключевой и холодноватый контровой
scene.add(new THREE.HemisphereLight(0xfff3ea, 0x1a1410, 0.55));
const key = new THREE.DirectionalLight(0xffd9c2, 1.6); key.position.set(-30, 40, 50); scene.add(key);
const rim = new THREE.DirectionalLight(0xc49b84, 1.4); rim.position.set(40, -10, -30); scene.add(rim);
const fill = new THREE.PointLight(0xc49b84, 0.9, 140); fill.position.set(20, -25, 30); scene.add(fill);

const bevel = {depth: 5, bevelEnabled: true, bevelThickness: 1.4, bevelSize: 1.1, bevelSegments: 6, curveSegments: 12};

// Скобка «[»: П-образная форма, повёрнутая боком
function bracket(w, h, t) {
  const s = new THREE.Shape();
  s.moveTo(0, 0); s.lineTo(w, 0); s.lineTo(w, t); s.lineTo(t, t);
  s.lineTo(t, h - t); s.lineTo(w, h - t); s.lineTo(w, h); s.lineTo(0, h); s.lineTo(0, 0);
  const g = new THREE.ExtrudeGeometry(s, bevel);
  g.translate(0, -h / 2, -bevel.depth / 2);
  return g;
}
// Строчка — капсула
function capsule(len, r) {
  const s = new THREE.Shape();
  s.moveTo(0, -r); s.lineTo(len, -r); s.absarc(len, 0, r, -Math.PI / 2, Math.PI / 2, false);
  s.lineTo(0, r); s.absarc(0, 0, r, Math.PI / 2, Math.PI * 1.5, false);
  const g = new THREE.ExtrudeGeometry(s, {...bevel, depth: 3, bevelThickness: 0.9, bevelSize: 0.6});
  g.translate(0, 0, -1.5);
  return g;
}

const cream = new THREE.MeshStandardMaterial({color: 0xe9e1d8, roughness: 0.48, metalness: 0.05});
const mocha = new THREE.MeshStandardMaterial({color: 0x9a5c40, roughness: 0.32, metalness: 0.25, emissive: 0x3a1c0e, emissiveIntensity: 0.35});

const logo = new THREE.Group();
const W = 9, H = 36, T = 5;
const left = new THREE.Mesh(bracket(W, H, T), cream); left.position.x = -19;
const right = new THREE.Mesh(bracket(W, H, T), cream); right.scale.x = -1; right.position.x = 19;
logo.add(left, right);

const lines = [[12, 7], [12, 0], [7, -7]].map(([len, y]) => {
  const m = new THREE.Mesh(capsule(len, 2.1), mocha.clone());
  m.material.transparent = true;
  m.position.set(-6.5, y, 2);
  logo.add(m);
  return m;
});
scene.add(logo);

// Размер холста по контейнеру
function resize() {
  const w = box.clientWidth, h = box.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.position.z = w / h < 0.9 ? 100 : w / h > 2.2 ? 66 : 84;   // на узком экране отодвигаем камеру
  camera.updateProjectionMatrix();
  if (still) renderer.render(scene, camera);   // неподвижный кадр перерисовываем при смене размера
}
resize();
new ResizeObserver(resize).observe(box);

// Поворот за курсором
let tx = 0, ty = 0;
addEventListener("pointermove", e => {
  tx = (e.clientX / innerWidth - 0.5) * 0.9;
  ty = (e.clientY / innerHeight - 0.5) * 0.6;
}, {passive: true});

let visible = true, raf = 0, t0 = performance.now();

function frame(now) {
  const t = (now - t0) / 1000;
  // Строчки «печатаются» по очереди, держатся и гаснут — цикл 4 секунды
  const c = t % 4;
  lines.forEach((m, i) => {
    const k = still ? 1 : Math.min(1, Math.max(0, (c - 0.3 - i * 0.45) / 0.5));
    const e = 1 - Math.pow(1 - k, 3);                                   // плавное замедление
    const fade = still ? 1 : 1 - Math.min(1, Math.max(0, (c - 3.3) / 0.5));
    m.material.opacity = e * fade;
    m.position.x = -6.5 - (1 - e) * 5;                                  // строчка выезжает слева
    m.position.z = 2 + (1 - e) * 4;
    m.visible = m.material.opacity > 0.01;
  });
  const sway = (still ? 0 : Math.sin(t * 0.6) * 0.22) - 0.32;   // слегка развёрнут, чтобы был виден объём
  logo.rotation.y += ((sway + tx) - logo.rotation.y) * 0.06;
  logo.rotation.x += ((ty * 0.8 + (still ? 0 : Math.sin(t * 0.8) * 0.06)) - logo.rotation.x) * 0.06;
  logo.position.y = still ? 0 : Math.sin(t * 1.1) * 1.2;
  renderer.render(scene, camera);
  if (!still && visible && !document.hidden) raf = requestAnimationFrame(frame);
  else raf = 0;
}
const start = () => { if (!raf) raf = requestAnimationFrame(frame); };

// Не рисуем, когда первый экран не виден или вкладка скрыта
new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) start(); }).observe(box);
document.addEventListener("visibilitychange", () => { if (!document.hidden) start(); });
start();
box.classList.add("ready");
})();
