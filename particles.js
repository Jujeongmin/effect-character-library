/**
 * ParticleFX - play the Unity particle recipes in particles.json on a canvas.
 *
 * The recipes were read out of the original Unity prefabs, so the numbers are
 * the artist's: how many particles, how long they live, how fast they leave,
 * how they grow and fade. This runtime is a 2D reading of them - close, not
 * identical, because Unity simulates in 3D.
 *
 *   const fx = await ParticleFX.load('./particles.json', {
 *     resolveTexture: (name) => imageFor(name),   // 'NY_glow_01' -> HTMLImageElement
 *   });
 *   const burst = fx.spawn('blow_M_fire_magical', { x: 200, y: 300 });
 *
 *   // per frame
 *   burst.update(dt);            // dt in seconds
 *   burst.draw(ctx);
 *
 * `unitScale` converts Unity world units to pixels (default 100).
 */
(function (global) {
  'use strict';

  function rand(a, b) { return a + Math.random() * (b - a); }

  /** Sample a flattened MinMaxCurve at normalised time t. */
  function sample(spec, t, fallback) {
    if (!spec) return fallback;
    if (spec.v !== undefined) return spec.v;
    if (spec.min !== undefined) return rand(spec.min, spec.max);
    var keys = spec.keys;
    if (!keys || !keys.length) return fallback;
    if (t <= keys[0][0]) return keys[0][1];
    for (var i = 1; i < keys.length; i++) {
      if (t <= keys[i][0]) {
        var a = keys[i - 1], b = keys[i];
        var span = b[0] - a[0];
        var k = span > 0 ? (t - a[0]) / span : 0;
        return a[1] + (b[1] - a[1]) * k;
      }
    }
    return keys[keys.length - 1][1];
  }

  /** A curve's value at spawn time - ranges roll once, curves read at t=0. */
  function initial(spec, fallback) { return sample(spec, 0, fallback); }

  function sampleGradient(spec, t) {
    if (!spec) return null;
    if (spec.color) return spec.color;
    var stops = spec.stops || [];
    var alpha = spec.alpha || [];
    var rgb = [1, 1, 1];
    if (stops.length) {
      rgb = stops[0][1];
      for (var i = 1; i < stops.length; i++) {
        if (t <= stops[i][0]) {
          var a = stops[i - 1], b = stops[i];
          var span = b[0] - a[0], k = span > 0 ? (t - a[0]) / span : 0;
          rgb = [0, 1, 2].map(function (c) { return a[1][c] + (b[1][c] - a[1][c]) * k; });
          break;
        }
        rgb = stops[i][1];
      }
    }
    var av = 1;
    if (alpha.length) {
      av = alpha[0][1];
      for (var j = 1; j < alpha.length; j++) {
        if (t <= alpha[j][0]) {
          var p = alpha[j - 1], q = alpha[j];
          var s2 = q[0] - p[0], k2 = s2 > 0 ? (t - p[0]) / s2 : 0;
          av = p[1] + (q[1] - p[1]) * k2;
          break;
        }
        av = alpha[j][1];
      }
    }
    return [rgb[0], rgb[1], rgb[2], av];
  }

  /**
   * Canvas cannot tint a drawImage, so keep a coloured copy of the texture.
   * Colours are bucketed to 32 steps per channel to bound the cache; alpha is
   * left to globalAlpha, which varies per particle every frame.
   */
  var tintCache = {};

  function tinted(img, rgb) {
    var r = Math.round(rgb[0] * 31), g = Math.round(rgb[1] * 31), b = Math.round(rgb[2] * 31);
    if (r >= 31 && g >= 31 && b >= 31) return img;
    var w = img.width || img.naturalWidth, h = img.height || img.naturalHeight;
    if (!w || !h || typeof document === 'undefined') return img;
    var key = (img.__tintId || (img.__tintId = ++tinted.seq)) + ':' + r + '_' + g + '_' + b;
    var hit = tintCache[key];
    if (hit) return hit;

    var off = document.createElement('canvas');
    off.width = w;
    off.height = h;
    var c = off.getContext('2d');
    c.drawImage(img, 0, 0);
    c.globalCompositeOperation = 'multiply';
    c.fillStyle = 'rgb(' + Math.round(r / 31 * 255) + ',' + Math.round(g / 31 * 255) +
      ',' + Math.round(b / 31 * 255) + ')';
    c.fillRect(0, 0, w, h);
    c.globalCompositeOperation = 'destination-in';   // put the alpha back
    c.drawImage(img, 0, 0);
    tintCache[key] = off;
    return off;
  }
  tinted.seq = 0;

  /** Particle colour times the material's tint - that is where the hue lives. */
  function multiply(color, tint) {
    var c = color || [1, 1, 1, 1];
    if (!tint) return c.slice();
    return [c[0] * tint[0], c[1] * tint[1], c[2] * tint[2], c[3] * tint[3]];
  }

  /** A launch direction, in the spirit of Unity's shape module. */
  function launch(shape) {
    if (!shape) {
      var a0 = Math.random() * Math.PI * 2;
      return [Math.cos(a0), Math.sin(a0)];
    }
    if (shape.type === 'cone' || shape.type === 'cone_volume') {
      // Unity cones point along +Z; on a 2D stage that reads as "upward".
      var spread = (shape.angle || 25) * Math.PI / 180;
      var a1 = -Math.PI / 2 + rand(-spread, spread);
      return [Math.cos(a1), Math.sin(a1)];
    }
    if (shape.type === 'box' || shape.type === 'edge') {
      return [rand(-1, 1), rand(-0.2, 0.2)];
    }
    var a = Math.random() * Math.PI * 2;
    return [Math.cos(a), Math.sin(a)];
  }

  function Emitter(spec, opts) {
    this.spec = spec;
    this.opts = opts;
    this.particles = [];
    this.age = 0;
    this.pending = 0;
    this.burstsFired = [];
    this.texture = null;
    this.additive = spec.dstBlend !== 10;      // 10 = OneMinusSrcAlpha (alpha blend)
  }

  /**
   * Textures usually arrive after the first frame, so ask again until one
   * turns up rather than deciding at construction time that there is none.
   */
  Emitter.prototype.image = function () {
    if (this.texture) return this.texture;
    if (!this.opts.resolveTexture) return null;
    var img = this.opts.resolveTexture(this.spec.texture);
    if (img && (img.width || img.naturalWidth)) this.texture = img;
    return this.texture;
  };

  Emitter.prototype.emit = function (n) {
    var spec = this.spec, scale = this.opts.unitScale;
    var room = (spec.maxParticles || 200) - this.particles.length;
    n = Math.min(n, Math.max(0, room));
    for (var i = 0; i < n; i++) {
      var dir = launch(spec.shape);
      var speed = initial(spec.speed, 1) * scale;
      var radius = (spec.shape && spec.shape.radius ? spec.shape.radius : 0) * scale;
      this.particles.push({
        x: dir[0] * radius * Math.random(),
        y: dir[1] * radius * Math.random(),
        vx: dir[0] * speed,
        vy: dir[1] * speed,
        life: 0,
        maxLife: Math.max(0.05, initial(spec.lifetime, 1)),
        size: initial(spec.size, 1) * scale,
        rot: (initial(spec.rotation, 0) || 0),
        tint: multiply(sampleGradient(spec.color, 0), spec.tint),
      });
    }
  };

  Emitter.prototype.update = function (dt) {
    var spec = this.spec;
    this.age += dt;
    var duration = spec.duration || 1;
    var running = spec.looping || this.age <= duration;
    var cycle = duration > 0 ? (this.age % duration) / duration : 0;

    if (running && spec.rate) {
      this.pending += sample(spec.rate, cycle, 0) * dt;
      var whole = Math.floor(this.pending);
      if (whole > 0) { this.emit(whole); this.pending -= whole; }
    }
    (spec.bursts || []).forEach(function (b, i) {
      var due = Math.floor(this.age / (duration || 1));
      var key = spec.looping ? due : 0;
      if (this.age % (duration || 1) >= b[0] && this.burstsFired[i] !== key && running) {
        this.burstsFired[i] = key;
        this.emit(b[1]);
      }
    }, this);

    var gravity = sample(spec.gravity, cycle, 0) * this.opts.unitScale * 9.81;
    var vel = spec.velocity;
    var out = [];
    for (var i = 0; i < this.particles.length; i++) {
      var p = this.particles[i];
      p.life += dt;
      if (p.life >= p.maxLife) continue;
      var t = p.life / p.maxLife;
      if (vel) {
        p.vx += sample(vel.x, t, 0) * this.opts.unitScale * dt;
        p.vy -= sample(vel.y, t, 0) * this.opts.unitScale * dt;
      }
      p.vy += gravity * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      out.push(p);
    }
    this.particles = out;
    return this;
  };

  Emitter.prototype.draw = function (ctx, ox, oy) {
    var spec = this.spec, img = this.image();
    if (!img) return this;
    ctx.save();
    ctx.globalCompositeOperation = this.additive ? 'lighter' : 'source-over';
    for (var i = 0; i < this.particles.length; i++) {
      var p = this.particles[i];
      var t = p.life / p.maxLife;
      var s = p.size * sample(spec.sizeOverLife, t, 1);
      if (s <= 0) continue;
      var col = sampleGradient(spec.colorOverLife, t);
      var a = p.tint[3] * (col ? col[3] : 1);
      if (a <= 0.003) continue;
      var paint = tinted(img, col ? multiply(p.tint, [col[0], col[1], col[2], 1]) : p.tint);
      ctx.globalAlpha = Math.min(1, a);
      ctx.setTransform(1, 0, 0, 1, ox + p.x, oy + p.y);
      if (p.rot) ctx.rotate(p.rot);
      ctx.drawImage(paint, -s / 2, -s / 2, s, s);
    }
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    return this;
  };

  function Instance(spec, opts) {
    this.x = opts.x || 0;
    this.y = opts.y || 0;
    this.emitters = spec.emitters.map(function (e) { return new Emitter(e, opts); });
  }

  Instance.prototype.update = function (dt) {
    for (var i = 0; i < this.emitters.length; i++) this.emitters[i].update(dt);
    return this;
  };

  Instance.prototype.draw = function (ctx) {
    for (var i = 0; i < this.emitters.length; i++) this.emitters[i].draw(ctx, this.x, this.y);
    return this;
  };

  Instance.prototype.alive = function () {
    return this.emitters.some(function (e) {
      return e.particles.length || e.spec.looping || e.age <= (e.spec.duration || 1);
    });
  };

  function Library(spec, opts) {
    this.spec = spec;
    this.opts = opts;
  }

  Library.prototype.ids = function () { return Object.keys(this.spec.effects); };

  Library.prototype.has = function (id) { return !!this.spec.effects[id]; };

  Library.prototype.get = function (id) {
    var e = this.spec.effects[id];
    if (!e) throw new Error('unknown particle effect: ' + id);
    return e;
  };

  /** Every texture name the recipes ask for, so a page can preload them. */
  Library.prototype.textures = function () {
    var seen = {};
    Object.keys(this.spec.effects).forEach(function (id) {
      this.spec.effects[id].emitters.forEach(function (e) {
        if (e.texture) seen[e.texture] = (seen[e.texture] || 0) + 1;
      });
    }, this);
    return seen;
  };

  Library.prototype.spawn = function (id, options) {
    options = options || {};
    var opts = {
      x: options.x, y: options.y,
      unitScale: options.unitScale || this.opts.unitScale || 100,
      resolveTexture: options.resolveTexture || this.opts.resolveTexture,
    };
    return new Instance(this.get(id), opts);
  };

  function load(url, options) {
    options = options || {};
    return fetch(url || './particles.json')
      .then(function (r) {
        if (!r.ok) throw new Error('particles.json -> HTTP ' + r.status);
        return r.json();
      })
      .then(function (spec) { return new Library(spec, options); });
  }

  var ParticleFX = { load: load, Library: Library, Instance: Instance, Emitter: Emitter };
  if (typeof module !== 'undefined' && module.exports) module.exports = ParticleFX;
  global.ParticleFX = ParticleFX;
})(typeof window !== 'undefined' ? window : globalThis);
