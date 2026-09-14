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

299장의 그림이 **172개 캐릭터 항목**으로 들어있다 (인간형 69 · 야수형 54 ·
동물형 7 · 몬스터형 42). 148개는 그림 한 장짜리, 24개는 여러 장 중 골라보는
B 형식(`animations`) — 뷰어에서 카드를 클릭하면 자동으로 탭이 뜨고, 그리드
카드에도 미리 "N개" 표시가 붙어서 클릭 전에 여러 모습이 있는지 알 수 있다.

**주의: `animations` 는 스키마 이름일 뿐, 지금 들어있는 건 전부 정지 그림이다.**
탭 여러 개는 "이 캐릭터가 걷고 공격하는 애니메이션"이 아니라 "이 캐릭터의
여러 모습(색상 스킨·표정·성장단계) 중 고르는 것"이다. 뷰어 상세 패널에도
"애니메이션"이 아니라 "모습"이라고 표시해 뒀다 — 오해 소지 있어서 고쳤다.

### 언제 한 캐릭터로 묶고, 언제 따로 두나

기준은 하나 — **색상만 다른가, 콘셉이 다른가.**

- **색상/톤만 다르면 → 한 캐릭터, 탭으로 묶는다.** `valkyrie` 의 검은색·갈색·
  흰금 스킨처럼 포즈·무기·이름에 콘셉 단어가 없고 팔레트만 바뀐 경우.
  표정 세트(idle/attack/win/die/...)도 여기 해당 — "같은 사람이 다른 표정을
  짓는 것"이지 다른 사람이 아니다. 펫의 성장 단계(1/2/3)도 마찬가지.
- **콘셉·테마·이름이 다르면 → 따로따로 항목.** `mage`(기본)와
  `mage_angel`/`mage_demon`/`mage_yellowhair` 는 포즈만 같을 뿐 "천사"·
  "악마" 라는 서로 다른 콘셉이라 4개 캐릭터로 분리돼 있다. 같은 이유로
  `white_lion_knight`/`_fire`(불의 화신)/`_blackghost`, `archer`/`_goblin`/
  `_cherryblossom`/`_summerbeach` 등도 전부 별도 항목.
- **몬스터 장비단계·속성폼도 콘셉이 다른 것으로 본다.** `fox_warrior_daggers`
  ~ `_chief` 8개, `shell_leaf`/`_crab`/`_flame`/`_wind`/`_water` 5개 —
  전부 무기·방어구·모양 자체가 달라서(단순 재도색이 아님) 각자 캐릭터다.
  다만 `102xxxxx` 고양이수인 소년의 **장비 단계**(`neko_boy_casual` ~
  `neko_boy_gold_knight`, 7개)도 이 기준으로 각자 캐릭터로 분리했고, 그
  안에서 순수 속성태그 재도색(`_tag1~4`)과 코스튬B(`_alt`)만 탭으로 묶었다
  (예: `neko_boy_dark_armor` 카드 안에 태그 10개 탭).

id 접두어로 계열을 알아볼 수 있게 맞췄다 (`fox_warrior_*`, `neko_boy_dark_armor_*`
등). 웹에서 원본 해상도(최대 4500px)로 쓸 이유가 없어서 긴 변 900px로 줄여서
넣었다(원본은 훨씬 큼). 이름이 원본에 없는 항목(주로 몬스터, 일부 캐릭터)은
생김새 보고 대충 지었다 — `note` 필드에 `"이름 미상 — 대충 지은 이름"` 이라고
표시해 뒀다. 다른 프로젝트에서 가져다 쓸 때 원하는 이름으로 다시 붙이면 된다는
전제로 정확도보다 속도를 택함.

### 표정 시트 — 몸은 안 움직여도 얼굴은 바뀐다

여러 캐릭터 폴더에 `_F_표정.png` 라는, 이미 완성된 **6~9종 표정 세트**가
따로 있었다 (idle/attack/turnover/win/casting/die/hit/run, 캐릭터에 따라
touch 하나 더). 리깅 없이 상태별로 초상화만 바꿔치기하는 용도로 바로 쓸 수
있다.

- **마법사·마도사·나드·마녀·크리스마스·궁수·다그·갈색피부의 여전사 (8명)**
  — 표정마다 배경·라벨 글자 없이 낱장으로 깨끗하게 잘라서 `<베이스id>_expr_*`
  탭으로 넣었다. 마법사는 PSD 레이어에서 직접 뽑아서 `idle`/`attack`/... 실제
  상태 이름이 붙어있고, 나머지 7명은 PNG만 있어서(레이어 접근 불가) 자동
  슬라이서로 배경 제거는 했지만 어느 게 idle/attack인지는 몰라 `expr_00`,
  `expr_01`... 번호로만 구분된다.
- **베르단디·스쿨드·울드·고양이수인·페어리·루이·루시 (7명)** — 세로로 긴
  2단 레이아웃이라 자동 슬라이서가 열을 못 나눴다. 시트 통째로 한 장이라
  캐릭터 탭으로도, 별도 항목으로도 실제로 못 쓴다(누가 봐도 캐릭터 그림이
  아니라 얼굴 8개 뭉친 참고용 시트) — **아예 뺐다.** 본체(`lucy` 등)는
  기본 정지 그림 하나만 남는다. 원본은 여전히 로컬 소스 폴더에 있다.
- 발키리처럼 PSD 안에 `표정용오브제` 같은 작은 표정 소품 레이어만 있고
  독립된 표정 세트는 없는 경우도 있다 (247개 PSD 레이어명 전수조사로 확인,
  아래 참고).

### PSD 247개 전수조사 결과

레이어 이름에 "표정"이 들어가는 PSD를 전부 찾아봤다:

- **몬스터 201 계열**(둥근 열매정령), **발키리** — 작은 눈/입/땀방울 소품
  레이어만 있음, 독립된 표정 그림이 아니라 캐릭터 목록에는 안 넣었다
- **209004(scarecrow_ice_swordsman)** — 진짜 5칸 표정 시트가 있었지만
  라벨이 텍스트 레이어가 아니라 손그림에 잉크로 직접 그려져 있어서
  깨끗하게 뺄 수 없다 — 카탈로그에는 안 넣음
- **그 외 200여 개** — 매칭된 건 전부 캐릭터 얼굴 리그의 정상적인
  `eye_01~04`/`mouth_01~05` 부위 이름(표정 스왑용 파츠, 특정 캐릭터만의
  보너스 세트가 아니라 리그 자체의 일부)이었다

또한 `_애니메이션시트.png`/`_animation.png`/`_sheet.png` 이름이 붙은 파일이
나드·마녀·크리스마스·궁수·페어리·다그·고양이수인 등 여러 캐릭터 폴더에
있었는데, **전부 예외 없이 손그림 스토리보드**였다(색칠 안 된 스케치 +
"열이 받은 듯 씩씩거리며 달려온다" 같은 동작 지시문). 실제 게임용 프레임은
어디에도 없었다 — 앞서 확인한 울드 사례와 정확히 같은 패턴.

### 시도했다가 접은 것 — 컷아웃 리깅

원본 PSD 일부(특히 `102xxxxx` 라인)는 팔·다리·머리카락·표정이 레이어로 다
쪼개져 있어서, 새로 안 그리고도 관절 회전만으로 캐릭터를 "움직이게" 만들 수
있을지 시범 삼아 캐릭터 하나로 만들어봤다(부위 24개 추출 → 회전축 잡고 CSS로
흔들기). 결과물은 실제로 움직였지만 — **이 방향은 채택 안 함**. 이유를 남겨서
나중에 똑같은 시도 반복하지 않게: 관절 위치를 캐릭터마다 눈대중으로 손수 잡아야
해서 스케일이 안 나옴. 재추진하려면 Spine 같은 전문 툴로(사람이 직접) 하는 걸
권장 — PSD 쪽에 idle/attack/hit/die 같은 상태별 파츠까지 있어서 재료는 충분함.

### 다시 시도함 — 자동 리깅 4종 (실험적, `characters/rigs/`)

위 항목을 손으로 반복 잡던 것에서, PSD 파츠 위치를 코드로 읽어 뼈대를 직접
계산하는 쪽으로 바꿔서 4개(`neko_boy_traveler`, `archer`, `valkyrie`, `mage`)
만들어봤다. `characters.json`의 해당 항목에 `spineRig` 필드로 연결돼 있다.

```json
"spineRig": {
  "file": "characters/rigs/archer/archer.json",
  "images": "characters/rigs/archer/images/",
  "animations": ["idle", "attack", "hit", "die"],
  "note": "..."
}
```

`file`은 Spine 4.3 스켈레톤 JSON(런타임 익스포트 포맷과 동일 — Spine에서
File → New로 빈 프로젝트를 연 다음 File → Import Data로 불러오면 됨. 더블
클릭이나 File → Open으로 열면 "프로젝트 파일 아님" 에러남). 뼈대·슬롯·스킨은
PSD 레이어 위치에서 그대로 계산해서 바인드 포즈는 원본 그림과 픽셀 단위로
똑같다 — 팔다리를 이어붙이는 부모-자식 관계, 관절(어깨/팔꿈치/무릎 등) 위치는
인접 파츠의 바운딩박스가 겹치는 자리를 추정한 것.

**한계 (사람이 다듬어야 하는 부분):**
- 관절 위치는 추정치. 특히 이름이 없는 레이어("Layer 12" 류)나 파츠 이름이
  일관되지 않은 캐릭터(`mage`, `valkyrie`)는 일부 장식 파츠가 몸통에 그냥
  고정 부착됨 — 따로 흔들리지 않음.
- `idle`/`attack`/`hit`/`die` 네 애니메이션 다 절차적으로 자동 생성한
  것(회전각을 손으로 안 맞춤) — 무기 종류 상관없이 팔을 앞으로 크게 휘두르는
  동작 하나로 통일. 궁수의 활시위 당기기처럼 무기별 전용 동작은 없음.
- 어느 손에 무기를 쥐는지도 임의로 가정(오른손 우선). 틀렸으면 Spine에서
  `weapon` 뼈의 부모만 바꿔주면 됨.

즉 "PSD import + 뼈 배치" 두 단계를 자동화한 것이고, 관절 미세조정과 실제
손맛 나는 애니메이션은 여전히 Spine에서 사람이 해야 한다.

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
