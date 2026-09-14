/**
 * CharacterLib - character sprite loader for the Nine Corporation asset pack.
 *
 * Sibling of loader.js (EffectLib), same framework-agnostic shape, but a
 * character can carry several named animation clips (idle / walk / attack /
 * hit / death …) instead of exactly one. A character with no `animations`
 * map is treated as a single clip named "default", so old-style flat entries
 * (identical shape to an effects.json asset) still work unchanged.
 *
 *   const lib = await CharacterLib.load('./characters.json');
 *   const anim = lib.play('goblin', 'walk', { loop: true });
 *   anim.draw(ctx, x, y);            // call once per frame
 *
 * See CHARACTERS.md for the manifest schema and how to add an entry.
 */
(function (global) {
  'use strict';

  function joinPath(base, file) {
    if (!base) return file;
    return base.replace(/\/+$/, '') + '/' + file.replace(/^\/+/, '');
  }

  /** One animation clip - a spritesheet plus its playback grid. */
  function Clip(name, entry, baseUrl) {
    Object.assign(this, entry);
    this.name = name;
    this.url = joinPath(baseUrl, entry.file);
    this.image = null;
    this._promise = null;
  }

  Clip.prototype.load = function () {
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

  /** Pixel rect of frame `i` inside this clip's spritesheet. */
  Clip.prototype.frameRect = function (i) {
    var idx = ((i % this.frames) + this.frames) % this.frames;
    return {
      x: (idx % this.cols) * this.frameWidth,
      y: Math.floor(idx / this.cols) * this.frameHeight,
      w: this.frameWidth,
      h: this.frameHeight
    };
  };

  /** A playhead over a Clip. Advances on wall-clock time, not frame count. */
  function Animation(clip, options) {
    options = options || {};
    this.clip = clip;
    this.fps = options.fps || clip.fps || 12;
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
      if (this.frame >= this.clip.frames) {
        if (this.loop) {
          this.frame = 0;
        } else {
          this.frame = this.clip.frames - 1;
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
   * Draw the current frame. `x`/`y` is the CENTER of the frame - same
   * convention as EffectLib, so a character and an effect can be placed with
   * the same math (e.g. an impact effect centered on a character).
   */
  Animation.prototype.draw = function (ctx, x, y, opts) {
    if (!this.clip.image) return this;
    opts = opts || {};
    var r = this.clip.frameRect(this.frame);
    var scale = opts.scale == null ? 1 : opts.scale;
    var w = r.w * scale;
    var h = r.h * scale;
    var rotation = opts.rotation || 0;
    var alpha = opts.alpha == null ? 1 : opts.alpha;
    var flipX = !!opts.flipX;

    ctx.save();
    if (alpha !== 1) ctx.globalAlpha *= alpha;
    if (opts.blend) ctx.globalCompositeOperation = opts.blend;
    ctx.translate(x, y);
    if (rotation) ctx.rotate(rotation);
    if (flipX) ctx.scale(-1, 1);
    ctx.drawImage(this.clip.image, r.x, r.y, r.w, r.h, -w / 2, -h / 2, w, h);
    ctx.restore();
    return this;
  };

  /** One character - a bundle of named Clips (idle/walk/attack/...). */
  function Character(entry, baseUrl) {
    this.id = entry.id;
    this.name = entry.name || entry.id;
    this.category = entry.category;
    this.source = entry.source;
    this.note = entry.note;

    // Flat single-clip shorthand (same shape as an effects.json asset):
    // no `animations` map means the whole entry - minus id/name/category -
    // IS the one clip, filed under "default".
    var animEntries = entry.animations;
    if (!animEntries) {
      var flat = Object.assign({}, entry);
      delete flat.id; delete flat.name; delete flat.category;
      delete flat.source; delete flat.note; delete flat.defaultAnimation;
      animEntries = { 'default': flat };
    }

    this.defaultAnimation = entry.defaultAnimation ||
      (animEntries['default'] ? 'default' : Object.keys(animEntries)[0]);

    this.clips = {};
    this._byName = {};
    for (var name in animEntries) {
      if (!Object.prototype.hasOwnProperty.call(animEntries, name)) continue;
      var clip = new Clip(name, animEntries[name], baseUrl);
      this.clips[name] = clip;
      this._byName[name] = clip;
    }
  }

  Character.prototype.animationNames = function () { return Object.keys(this.clips); };

  Character.prototype.hasAnimation = function (name) { return !!this._byName[name]; };

  Character.prototype.getClip = function (name) {
    var clip = this._byName[name || this.defaultAnimation];
    if (!clip) throw new Error('character "' + this.id + '" has no "' + name + '" animation');
    return clip;
  };

  /** Preload one clip, every clip, or a named subset. */
  Character.prototype.preload = function (names) {
    var list = (names || this.animationNames()).map(function (n) { return this.getClip(n); }, this);
    return Promise.all(list.map(function (c) { return c.load(); }));
  };

  function Library(manifest, baseUrl) {
    this.version = manifest.version;
    this.categories = manifest.categories || {};
    this.baseUrl = baseUrl;
    this.characters = (manifest.assets || []).map(function (e) { return new Character(e, baseUrl); });
    this._byId = {};
    this.characters.forEach(function (c) { this._byId[c.id] = c; }, this);
  }

  Library.prototype.get = function (id) {
    var c = this._byId[id];
    if (!c) throw new Error('unknown character id: ' + id);
    return c;
  };

  Library.prototype.has = function (id) { return !!this._byId[id]; };

  Library.prototype.ids = function () { return Object.keys(this._byId); };

  Library.prototype.categoryLabel = function (key) { return this.categories[key] || key; };

  Library.prototype.byCategory = function (category) {
    return this.characters.filter(function (c) { return c.category === category; });
  };

  Library.prototype.search = function (needle) {
    var q = String(needle).toLowerCase();
    return this.characters.filter(function (c) {
      return c.id.indexOf(q) !== -1 || (c.name || '').toLowerCase().indexOf(q) !== -1;
    });
  };

  /** Load every clip for one, several, or all characters. */
  Library.prototype.preload = function (ids) {
    var list = ids ? ids.map(function (i) { return this.get(i); }, this) : this.characters;
    return Promise.all(list.map(function (c) { return c.preload(); }));
  };

  /** Load the clip if needed and return a ready-to-tick Animation. */
  Library.prototype.play = function (id, animName, options) {
    if (animName && typeof animName === 'object') { options = animName; animName = null; }
    var character = this.get(id);
    var clip = character.getClip(animName);
    var anim = new Animation(clip, options);
    clip.load();
    return anim;
  };

  /**
   * Register every clip of the given (or all) characters with a Phaser 3
   * scene. Spritesheet key is `${characterId}:${animationName}`. Call from
   * `preload()`; animations are created on `create()`.
   */
  Library.prototype.registerPhaser = function (scene, ids) {
    var list = ids ? ids.map(function (i) { return this.get(i); }, this) : this.characters;
    list.forEach(function (c) {
      c.animationNames().forEach(function (n) {
        var clip = c.getClip(n);
        var key = c.id + ':' + n;
        scene.load.spritesheet(key, clip.url, {
          frameWidth: clip.frameWidth,
          frameHeight: clip.frameHeight
        });
      });
    });
    scene.load.once('complete', function () {
      list.forEach(function (c) {
        c.animationNames().forEach(function (n) {
          var clip = c.getClip(n);
          var key = c.id + ':' + n;
          if (clip.frames < 2 || scene.anims.exists(key)) return;
          scene.anims.create({
            key: key,
            frames: scene.anims.generateFrameNumbers(key, { start: 0, end: clip.frames - 1 }),
            frameRate: clip.fps || 12,
            repeat: -1
          });
        });
      });
    });
    return list;
  };

  /** Build a PixiJS AnimatedSprite for one character clip (PIXI v7+). */
  Library.prototype.toPixi = function (PIXI, id, animName) {
    var clip = this.get(id).getClip(animName);
    var base = PIXI.BaseTexture.from(clip.url);
    var textures = [];
    for (var i = 0; i < clip.frames; i++) {
      var r = clip.frameRect(i);
      textures.push(new PIXI.Texture(base, new PIXI.Rectangle(r.x, r.y, r.w, r.h)));
    }
    var sprite = new PIXI.AnimatedSprite(textures);
    sprite.animationSpeed = (clip.fps || 12) / 60;
    sprite.anchor.set(0.5);
    return sprite;
  };

  function load(manifestUrl, baseUrl) {
    manifestUrl = manifestUrl || './characters.json';
    if (baseUrl == null) baseUrl = manifestUrl.replace(/[^/]*$/, '');
    return fetch(manifestUrl)
      .then(function (r) {
        if (!r.ok) throw new Error('manifest ' + manifestUrl + ' -> HTTP ' + r.status);
        return r.json();
      })
      .then(function (m) { return new Library(m, baseUrl); });
  }

  var CharacterLib = { load: load, Library: Library, Character: Character, Clip: Clip, Animation: Animation };

  if (typeof module !== 'undefined' && module.exports) module.exports = CharacterLib;
  global.CharacterLib = CharacterLib;
})(typeof window !== 'undefined' ? window : globalThis);
