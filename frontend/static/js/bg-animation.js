/* bg-animation.js · Malla fluida de partículas y gradientes neón */
(() => {
  const canvas = document.createElement("canvas");
  canvas.id = "bgCanvas";
  document.body.prepend(canvas);

  const ctx = canvas.getContext("2d");
  let width, height, particles = [];

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
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
      ctx.shadowBlur = 12;
      ctx.shadowColor = "#00f2fe";
      ctx.fill();
    }
  }

  for (let i = 0; i < 45; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, width, height);

    // Fondo ambiental gradiente
    const gradient = ctx.createRadialGradient(width * 0.5, height * 0.3, 100, width * 0.5, height * 0.5, width * 0.8);
    gradient.addColorStop(0, "rgba(15, 23, 42, 0.4)");
    gradient.addColorStop(1, "rgba(7, 9, 19, 0.9)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    particles.forEach(p => {
      p.update();
      p.draw();
    });

    requestAnimationFrame(animate);
  }

  animate();
})();