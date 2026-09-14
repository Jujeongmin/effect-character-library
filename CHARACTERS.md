# Character Library — 스키마

`characters.json` / `character-loader.js` / `characters/index.html` 는
[effects.json 팩](README.md)과 같은 저장소에 있지만 **완전히 별도의 라이브러리**다.
서로의 id 공간을 공유하지 않고, 뷰어 링크도 따로다 (`characters/index.html`).

## 폴더

```
characters.json          매니페스트
character-loader.js      로더 (CharacterLib — loader.js 의 캐릭터 버전)
characters/
  index.html              뷰어 (effects 뷰어와 같은 디자인 시스템, 별도 링크)
  humanoid/               인간형 — 사람 체형 (동물 귀·꼬리가 있어도 얼굴·몸은 사람)
  beast/                  야수형 — 짐승 몸(네발 또는 짐승 머리)의 판타지 생물
  animal/                 동물형 — 평범한 실사풍 동물(고양이, 새 등)
  monster/                몬스터형 — 위 셋에 안 들어가는 나머지(슬라임, 유령, 오우거, 식물 골렘 등)
```

분류는 **원본이 어느 폴더(캐릭터/몬스터/NPC/펫)에서 왔는지가 아니라 실제로
어떻게 생겼는지** 기준이다 — `effects.json` 이 카테고리를 "원본 폴더 이름이
아니라 실제로 어떻게 보이는지" 기준으로 잡은 것과 같은 원칙. NPC 폴더에서
왔어도 사람처럼 생겼으면 `humanoid`, 고양이처럼 생겼으면 `animal`.

카테고리를 늘리려면 `characters.json` 의 `categories` 맵에 키를 추가하고
`characters/<새 카테고리>/` 폴더를 만들면 된다. 뷰어의 칩은 그 맵에서 자동으로 뽑힌다.

## 지금 들어있는 데이터

260개 (인간형 137 · 야수형 56 · 동물형 23 · 몬스터형 44). 전부 정지 이미지 한 장
(A 형식, `frames: 1`) — 원본이 애니메이션 스프라이트가 아니라 일러스트 한 장짜리
원화이기 때문이다.

처음엔 "같은 포즈·같은 무기에 색만 다른 스킨"을 재탕으로 보고 한 장만 남기고
뺐었는데(`effects` 팩이 파티클 344개를 209개로 접었을 때 방식), **색만 달라도
다른 프로젝트에선 각자 다른 이름 붙여서 쓸 수 있다**는 이유로 전부 되살렸다 —
지금은 아무것도 안 뺀다. 색상/의상 스킨은 `<베이스id>_<스킨명>` 식으로,
`102xxxxx` 장비단계 라인의 속성태그 변형은 `<베이스id>_tagN` / `_alt` 식으로
접두어를 맞춰서 어느 캐릭터의 스킨인지 id만 보고 알 수 있게 해뒀다.
(`note` 필드에도 "OO 재탕 — 색/속성태그만 다름" 이라고 표시)

**몬스터(002_monster)** 는 겉보기엔 비슷한 패턴(한 몬스터당 파일이 5~9장)이지만
열어서 비교해보니 색만 다른 게 아니라 **장비 단계마다 그림 자체가 다르거나
(무기·방어구가 바뀜), 속성별로 아예 다르게 그린 것**이었다 — 그래서 몬스터는
하나도 안 뺐다. 한 몬스터 "계열"의 여러 단계가 전부 각자 캐릭터 항목으로
들어있다 (예: `fox_warrior_daggers` ~ `fox_warrior_chief` 8개는 전부 여우
전사 한 계열의 장비 단계). id에서 계열을 알아볼 수 있게 접두어를 맞췄다.

웹에서 원본 해상도(최대 4500px)로 쓸 이유가 없어서 긴 변 900px로 줄여서
넣었다(원본은 훨씬 큼).

이름이 원본에 없는 항목(주로 몬스터, 일부 캐릭터)은 생김새 보고 대충 지었다 —
`note` 필드에 `"이름 미상 — 대충 지은 이름"` 이라고 표시해 뒀다. 다른 프로젝트에서
가져다 쓸 때 원하는 이름으로 다시 붙이면 된다는 전제로 정확도보다 속도를 택함.

### 표정 시트 — 몸은 안 움직여도 얼굴은 바뀐다

여러 캐릭터 폴더에 `_F_표정.png` 라는, 이미 완성된 **8~9종 표정 세트**가
따로 있었다 (idle/attack/turnover/win/casting/die/hit/run, 캐릭터에 따라
touch 하나 더). 리깅 없이 상태별로 초상화만 바꿔치기하는 용도로 바로 쓸 수
있다. `mage_expr_idle` ~ `mage_expr_run` 8개는 시트에서 낱장으로 잘라
넣었고, 나머지 13명(`rui_expressions`, `verdandi_expressions` 등)은 시트
통째로 한 장씩 들어있다 — 필요하면 마법사처럼 나중에 낱장으로 잘라도 된다.
발키리처럼 PSD 안에 `표정관련레이어` 그룹만 있고 PNG로 안 뽑힌 캐릭터도
더 있을 수 있다(전수조사 안 함).

### 시도했다가 접은 것 — 컷아웃 리깅

원본 PSD 일부(특히 `102xxxxx` 라인)는 팔·다리·머리카락·표정이 레이어로 다
쪼개져 있어서, 새로 안 그리고도 관절 회전만으로 캐릭터를 "움직이게" 만들 수
있을지 시범 삼아 캐릭터 하나로 만들어봤다(부위 24개 추출 → 회전축 잡고 CSS로
흔들기). 결과물은 실제로 움직였지만 — **이 방향은 채택 안 함**. 이유를 남겨서
나중에 똑같은 시도 반복하지 않게: 관절 위치를 캐릭터마다 눈대중으로 손수 잡아야
해서 스케일이 안 나옴. 재추진하려면 Spine 같은 전문 툴로(사람이 직접) 하는 걸
권장 — PSD 쪽에 idle/attack/hit/die 같은 상태별 파츠까지 있어서 재료는 충분함.

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

## 리소스가 더 들어오면 할 일

1. PNG를 `characters/<카테고리>/` 에 넣는다 (필요하면 웹용으로 리사이즈 —
   원본이 리소스 폴더에 그대로 있으니 손실은 없다).
2. `characters.json` 의 `assets` 배열에 위 A/B 형식 중 맞는 쪽으로 항목을 추가한다.
3. `characters/index.html` 을 열어 그리드·상세·애니메이션 탭이 뜨는지 확인한다.
   코드를 고칠 필요는 없다 — 데이터만 채우면 된다.

실제 애니메이션 스프라이트(`idle`/`walk`/`attack`/`hit`/`death` 여러 장)가 들어오면
B 형식으로 바꿔서 등록하면 된다 — 지금 A 형식으로 들어있는 항목도 나중에 그렇게
업그레이드할 수 있다, id는 그대로 두고 `animations` 맵만 채우면 된다.
