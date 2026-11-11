/* bg-animation.js · Malla fluida de partículas y gradientes neón */
(() => {
  const canvas = document.createElement("canvas");
  canvas.id = "bgCanvas";
  document.body.prepend(canvas);

  const ctx = canvas.getContext("2d");
  let width, height, backgroundGradient, frameId = 0, lastFrame = 0;
  const particles = [];
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    backgroundGradient = null;
  }

  window.addEventListener("resize", resize);
  resize();

  class Particle {
    constructor() {
      this.reset();
    }
    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * 0.4;
      this.vy = (Math.random() - 0.5) * 0.4;
      this.radius = Math.random() * 2 + 1;
      this.alpha = Math.random() * 0.4 + 0.1;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > width || this.y < 0 || this.y > height) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0, 242, 254, ${this.alpha})`;
      ctx.shadowBlur = 6;
      ctx.shadowColor = "#00f2fe";
      ctx.fill();
    }
  }

  const isLowPower = window.innerWidth < 600 || (navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency <= 4);
  const particleCount = isLowPower ? 8 : 16;
  for (let i = 0; i < particleCount; i++) particles.push(new Particle());

  function draw(advance = true) {
    ctx.clearRect(0, 0, width, height);

    if (!backgroundGradient) {
      backgroundGradient = ctx.createRadialGradient(width * 0.5, height * 0.3, 100, width * 0.5, height * 0.5, width * 0.8);
      backgroundGradient.addColorStop(0, "rgba(15, 23, 42, 0.4)");
      backgroundGradient.addColorStop(1, "rgba(7, 9, 19, 0.9)");
    }
    ctx.fillStyle = backgroundGradient;
    ctx.fillRect(0, 0, width, height);

    particles.forEach(particle => {
      if (advance) particle.update();
      particle.draw();
    });
  }

  function animate(timestamp) {
    frameId = 0;
    if (document.hidden || reducedMotion.matches) return;

    if (timestamp - lastFrame >= 1000 / 20) {
      lastFrame = timestamp;
      draw();
    }

    frameId = requestAnimationFrame(animate);
  }

  function syncAnimation() {
    if (document.hidden || reducedMotion.matches) {
      cancelAnimationFrame(frameId);
      frameId = 0;
      draw(false);
      return;
    }

    if (!frameId) {
      lastFrame = 0;
      frameId = requestAnimationFrame(animate);
    }
  }

  document.addEventListener("visibilitychange", syncAnimation);
  reducedMotion.addEventListener("change", syncAnimation);

  resize();
  syncAnimation();
})();