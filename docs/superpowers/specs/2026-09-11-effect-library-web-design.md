# Effect Library 웹 공개 — 설계

날짜: 2026-09-11
상태: 승인됨

## 목표

로컬에서만 쓰던 이펙트 라이브러리(`viewer.html` + PNG 201개 + 파티클 설계 209개)를
공개 URL로 올린다. 보는 사람은 아무것도 내려받거나 clone 하지 않고 브라우저만 열면
검색·미리보기·개별 에셋 사용까지 끝난다.

레퍼런스 UX: https://resource-search.msu.io/search (2단 레이아웃 — 좌측 그리드, 우측 고정 상세)

## 결정 사항

| 항목 | 결정 |
|---|---|
| 접근 범위 | 완전 공개 URL, 인증 없음 |
| 호스팅 | GitHub Pages (`gh` CLI 인증됨 — 계정 Jujeongmin) |
| 저장소 | `effect-library` (public) |
| 배포 URL | `https://jujeongmin.github.io/effect-library/` |
| UI 언어 | 한국어만 |
| 파티클 209개 | 포함 |
| 빌드 도구 | 없음. 바닐라 JS 정적 파일 |

## 데이터

이미 만들어져 있고 이번 작업에서 재생성하지 않는다.

- `effects.json` (82KB) — 스프라이트 201개 매니페스트.
  항목당 `id, category, file, width, height, frameWidth, frameHeight, frames, cols, rows, fps, opaque, source`
- `effects/` 87개 — 애니메이션 스프라이트시트 (8.1MB)
- `singles/` 114개 — 단일 이미지 (1.8MB)
- `particles.json` (909KB) — Unity 프리팹에서 뽑은 파티클 설계 209개
- `particles.js` — 그 설계를 캔버스에서 재생. `ParticleFX.load(url, {resolveTexture})` → `spawn(id, {x,y})` → `update(dt)` / `draw(ctx)`
- `loader.js` — 외부 프로젝트용 스프라이트 로더 (canvas / Phaser 3 / PixiJS)

카테고리 분포: `single` 114, `impact` 18, `lightning` 14, `misc` 12, `projectile` 12,
`explosion` 11, `zone` 11, `aura` 9, 그리고 파티클 209.

## 산출물 구조

저장소 루트가 곧 사이트 루트다. Pages가 `index.html`을 바로 서빙한다.

```
index.html            새 MSU식 2단 뷰어 (이번 작업의 본체)
viewer-classic.html   기존 viewer.html 그대로 이름만 변경. 로컬 더블클릭용 보존
effects/  singles/    PNG 원본. 경로 변경 없음
effects.json  particles.json  particles.js  loader.js
README.md             웹 URL 안내 추가
tools/                재빌드 스크립트 (__pycache__ 는 .gitignore)
docs/superpowers/specs/  이 문서
```

## 레이아웃

MSU 리소스 페이지 구조를 따른다.

**상단 바** — 타이틀, 검색 입력, 결과 수(`410개 중 87개`).

**칩 행** — 전체 / 피격 / 번개 / 폭발 / 투사체 / 장판 / 아우라 / 기타 / 단일 이미지 / 파티클.
한국어 라벨은 기존 뷰어의 `CAT_LABEL` 맵을 그대로 쓴다.

**좌측 그리드** — 카드마다 애니메이션 썸네일(canvas), id, 카테고리 배지.
카드 클릭이 우측 패널을 채운다. 모달 없음.

**우측 고정 상세 패널** — 선택 전에는 안내 문구. 선택 후:

- 큰 미리보기 + 재생/정지 + 배경 전환(어둠 / 체커 / 밝음) + 배율
- 프레임 스트립 (스프라이트만)
- 메타: 프레임 수, 프레임 크기, fps, 시트 크기, 원본 경로
- 복사 버튼: id / 상대 경로 / **절대 직링크 URL** / 코드 스니펫
- PNG 다운로드

**모바일** (<900px) — 상세가 우측 패널 대신 하단 시트로 올라온다.

## 웹 성능

기존 뷰어에 이미 들어 있어 유지하는 것:

- `IntersectionObserver` 로 화면에 들어온 카드만 PNG 요청
- 전역 rAF 루프 하나. 카드별 타이머 없음
- 화면 밖 카드는 `visible` 플래그로 업데이트 건너뜀
- `prefers-reduced-motion` 존중 — 기본 정지

이번에 새로 하는 것:

- 인라인 `<script type="application/json">` 두 덩어리(합 950KB)를 제거하고 `fetch` 로 전환.
  `effects.json` 은 즉시, `particles.json`(909KB)은 목록 끝의 자리표시자가 화면에 들어올 때.
- 파티클 설계는 전용 `IntersectionObserver` 가 지킨다. 파티클 칩을 누르거나
  스프라이트 201개를 끝까지 내려야 받는다.

실측 (1200×1270 뷰포트, 첫 화면):

| | 기존 viewer.html | 새 index.html |
|---|---|---|
| 첫 전송량 | 약 12MB (전부) | 3.0MB |
| PNG 요청 수 | 201개 | 28개 |
| particles.json | 즉시 | 안 받음 |

남은 3.0MB 는 화면에 실제로 보이는 스프라이트시트 28장이다. 원본 시트가 크다
(`poison_9.png` 832KB, `frost_zone.png` 616KB). 이보다 더 줄이려면 128px
썸네일 아틀라스를 따로 구워야 하는데, 이 환경에 이미지 툴(Pillow/sharp)이
없어 이번 범위에서는 뺐다.

## 공유와 직접 사용

**딥링크** — `location.hash` 에 상태를 싣는다.

- `#/aura/fire_aura` — 그 항목이 선택된 채로 열린다
- `#/?q=frost&cat=zone` — 검색어·필터가 적용된 목록

**직링크 복사** — GitHub Pages 가 PNG 를 그대로 서빙하므로 절대 URL 을 준다.

```
https://jujeongmin.github.io/effect-library/effects/fire_aura.png
```

받는 사람은 이 URL 을 코드에 그대로 넣어 쓴다. 파일을 받을 필요가 없다.
코드 스니펫도 이 절대 URL 기준으로 뽑는다.

## 검색

`id` + 한국어 카테고리 라벨 + `source` 원본 경로에 대한 부분 일치. 파티클은 이름 기준.
항목이 410개뿐이라 클라이언트 필터로 충분하다. 검색 라이브러리를 넣지 않는다.

## 검증

- `effects.json` 의 201개 `file` 경로가 전부 실제로 존재하는지 확인
- 배포 후 URL 로 접속해 그리드·검색·칩·상세·딥링크가 동작하는지 확인
- 첫 화면 전송량을 실제 네트워크 기록으로 확인 (목표 300KB 안쪽)
- 모바일 폭(375px)에서 레이아웃 확인

## 범위 밖

- 인증, 업로드, 사용자별 즐겨찾기
- 에셋 재생성 / 재분류 / PNG 재압축
- 영어 UI
