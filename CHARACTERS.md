# Character Library — 스키마 (틀만 준비된 상태)

`characters.json` / `character-loader.js` / `characters/index.html` 는
[effects.json 팩](README.md)과 같은 저장소에 있지만 **완전히 별도의 라이브러리**다.
서로의 id 공간을 공유하지 않고, 뷰어 링크도 따로다 (`characters/index.html`).

리소스가 아직 없다 — `characters.json` 의 `assets` 는 `[]`. 아래 스키마대로 항목을
채우면 `characters/index.html` 은 고칠 필요 없이 그대로 그리드에 표시한다.

## 폴더

```
characters.json          매니페스트
character-loader.js      로더 (CharacterLib — loader.js 의 캐릭터 버전)
characters/
  index.html              뷰어 (effects 뷰어와 같은 디자인 시스템, 별도 링크)
  humanoid/               인간형 스프라이트 원본
  monster/                몬스터형 스프라이트 원본
```

카테고리를 늘리려면 `characters.json` 의 `categories` 맵에 키를 추가하고
`characters/<새 카테고리>/` 폴더를 만들면 된다. 뷰어의 칩은 그 맵에서 자동으로 뽑힌다.

## 매니페스트 형식

두 가지 모양을 다 받는다. **어느 쪽이 맞을지는 실제 리소스를 받아 봐야 안다** —
그래서 로더가 둘 다 지원하도록 만들어 놓았다.

### A. 캐릭터당 애니메이션 1개 (effects.json 항목과 똑같은 모양)

```json
{
  "id": "villager_m",
  "name": "마을 남자",
  "category": "humanoid",
  "file": "characters/humanoid/villager_m.png",
  "width": 512, "height": 64,
  "frameWidth": 64, "frameHeight": 64,
  "frames": 8, "cols": 8, "rows": 1,
  "fps": 10,
  "source": "원본 경로"
}
```

### B. 캐릭터당 여러 애니메이션 (idle/walk/attack/hit/death …)

```json
{
  "id": "goblin",
  "name": "고블린",
  "category": "monster",
  "defaultAnimation": "idle",
  "animations": {
    "idle":   { "file": "characters/monster/goblin_idle.png",   "width": 256, "height": 64, "frameWidth": 64, "frameHeight": 64, "frames": 4, "cols": 4, "rows": 1, "fps": 8 },
    "walk":   { "file": "characters/monster/goblin_walk.png",   "width": 384, "height": 64, "frameWidth": 64, "frameHeight": 64, "frames": 6, "cols": 6, "rows": 1, "fps": 10 },
    "attack": { "file": "characters/monster/goblin_attack.png", "width": 320, "height": 64, "frameWidth": 64, "frameHeight": 64, "frames": 5, "cols": 5, "rows": 1, "fps": 12 },
    "hit":    { "file": "characters/monster/goblin_hit.png",    "width": 128, "height": 64, "frameWidth": 64, "frameHeight": 64, "frames": 2, "cols": 2, "rows": 1, "fps": 12 },
    "death":  { "file": "characters/monster/goblin_death.png",  "width": 384, "height": 64, "frameWidth": 64, "frameHeight": 64, "frames": 6, "cols": 6, "rows": 1, "fps": 10 }
  },
  "source": "원본 경로"
}
```

`animations` 가 없으면 A 형식으로, 있으면 B 형식으로 읽는다. 섞어 써도 된다 —
캐릭터마다 필요한 만큼만 애니메이션을 채우면 되고, 리소스가 idle 하나만
있는 캐릭터는 A 형식으로 두면 된다.

필드 의미는 `effects.json` 과 동일 (`README.md` 의 "매니페스트 형식" 참고):
`cols`/`rows` 는 시트 안 프레임 배열, `frames` 는 실제로 재생할 프레임 수
(시트 끝 빈 칸을 잘라내려면 `cols × rows` 보다 작게), `fps` 없으면 12.

## 로더 (`character-loader.js`)

`loader.js`(EffectLib)와 같은 API 감각으로 맞췄다. 차이는 `play()` 에
애니메이션 이름이 하나 더 들어간다는 것뿐:

```html
<script src="./character-loader.js"></script>
<script>
const lib = await CharacterLib.load('./characters.json');
await lib.preload(['goblin']);           // 그 캐릭터의 애니메이션을 전부 미리 받는다

const anim = lib.play('goblin', 'walk', { loop: true });
function frame() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  anim.update().draw(ctx, x, y, { scale: 1.5 });
  requestAnimationFrame(frame);
}
</script>
```

`animations` 없이 A 형식으로 등록한 캐릭터는 애니메이션 이름을 생략해도 된다
(`lib.play('villager_m', { loop: true })` — 내부적으로 `"default"` 클립을 쓴다).

`registerPhaser` / `toPixi` 도 있다 — Phaser 스프라이트시트 키는
`"<캐릭터id>:<애니메이션이름>"` (예: `"goblin:walk"`).

## 리소스가 들어오면 할 일

1. PNG를 `characters/humanoid/` 또는 `characters/monster/` 에 넣는다
   (effects 팩처럼 `tools/build.py` 계열로 자동화해도 되고, 수동으로 넣어도 된다).
2. `characters.json` 의 `assets` 배열에 위 A/B 형식 중 맞는 쪽으로 항목을 추가한다.
3. `characters/index.html` 을 열어 그리드·상세·애니메이션 탭이 뜨는지 확인한다.
   코드를 고칠 필요는 없다 — 데이터만 채우면 된다.
