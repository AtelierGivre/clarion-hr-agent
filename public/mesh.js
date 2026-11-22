(() => {
  const canvas = document.getElementById("mesh");
  if (!canvas) return;
  const front = document.getElementById("mesh-front");
  const glow = document.querySelector(".cursor-glow");
  const backdrop = document.querySelector(".backdrop");
  const ctx = canvas.getContext("2d");
  const fctx = front ? front.getContext("2d") : null;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const coarse = window.matchMedia("(pointer: coarse)");
  const ICE = "185, 236, 255";
  const AMBER = "255, 216, 161";

  const state = {
    w: 0,
    h: 0,
    nodes: [],
    raf: 0,
    mouse: { x: 0, y: 0, tx: 0, ty: 0, active: false, moved: 0 },
    trail: [],
    ripples: [],
  };

  function nodeCount() {
    const base = (state.w * state.h) / 21000;
    return Math.round(Math.min(82, Math.max(coarse.matches ? 24 : 38, base)));
  }

  function resizeLayer(layer, context, dpr) {
    if (!layer || !context) return;
    layer.width = Math.round(state.w * dpr);
    layer.height = Math.round(state.h * dpr);
    layer.style.width = `${state.w}px`;
    layer.style.height = `${state.h}px`;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function resize() {
    state.w = window.innerWidth;
    state.h = window.innerHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    resizeLayer(canvas, ctx, dpr);
    resizeLayer(front, fctx, dpr);

    state.nodes = Array.from({ length: nodeCount() }, () => ({
      x: Math.random() * state.w,
      y: Math.random() * state.h,
      vx: (Math.random() - 0.5) * 0.13,
      vy: (Math.random() - 0.5) * 0.13,
      r: Math.random() * 1.2 + 0.5,
      a: 0.3 + Math.random() * 0.34,
      tone: Math.random() < 0.12 ? AMBER : ICE,
      phase: Math.random() * Math.PI * 2,
    }));
    state.trail.length = 0;
    state.ripples.length = 0;

    if (reduce.matches) draw();
  }

  function drift(node, t) {
    node.x += node.vx + Math.sin(t * 0.3 + node.y * 0.01) * 0.04;
    node.y += node.vy + Math.cos(t * 0.26 + node.x * 0.01) * 0.04;
    if (node.x < -30) node.x = state.w + 30;
    if (node.x > state.w + 30) node.x = -30;
    if (node.y < -30) node.y = state.h + 30;
    if (node.y > state.h + 30) node.y = -30;
  }

  function drawAmbient(now) {
    const { w, h, nodes } = state;
    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";

    const reach = w < 760 ? 126 : 168;
    const breathe = 0.86 + 0.14 * Math.sin(now * 0.0009);

    ctx.lineWidth = 0.8;
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        if (Math.abs(dx) > reach || Math.abs(dy) > reach) continue;
        const d = Math.hypot(dx, dy);
        if (d > reach) continue;
        const alpha = Math.min(0.3, (1 - d / reach) * 0.2 * breathe);
        ctx.strokeStyle = `rgba(${ICE}, ${alpha.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }

    for (const node of nodes) {
      const pulse = 0.82 + 0.18 * Math.sin(now * 0.0016 + node.phase);
      ctx.fillStyle = `rgba(${node.tone}, ${(node.a * pulse).toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawInteraction(now) {
    if (!fctx) return;
    const { w, h, nodes, mouse, trail } = state;
    fctx.clearRect(0, 0, w, h);
    const hover = mouse.active && !reduce.matches;
    const hasRipples = state.ripples.length > 0;
    if (!hover && !hasRipples) return;

    fctx.globalCompositeOperation = "lighter";
    const mx = mouse.x;
    const my = mouse.y;
    const linkReach = w < 760 ? 126 : 168;
    const hoverReach = w < 760 ? 170 : 250;

    if (hover) {
      fctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          if (Math.abs(dx) > linkReach || Math.abs(dy) > linkReach) continue;
          if (Math.hypot(dx, dy) > linkReach) continue;
          const cd = Math.hypot(mx - (a.x + b.x) * 0.5, my - (a.y + b.y) * 0.5);
          if (cd > hoverReach) continue;
          const near = 1 - cd / hoverReach;
          const alpha = near * near * 0.58;
          if (alpha < 0.015) continue;
          fctx.strokeStyle = `rgba(${ICE}, ${alpha.toFixed(3)})`;
          fctx.beginPath();
          fctx.moveTo(a.x, a.y);
          fctx.lineTo(b.x, b.y);
          fctx.stroke();
        }
      }

      for (const node of nodes) {
        const d = Math.hypot(mx - node.x, my - node.y);
        if (d > hoverReach) continue;
        const near = 1 - d / hoverReach;
        fctx.lineWidth = 1;
        fctx.strokeStyle = `rgba(${ICE}, ${(near * 0.4).toFixed(3)})`;
        fctx.beginPath();
        fctx.moveTo(mx, my);
        fctx.lineTo(node.x, node.y);
        fctx.stroke();

        fctx.fillStyle = `rgba(${node.tone}, ${(near * 0.16).toFixed(3)})`;
        fctx.beginPath();
        fctx.arc(node.x, node.y, node.r + 5, 0, Math.PI * 2);
        fctx.fill();
        fctx.fillStyle = `rgba(${node.tone}, ${(0.55 + near * 0.45).toFixed(3)})`;
        fctx.beginPath();
        fctx.arc(node.x, node.y, node.r + near, 0, Math.PI * 2);
        fctx.fill();
      }

      const halo = fctx.createRadialGradient(mx, my, 0, mx, my, 170);
      halo.addColorStop(0, `rgba(${ICE}, 0.1)`);
      halo.addColorStop(0.45, `rgba(${ICE}, 0.035)`);
      halo.addColorStop(1, `rgba(${ICE}, 0)`);
      fctx.fillStyle = halo;
      fctx.beginPath();
      fctx.arc(mx, my, 170, 0, Math.PI * 2);
      fctx.fill();

      const spin = now * 0.0004;
      const reticle = 16;
      fctx.lineWidth = 1;
      fctx.strokeStyle = `rgba(${ICE}, 0.55)`;
      fctx.beginPath();
      fctx.arc(mx, my, reticle, spin, spin + Math.PI * 1.15);
      fctx.stroke();
      fctx.strokeStyle = `rgba(${ICE}, 0.26)`;
      fctx.beginPath();
      fctx.arc(mx, my, reticle, spin + Math.PI, spin + Math.PI * 2.15);
      fctx.stroke();
      fctx.strokeStyle = `rgba(${ICE}, 0.45)`;
      fctx.beginPath();
      fctx.moveTo(mx - reticle - 5, my);
      fctx.lineTo(mx - reticle - 1.5, my);
      fctx.moveTo(mx + reticle + 1.5, my);
      fctx.lineTo(mx + reticle + 5, my);
      fctx.moveTo(mx, my - reticle - 5);
      fctx.lineTo(mx, my - reticle - 1.5);
      fctx.moveTo(mx, my + reticle + 1.5);
      fctx.lineTo(mx, my + reticle + 5);
      fctx.stroke();
      fctx.fillStyle = `rgba(${ICE}, 0.9)`;
      fctx.beginPath();
      fctx.arc(mx, my, 1.7, 0, Math.PI * 2);
      fctx.fill();

      let live = 0;
      fctx.lineWidth = 1.4;
      for (let i = 1; i < trail.length; i++) {
        const age = 1 - (now - trail[i].t) / 520;
        if (age <= 0) continue;
        live = i;
        fctx.strokeStyle = `rgba(${ICE}, ${(age * 0.42).toFixed(3)})`;
        fctx.beginPath();
        fctx.moveTo(trail[i - 1].x, trail[i - 1].y);
        fctx.lineTo(trail[i].x, trail[i].y);
        fctx.stroke();
      }
      if (live === 0) state.trail = [];
    } else {
      state.trail = [];
    }

    fctx.lineWidth = 1.2;
    for (const ripple of state.ripples) {
      const p = (now - ripple.t) / 760;
      if (p >= 1) continue;
      fctx.strokeStyle = `rgba(${ICE}, ${(0.34 * (1 - p)).toFixed(3)})`;
      fctx.beginPath();
      fctx.arc(ripple.x, ripple.y, 12 + p * 150, 0, Math.PI * 2);
      fctx.stroke();
    }
  }

  function draw(now = performance.now()) {
    drawAmbient(now);
    state.ripples = state.ripples.filter((ripple) => now - ripple.t < 760);
    drawInteraction(now);
  }

  function frame(now) {
    if (reduce.matches) {
      state.raf = 0;
      return;
    }
    state.raf = requestAnimationFrame(frame);
    if (document.hidden) return;

    const t = now * 0.001;
    const mouse = state.mouse;
    if (mouse.active) {
      mouse.x += (mouse.tx - mouse.x) * 0.26;
      mouse.y += (mouse.ty - mouse.y) * 0.26;
      if (now - mouse.moved < 600) {
        for (const node of state.nodes) {
          const dx = mouse.x - node.x;
          const dy = mouse.y - node.y;
          const d = Math.hypot(dx, dy);
          if (d < 260 && d > 1) {
            const pull = (1 - d / 260) * 0.085;
            node.x += (dx / d) * pull;
            node.y += (dy / d) * pull;
          }
        }
      }
    }

    for (const node of state.nodes) drift(node, t);
    draw(now);
  }

  function start() {
    if (reduce.matches) {
      draw();
      return;
    }
    if (!state.raf) state.raf = requestAnimationFrame(frame);
  }

  let resizeTimer = 0;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(resize, 180);
  });

  reduce.addEventListener?.("change", () => {
    cancelAnimationFrame(state.raf);
    state.raf = 0;
    state.mouse.active = false;
    state.trail.length = 0;
    state.ripples.length = 0;
    if (glow) glow.style.opacity = "0";
    if (backdrop) backdrop.style.transform = "translate3d(0, 0, 0) scale(1.035)";
    if (reduce.matches) draw();
    else start();
  });

  window.addEventListener(
    "pointermove",
    (event) => {
      if (event.pointerType === "touch") {
        if (state.mouse.active) {
          state.mouse.active = false;
          state.trail.length = 0;
          state.ripples.length = 0;
          if (glow) glow.style.opacity = "0";
        }
        return;
      }
      const mouse = state.mouse;
      if (!mouse.active) {
        mouse.x = event.clientX;
        mouse.y = event.clientY;
      }
      mouse.tx = event.clientX;
      mouse.ty = event.clientY;
      mouse.active = true;
      mouse.moved = performance.now();
      state.trail.push({ x: event.clientX, y: event.clientY, t: performance.now() });
      if (state.trail.length > 36) state.trail.shift();

      document.body.classList.add("mouse-active");
      if (glow) {
        glow.style.transform = `translate3d(${event.clientX}px, ${event.clientY}px, 0)`;
        glow.style.opacity = "1";
      }
      if (backdrop && !reduce.matches) {
        const nx = event.clientX / state.w - 0.5;
        const ny = event.clientY / state.h - 0.5;
        backdrop.style.transform =
          `translate3d(${(-nx * 14).toFixed(2)}px, ${(-ny * 10).toFixed(2)}px, 0) scale(1.035)`;
      }
    },
    { passive: true }
  );

  window.addEventListener(
    "pointerdown",
    (event) => {
      if (event.pointerType === "touch") return;
      state.ripples.push({ x: event.clientX, y: event.clientY, t: performance.now() });
      if (state.ripples.length > 4) state.ripples.shift();
    },
    { passive: true }
  );

  document.addEventListener("mouseleave", () => {
    state.mouse.active = false;
    state.trail.length = 0;
    state.ripples.length = 0;
    if (glow) glow.style.opacity = "0";
    if (backdrop) backdrop.style.transform = "translate3d(0, 0, 0) scale(1.035)";
  });

  resize();
  start();
})();
