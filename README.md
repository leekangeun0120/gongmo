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

## 자동으로 되는 것 / 사람이 채우는 것

| 자동 (하루 3번) | Claude가 주 1회 |
|---|---|
| 새 공모주 증권신고서 등장 → 종목 추가 | 쉬운 기업 설명 |
| 정정신고서 → '일정 다시 확인' 표시 | 기관 수요예측 경쟁률·확약 |
| 청약일·주관사 (DART에 있으면) | 확정 공모가, 상장일 |
| 끝난 지 40일 지난 종목 정리 | |
