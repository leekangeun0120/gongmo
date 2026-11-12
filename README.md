# 강은의 공모주 달력

공모주 청약·상장 일정, 기업 설명, 주관 증권사, 주린이 체크리스트를 모은 페이지예요.

- `index.html` : 화면
- `data.json` : 종목 정보 (이 파일만 바뀌면 화면이 바뀌어요)
- `scripts/update.py` : DART 공시를 확인해서 `data.json`을 고치는 코드
- `.github/workflows/update.yml` : 평일 하루 세 번(08:00, 12:30, 18:00) 자동 실행

## 처음 한 번만 하는 설정

1. **DART API 키 발급** (무료)
   opendart.fss.or.kr → 인증키 신청/관리 → 인증키 신청. 메일로 40자리 키가 와요.
2. **GitHub에 저장소 만들기**
   github.com → New repository → 이름 `gongmo` → Public → Create.
   "uploading an existing file"을 눌러 이 폴더 안의 파일을 전부 끌어다 놓고 Commit.
   (`.github` 폴더는 숨김 폴더라 안 보일 수 있어요. 안 되면 아래 '워크플로 직접 만들기'를 보세요.)
3. **키 넣기**
   저장소 Settings → Secrets and variables → Actions → New repository secret
   이름 `DART_API_KEY`, 값에 발급받은 키 → Add secret.
4. **페이지 켜기**
   Settings → Pages → Branch `main` / `(root)` → Save.
   1~2분 뒤 `https://leekangeun0120.github.io/gongmo/` 에서 열려요.
5. **첫 실행 확인**
   Actions 탭 → "공모주 일정 자동 갱신" → Run workflow. 초록 체크가 뜨면 성공.

## 워크플로 직접 만들기

`.github` 폴더가 업로드되지 않았다면: 저장소에서 Add file → Create new file →
파일 이름에 `.github/workflows/update.yml` 입력 → `update.yml` 내용을 붙여넣고 Commit.

## 누가 무엇을 채우나 (2026-11-13 기준)

파일 하나를 한 담당이 맡아요. 두 담당이 같은 칸을 고치면 서로 덮어쓰기 때문이에요.

| 담당 | 언제 | 파일 | 하는 일 |
|---|---|---|---|
| gongmo-bot (GitHub Actions, `scripts/update.py`) | 평일 08:00·12:30·18:00 | `data.json` | DART 새 증권신고서 → 종목 추가, 정정신고서 → `alert`, **철회신고서 → `cancel`** |
| Claude 예약 작업 "공모주 달력 수요예측 업데이트" | 평일 19:17 | `data.json` | `fix`·`inst`·`lock`·`float`·`retail`·`l`·`minq`·`fc`·`d`·`memo` 채우기, 철회 기사 확인, 카톡 알림 |
| Claude 예약 작업 "공모주 청약일 경쟁률" | 평일 11:23·15:23 | `live.json` | 청약 중인 종목의 증권사별 경쟁률·청약 건수·균등 예상 (뉴스·공시 기준), 15:23엔 마감 전 카톡 |
| 다른 도우미(피클 등) | — | 읽기만 | 청약일 아침 알림처럼 **읽어서 알려 주는 일**만. `data.json`·`live.json`에 쓰지 않기 |
| 클로드코드 (PC) | 필요할 때 | `index.html` | 화면 디자인·기능 |

## data.json 종목 필드

| 필드 | 뜻 | 예 |
|---|---|---|
| `n` | 종목명 | 동원파츠 |
| `mk` | 시장 | 코스닥 / 코스피 |
| `d` | 쉬운 회사 설명 1~2문장 | |
| `s`, `e` | 청약 시작·마감일 | 2026-11-12 |
| `l` | 상장일 | 2026-11-24 |
| `b` | 주관 증권사 목록 | ["하나증권"] |
| `band` | 희망 공모가 [하단, 상단] | [9600, 11700] |
| `fix` | 확정 공모가 | 7000 |
| `inst` | 기관 수요예측 경쟁률 | 187.1 |
| `lock` | 의무보유확약 % | 16.61 |
| `float` | 상장 직후 유통가능 물량 % | 29.47 |
| `retail` | 일반 청약 최종 경쟁률 | 1219.37 |
| `minq` | 균등배정 최소 청약 주수 | 10 / 20 |
| `fc` | 수요예측 결과 발표 예정일 | 2026-11-11 |
| `cancel` | 상장 철회일 (있으면 달력에서 빠지고 "상장 철회") | 2026-11-11 |
| `spac` | 스팩이면 true | |
| `memo`, `alert` | 메모 / 정정 알림 | |
| `dart`, `dart_seen`, `dart_name`, `new` | 봇이 쓰는 칸 (건드리지 않기) | |

## live.json (청약 당일 경쟁률)

```json
{"updated":"2026-11-13T11:23+09:00","by":"Claude 예약 작업",
 "items":{"종목명":{"증권사":{"rate":0.78,"count":12345,"alloc":250000,"est":44.12,
   "at":"2026-11-13T11:00+09:00","src":"출처 URL"}}}}
```
- `rate` 경쟁률, `count` 청약 건수, `alloc` 그 증권사 일반청약 배정 주식수(증권신고서)
- `est`(균등 예상 주수)가 없으면 화면이 `alloc × 0.5 ÷ count`로 계산해요.
- `alloc`이 있으면 카드에 "앱에서 본 청약 건수" 칸이 생겨서, 증권사 앱 숫자를 넣으면 바로 균등 예상이 나와요.
- 증권사 경쟁률 페이지는 자동 수집을 막아 두어서 긁어 오지 않아요. 기사·공시에 나온 숫자만 넣어요.
