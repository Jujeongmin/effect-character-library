/**
 * EffectLib - sprite library loader for the Nine Corporation effect pack.
 *
 * Framework-agnostic. Works with a raw 2D canvas, and ships helpers for
 * Phaser 3 and PixiJS.
 *
 *   const lib = await EffectLib.load('./effects.json');
 *   const anim = lib.play('mythic_frost_zone', { loop: true });
 *   anim.draw(ctx, x, y);            // call once per frame
 */
(function (global) {
  'use strict';

  function joinPath(base, file) {
    if (!base) return file;
    return base.replace(/\/+$/, '') + '/' + file.replace(/^\/+/, '');
  }

  /** One animated (or still) asset from the manifest. */
  function Asset(entry, baseUrl) {
    Object.assign(this, entry);
    this.url = joinPath(baseUrl, entry.file);
    this.image = null;
    this._promise = null;
  }

  Asset.prototype.load = function () {
    if (this._promise) return this._promise;
    this._promise = new Promise(function (resolve, reject) {
      var img = new Image();
      img.onload = function () { resolve(img); };
      img.onerror = function () { reject(new Error('failed to load ' + this.url)); }.bind(this);
      img.src = this.url;
    }.bind(this)).then(function (img) {
      this.image = img;
      return this;
    }.bind(this));
    return this._promise;
  };

  /** Pixel rect of frame `i` inside the spritesheet. */
  Asset.prototype.frameRect = function (i) {
    var idx = ((i % this.frames) + this.frames) % this.frames;
    return {
      x: (idx % this.cols) * this.frameWidth,
      y: Math.floor(idx / this.cols) * this.frameHeight,
      w: this.frameWidth,
      h: this.frameHeight
    };
  };

  /** A playhead over an Asset. Advances on wall-clock time, not frame count. */
  function Animation(asset, options) {
    options = options || {};
    this.asset = asset;
    this.fps = options.fps || asset.fps || 12;
    this.loop = options.loop !== false;
    this.speed = options.speed || 1;
    this.onComplete = options.onComplete || null;
    this.frame = 0;
    this.finished = false;
    this._elapsed = 0;
    this._last = null;
  }

  Animation.prototype.reset = function () {
    this.frame = 0;
    this.finished = false;
    this._elapsed = 0;
    this._last = null;
    return this;
  };

  /** @param {number} [dtMs] elapsed ms; omit to use the internal clock. */
  Animation.prototype.update = function (dtMs) {
    if (this.finished) return this;
    var now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    if (dtMs == null) {
      dtMs = this._last == null ? 0 : now - this._last;
    }
    this._last = now;

    this._elapsed += dtMs * this.speed;
    var step = 1000 / this.fps;
    while (this._elapsed >= step) {
      this._elapsed -= step;
      this.frame += 1;
      if (this.frame >= this.asset.frames) {
        if (this.loop) {
          this.frame = 0;
        } else {
          this.frame = this.asset.frames - 1;
          this.finished = true;
          this._elapsed = 0;
          if (this.onComplete) this.onComplete(this);
          break;
        }
      }
    }
    return this;
  };

  /**
   * Draw the current frame. `x`/`y` is the CENTER of the frame, which is what
   * effects almost always want (explosion on top of a unit, etc).
   */
  Animation.prototype.draw = function (ctx, x, y, opts) {
    if (!this.asset.image) return this;
    opts = opts || {};
    var r = this.asset.frameRect(this.frame);
    var scale = opts.scale == null ? 1 : opts.scale;
    var w = r.w * scale;
    var h = r.h * scale;
    var rotation = opts.rotation || 0;
    var alpha = opts.alpha == null ? 1 : opts.alpha;

    ctx.save();
    if (alpha !== 1) ctx.globalAlpha *= alpha;
    if (opts.blend) ctx.globalCompositeOperation = opts.blend;
    if (rotation) {
      ctx.translate(x, y);
      ctx.rotate(rotation);
      ctx.drawImage(this.asset.image, r.x, r.y, r.w, r.h, -w / 2, -h / 2, w, h);
    } else {
      ctx.drawImage(this.asset.image, r.x, r.y, r.w, r.h, x - w / 2, y - h / 2, w, h);
    }
    ctx.restore();
    return this;
  };

  function Library(manifest, baseUrl) {
    this.version = manifest.version;
    this.defaultFps = manifest.defaultFps;
    this.baseUrl = baseUrl;
    this.assets = manifest.assets.map(function (e) { return new Asset(e, baseUrl); });
    this._byId = {};
    this.assets.forEach(function (a) { this._byId[a.id] = a; }, this);
  }

  Library.prototype.get = function (id) {
    var a = this._byId[id];
    if (!a) throw new Error('unknown effect id: ' + id);
    return a;
  };

  Library.prototype.has = function (id) { return !!this._byId[id]; };

  Library.prototype.ids = function () { return Object.keys(this._byId); };

  Library.prototype.categories = function () {
    var seen = {};
    this.assets.forEach(function (a) { seen[a.category] = (seen[a.category] || 0) + 1; });
    return seen;
  };

  Library.prototype.byCategory = function (category) {
    return this.assets.filter(function (a) { return a.category === category; });
  };

  Library.prototype.search = function (needle) {
    var q = String(needle).toLowerCase();
    return this.assets.filter(function (a) { return a.id.indexOf(q) !== -1; });
  };

  /** Preload images. Pass ids, an array of Assets, or nothing for everything. */
  Library.prototype.preload = function (which) {
    var list;
    if (!which) list = this.assets;
    else list = which.map(function (w) { return typeof w === 'string' ? this.get(w) : w; }, this);
    return Promise.all(list.map(function (a) { return a.load(); }));
  };

  /** Load the image if needed and return a ready-to-tick Animation. */
  Library.prototype.play = function (id, options) {
    var asset = this.get(id);
    var anim = new Animation(asset, options);
    asset.load();
    return anim;
  };

  /**
   * Register every (or a subset of) asset with a Phaser 3 scene.
   * Call from `preload()`; animations are created on `create()`.
   */
  Library.prototype.registerPhaser = function (scene, ids) {
    var list = ids ? ids.map(function (i) { return this.get(i); }, this) : this.assets;
    list.forEach(function (a) {
      scene.load.spritesheet(a.id, a.url, {
        frameWidth: a.frameWidth,
        frameHeight: a.frameHeight
      });
    });
    scene.load.once('complete', function () {
      list.forEach(function (a) {
        if (a.frames < 2 || scene.anims.exists(a.id)) return;
        scene.anims.create({
          key: a.id,
          frames: scene.anims.generateFrameNumbers(a.id, { start: 0, end: a.frames - 1 }),
          frameRate: a.fps || 12,
          repeat: -1
        });
      });
    });
    return list;
  };

  /** Build a PixiJS AnimatedSprite for one effect (PIXI v7+). */
  Library.prototype.toPixi = function (PIXI, id) {
    var a = this.get(id);
    var base = PIXI.BaseTexture.from(a.url);
    var textures = [];
    for (var i = 0; i < a.frames; i++) {
      var r = a.frameRect(i);
      textures.push(new PIXI.Texture(base, new PIXI.Rectangle(r.x, r.y, r.w, r.h)));
    }
    var sprite = new PIXI.AnimatedSprite(textures);
    sprite.animationSpeed = (a.fps || 12) / 60;
    sprite.anchor.set(0.5);
    return sprite;
  };

  function load(manifestUrl, baseUrl) {
    manifestUrl = manifestUrl || './effects.json';
    if (baseUrl == null) baseUrl = manifestUrl.replace(/[^/]*$/, '');
    return fetch(manifestUrl)
      .then(function (r) {
        if (!r.ok) throw new Error('manifest ' + manifestUrl + ' -> HTTP ' + r.status);
        return r.json();
      })
      .then(function (m) { return new Library(m, baseUrl); });
  }

  var EffectLib = { load: load, Library: Library, Asset: Asset, Animation: Animation };

  if (typeof module !== 'undefined' && module.exports) module.exports = EffectLib;
  global.EffectLib = EffectLib;
})(typeof window !== 'undefined' ? window : globalThis);
