# Effect Library

Nine Corporation 게임의 이펙트 리소스를 **웹 게임에서 바로 쓸 수 있는 형태**로 변환한 팩입니다.
원본 PSD / GIF / Unity `.unitypackage` 를 전부 PNG 스프라이트시트 + JSON 매니페스트로 정리했습니다.

```
Effects/
  viewer.html     ← 더블클릭하면 열립니다. 서버 필요 없음
  effects/        이펙트 스프라이트시트 87개
  singles/        단일 이미지 114개 (파티클 재료)
  particles.json  Unity 프리팹에서 뽑은 파티클 설계 209개
  particles.js    그 설계를 캔버스에서 재생하는 런타임
  effects.json    매니페스트 — 프레임 크기·개수·fps
  loader.js       로더 (canvas / Phaser 3 / PixiJS)
  tools/          재빌드용 스크립트 (원본이 있을 때만 필요)
```

## 먼저 볼 것

`viewer.html` 을 더블클릭하세요. **410개가 한 격자에** 나오고, id 검색·카테고리 필터가 됩니다.
카드의 **COPY** 버튼을 누르면 id가 바로 복사되고, 카드 그림을 누르면 프레임 하나하나와
붙여넣을 코드가 나옵니다.

카테고리 칩 맨 앞의 **전체** 를 누르면 필터가 풀립니다. 애니메이션만 보려면
`단일 이미지` 외의 칩을 고르세요.

셀 배경을 **어둠 / 체커 / 밝음**으로 바꿀 수 있습니다. 체커는 알파(투명도) 확인용,
밝음은 밝은 맵 위에 얹었을 때 어떻게 보이는지 확인용입니다.

## 뷰어에서 코드로 옮기기

카드를 클릭하면 나오는 버튼 세 개는 쓰임새가 다릅니다.

| 버튼 | 복사되는 것 | 언제 쓰나 |
|---|---|---|
| **COPY** (카드 위) | `mythic_frost_zone` | 목록에서 바로 id만 복사 |
| **id 복사** (상세) | `mythic_frost_zone` | 코드에서 이펙트를 부르는 이름. AI에게 시킬 때도 이것을 넣습니다 |
| **경로 복사** | `effects/mythic_frost_zone.png` | 로더 없이 PNG를 직접 로드하거나 파일 하나만 옮길 때 |

흐름은 **검색 → 클릭 → id 복사 → 붙여넣기** 입니다.

### AI에게 시킬 때

처음 한 번, 프로젝트에 붙이는 프롬프트:

```
RB-Effects 폴더를 프로젝트에 넣었어. effects/ 와 effects.json, loader.js 가 있어.
loader.js 를 로드하고 effects.json 을 읽어서 이펙트를 재생할 수 있게 붙여줘.
```

그다음부터는 **id + 언제 + 어디에**를 적으면 됩니다:

```
적이 죽을 때 deatheffect 를 적 위치에 한 번 재생하고 끝나면 없애줘.
frost_zone 을 클릭한 자리에 3초 동안 반복 재생해줘. 크기는 1.5배.
플레이어가 스킬 쓰면 thor_thunder 를 적 머리 위에서 한 번 재생해줘.
```

뭘 쓸지 모르겠으면 매니페스트를 가리키면 됩니다. 201개의 id·프레임 수·크기·fps가
`effects.json` 한 파일(35 KB)에 다 들어 있어서 목록을 직접 읽고 고릅니다:

```
effects.json 에서 explosion 카테고리 중 제일 짧은 걸 골라서
총알이 벽에 맞을 때 재생해줘.
```

id는 정확히 복사해서 넣으세요 — `frost_zone` 과 `frost` 는 다른 이펙트입니다.

## 구성

카테고리는 원본 폴더 이름이 아니라 **실제로 어떻게 보이는지** 기준입니다.
(원본은 폭발·번개·링이 전부 `02_장판` 한 폴더에 들어 있었습니다.)

**애니메이션 87개** — 프레임이 여러 장이라 그대로 재생됩니다.

| 카테고리 | 개수 | 내용 |
|---|---|---|
| `impact` 피격 | 18 | 맞는 순간 터지고 사라지는 것 — 타격, 도탄, 흡수, 서리, 피 |
| `lightning` 번개 | 14 | 낙뢰, 전기 아크, 번개 룬 서클 |
| `misc` 기타 | 12 | 슬래시, 섬광, 연기 |
| `projectile` 투사체 | 12 | 화살, 마나볼, 펫, 토르, 티르 |
| `explosion` 폭발 | 11 | 화구가 터져 연기로 흩어지는 것 |
| `zone` 장판 | 11 | 바닥에 깔려 지속되는 것만 — 독, 서리 |
| `aura` 아우라 | 9 | 대상을 감싸는 고리, 불기둥 |

원본에 있던 `신화스킬` 분류는 없앴습니다. 그 9개는 생김새가 제각각이고 공통점이
보라색 하나뿐이라(원본 게임의 신화 등급 색), 각자 생김새에 맞는 곳으로 넣었습니다.

**단일 이미지 114개** (`single` 카테고리) — Unity 파티클 시스템이 뿌리던 조각들입니다.
글로우, 레이, 마법진, 연기, 눈, 스파클, 사슬, 별. 한 장짜리라 그대로는 안 움직이지만
**크기·회전·투명도를 코드로 바꿔가며 파티클을 직접 만들 때** 재료로 씁니다.

```js
// 단일 이미지로 간단한 파티클 만들기
const t = lib.get('ny_glow_01');
await t.load();
ctx.globalAlpha = 1 - age;                       // 서서히 사라지고
ctx.drawImage(t.image, x - r, y - r, r * 2, r * 2);  // 커지게
```

## 쓰는 법

### 순수 canvas

```html
<script src="./loader.js"></script>
<script>
const lib = await EffectLib.load('./effects.json');
await lib.preload(['mythic_frost_zone', 'explosion']);

const fx = lib.play('mythic_frost_zone', { loop: true });

function frame() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  fx.update().draw(ctx, x, y, { scale: 1.5 });
  requestAnimationFrame(frame);
}
</script>
```

`draw(ctx, x, y)` 의 `x, y` 는 프레임의 **중심**입니다. 유닛 좌표를 그대로 넘기면 됩니다.

한 번만 재생하고 없애려면:

```js
const hit = lib.play('manaball_hit', {
  loop: false,
  onComplete: () => removeFromScene(hit)
});
```

### Phaser 3

```js
function preload() {
  this.lib = await EffectLib.load('./effects.json');
  this.lib.registerPhaser(this, ['mythic_frost_zone', 'explosion']);
}
function create() {
  this.add.sprite(400, 300, 'mythic_frost_zone').play('mythic_frost_zone');
}
```

`registerPhaser` 는 `load.spritesheet` 등록과 `anims.create` 를 같이 처리합니다.
쓸 id 목록을 넘기세요 — 인자를 생략하면 201개를 전부 로드합니다.

### PixiJS

```js
const sprite = lib.toPixi(PIXI, 'mythic_frost_zone');
sprite.position.set(x, y);
sprite.play();
app.stage.addChild(sprite);
```

## 파티클 209개

`singles/` 의 이미지들은 그 자체로는 안 움직이는 **재료**입니다. 원본 Unity 프리팹 안에
그 재료를 어떻게 뿌리는지가 들어 있어서, 그것도 꺼냈습니다.

`particles.json` 에는 이펙트 209개, 이미터 1,574개가 들어 있습니다. 각 이미터마다
어느 텍스처를 쓰는지, 한 번에 몇 개를 뿌리는지, 얼마나 살고 얼마나 빨리 날아가는지,
중력이 얼마인지, 시간에 따라 크기와 색이 어떻게 변하는지 — 전부 작업자가 Unity에
넣은 숫자 그대로입니다.

뷰어에서 스프라이트와 **같은 격자에 섞여** 나오고, `PARTICLE` 배지가 붙습니다.
파티클만 보려면 **파티클** 칩을 누르세요.

원본 프리팹은 344개였는데 209개로 줄였습니다 — 버프 아이콘·메뉴·승리 배너 같은
UI 계열 99개를 빼고, 설계는 같고 색만 다른 36개를 대표 항목으로 접었습니다. 접힌 것은
사라지지 않고 대표 항목의 `variants` 에 각자의 id와 틴트 색으로 남아 있습니다.

```html
<script src="./loader.js"></script>
<script src="./particles.js"></script>
<script>
const lib = await EffectLib.load('./effects.json');
await lib.preload();                       // 텍스처를 먼저 받아두고

const fx = await ParticleFX.load('./particles.json', {
  unitScale: 42,                           // Unity 1유닛 = 몇 px 로 볼지
  resolveTexture: (name) => {
    const id = name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    return lib.has(id) ? lib.get(id).image : null;
  },
});

const burst = fx.spawn('blow_M_fire_magical', { x: 300, y: 400 });

function frame(dt) {
  burst.update(dt / 1000).draw(ctx);       // dt 는 초 단위
  if (!burst.alive()) removeFromScene(burst);
}
</script>
```

`fx.ids()` 로 목록, `fx.textures()` 로 어떤 텍스처가 필요한지 볼 수 있습니다.

**한계 두 가지**

- Unity는 3D로 시뮬레이션하고 이건 2D 재현입니다. 숫자는 원본이지만 결과가 완전히
  같지는 않습니다 — 특히 3D 방출 형태나 메시 파티클은 근사입니다.
- 이미터의 **95%** 가 팩 안의 텍스처로 연결됩니다. 나머지는 UI 이미지(`UI_stage_star_01`,
  `NY_menu_01` 등)를 쓰는 것들이라 일부러 안 넣었습니다. 그 이미터는 조용히 건너뜁니다.

## 배경 처리

전부 투명 배경입니다. 원래 검은 배경 위에 구워져 있던 `lightning_2`, `ring`,
`tyr_bomb` 은 `tools/dekey.py` 로 배경을 알파로 빼냈습니다 (밝기를 알파로 환산 —
발광 이펙트라 정확히 맞아떨어집니다). 그냥 그리면 됩니다.

발광 계열은 가산 합성을 주면 더 살아납니다. 선택 사항입니다.

```js
fx.draw(ctx, x, y, { blend: 'lighter' });                 // canvas
sprite.setBlendMode(Phaser.BlendModes.ADD);               // Phaser
sprite.blendMode = PIXI.BLEND_MODES.ADD;                  // Pixi
```

## 매니페스트 형식

```json
{
  "id": "mythic_frost_zone",
  "category": "mythic",
  "file": "effects/mythic_frost_zone.png",
  "width": 400, "height": 100,
  "frameWidth": 100, "frameHeight": 100,
  "frames": 4, "cols": 4, "rows": 1,
  "fps": 12,
  "source": "06_effect/04_신화스킬/260805_mythic_frost_zone_400x100.png"
}
```

- `cols` / `rows` — 시트 안 프레임 배열. 프레임 `i` 위치는 `(i % cols, floor(i / cols))`.
- `frames` — **실제로 재생할 프레임 수.** `cols × rows` 보다 작을 수 있습니다
  (시트 끝의 빈 칸, 또는 둘째 줄이 색만 다른 변형인 경우). 이 값까지만 재생하세요.
- `fps` — GIF 원본은 실제 프레임 딜레이에서 계산, 그 외는 기본 12.
- `opaque` / `blend` — 위 "알파 없는 이펙트" 참고.
- `source` — 원본 파일 경로. 결과가 이상하면 여기부터 확인.
- `note` — 사람이 확인하고 남긴 메모.

## 어떻게 골라냈나

원본 세 개 zip에서 나온 후보는 692개였고, 그중 201개를 남겼습니다. 걸러낸 것은:

| 분류 | 개수 |
|---|---|
| 단일 이미지 — Unity 파티클 텍스처(NY_glow·NY_ring 등), 아이콘, 무기 파츠, 원화 | 346 |
| 게임 화면 녹화 GIF — UI까지 통째로 찍힘 | 149 |
| `00_reference/` 외부 수집 영상 | 48 |
| UI·무기·배경·펫·보상 카테고리 | 11 |
| 컨택트 시트·목업·`_preview` 중복·`_old` | 25 |
| 화면 녹화·빈 작업본·캐릭터 일러스트·잘못 분할된 아틀라스 (프레임 단위로 확인) | 32 |
| 워터마크 박힌 것(`RTFX generator`), 알파 없는 JPG 중복본 | 2 |

> **저작권 주의** — 걸러낸 `00_reference/` 48개 중에는 `cgjoy.com` 워터마크가 찍힌
> 외부 영상이 있습니다. 자체 제작물이 아니므로 게임에 쓰지 마세요. 이 팩에는 포함돼
> 있지 않습니다.

## 재빌드

원본(`_raw_06/`, `_raw_old/`, `_raw_012/`, `_unpacked/`)이 있을 때만 의미가 있습니다.
`pip install pillow psd-tools` 가 필요합니다.

```bash
python tools/extract_unitypackage.py _raw_012 _unpacked   # unitypackage에서 텍스처 추출
python tools/build.py         # PSD/GIF/PNG → 스프라이트시트 + 매니페스트
python tools/classify.py      # 참고 자료 분리, opaque·oversized 표시
python tools/prune.py         # 이펙트만 남기고 삭제 (--dry-run 으로 먼저 확인)
python tools/regrid.py --apply  # 격자 검증·교정, 끝의 빈 프레임 제거
python tools/categorize.py    # 카테고리 재분류
python tools/dekey.py         # 구워진 배경을 알파로 변환
python tools/extract_unity_assets.py <zip> _unity   # 프리팹·머티리얼
python tools/parse_particles.py _unity .            # particles.json
python tools/dedupe_particles.py                    # 중복·UI 정리
```

각 스크립트가 하는 일:

- **build.py** — `_raw_06` → `_raw_012` → `_unpacked` → `_raw_old` 순으로 우선순위를 두고
  MD5로 중복을 거릅니다. GIF는 프레임을 풀어 시트로 합치고 딜레이에서 fps를 계산하고,
  PSD는 레이어를 프레임으로 봅니다(이 리소스의 제작 규칙). 한글 파일명은 로마자로
  바꿉니다(`romanize.py`).
- **classify.py** — 게임 화면 녹화, 외부 참고 영상, 목업을 `reference/` 로 분리합니다.
- **prune.py** — 이펙트만 남깁니다. 규칙(프레임 2장 이상 + 비이펙트 카테고리 제외)으로
  안 잡히는 것은 `DROP_IDS` 에 사유와 함께 적혀 있습니다.
- **regrid.py** — 알파 여백을 재서 격자가 스프라이트를 자르는지 검사합니다.
  Unity 머티리얼처럼 규칙으로 못 잡는 것은 `GRID_OVERRIDES` / `FRAME_LIMITS` 에
  눈으로 확인한 값이 들어 있습니다.
- **categorize.py** — 카테고리를 실제 모습 기준으로 다시 매깁니다. 목록이
  스크립트 안에 그대로 있으니, 분류를 바꾸려면 거기를 고치고 다시 실행하세요.
- **dekey.py** — 검은 배경 위에 구워진 시트에서 배경을 알파로 빼냅니다.
- **extract_unity_assets.py** — unitypackage에서 프리팹·머티리얼과 GUID 지도를 꺼냅니다.
- **parse_particles.py** — 프리팹 YAML을 읽어 `particles.json` 을 만듭니다.
  머티리얼을 거쳐 텍스처까지 GUID로 연결합니다.
- **dedupe_particles.py** — 같은 설계와 UI 계열을 걸러 파티클 목록을 줄입니다.
- **add_textures.py** — Unity 파티클 텍스처를 `singles/` 로 합칩니다. 버프 아이콘과
  UI 문구(VICTORY, LEVEL UP 등)는 이름 규칙으로 걸러냅니다.
- **build_catalog.py + make_page.py** — `viewer.html` 생성.
  `CATALOG_DIRECT=1` 이면 실제 시트를 읽는 뷰어, `--embed` 면 썸네일 아틀라스를
  파일 안에 넣어 혼자 돌아가는 뷰어를 만듭니다.
