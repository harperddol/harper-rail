# Harper Rail v4 — 시간대 검색 후 예약 희망 열차 선택

실제 코레일 열차 목록 조회 버튼(`/trains`, 읽기 전용)이 추가됐습니다. 출발시간 이후의 실제 조회 결과 중 하나를 선택하면 `train` 필드가 자동 설정됩니다. **실서버에서 로그인/조회 성공은 아직 검증되지 않았습니다.** 기존 Railway 환경변수 및 예약 비활성화 설정을 유지하세요.

# Harper Rail v3 · 1석 출퇴근 감시 베타

기존 GitHub Pages 웹사이트(`index.html`, `style.css`, `app.js`)와 Railway Python 백엔드(`backend.py`)를 함께 포함합니다.

## 기능 상태

- 기존 여정 저장, 코레일 공식 로그인/예매 링크는 유지.
- **개인 Railway 서버 연결**, 대전 ↔ 수서 등의 **정확히 1편의 열차**, 일반실 또는 특실, 성인 **1석만** 감시.
- 좌석 조회 결과가 예약 가능일 때만 실제 예약을 시도. 성공 응답을 받으면 **즉시 감시 중단**. 결제/환불 자동 처리 없음.
- 응답이 불분명한 예약 요청 후 **자동 재시도 금지**. 계정 상태 확인 필요.
- 선택적 텔레그램 메시지 알림. 브라우저 탭을 닫아도 *Railway 서버가 계속 실행되는 한* 감시 시도.

## 실제 연동에 관한 중요한 제한

**실시간 코레일 서버와의 로그인·좌석 조회·예약 성공은 검증되지 않았습니다.** 비공식 `korail-mobile-api` 라이브러리를 사용하므로 코레일의 접근 제한, DynaPath, 속도제한 또는 API 변경으로 거부될 수 있습니다. 이를 우회하지 않습니다. 실제 예약 활성화 전 확인 필요. 10초 설정은 과도한 요청을 유발할 수 있어 기본 조회 간격은 **60초**이고, 최소 **10초**는 환경변수로 설정 가능하나 접속 제한의 위험이 높습니다.

시작 시 서버는 `ENABLE_LIVE_RESERVATION=false` 상태로 실행합니다. 예약을 실제 실행하려면 사전 검증한 뒤 `true`로 변경해야 합니다. **예약 실패가 감지되더라도 서버가 요청을 받았을 수 있어 반드시 코레일 공식 앱에서 확인하세요.**

## GitHub에 업로드

1. 기존 저장소 `https://github.com/harperddol/harper-rail`에서 `Add file → Upload files`.
2. 이 ZIP을 **압축해제하고 나온 파일들**을 루트에 업로드(동일명 교체). `.env`, 계정 비밀번호, 대시보드 토큰은 **절대 GitHub에 저장하지 마세요**.
3. `Commit changes` 후 GitHub Pages는 자동 갱신됩니다.

## Railway 서버 배포 (별도 단계)

1. Railway에서 **New Project → Deploy from GitHub repo** 선택, `harperddol/harper-rail` 저장소 연결. Railway가 GitHub 권한 승인 요청을 표시하면 본인이 직접 로그인 및 승인.
2. Python 3.11+ 환경으로 배포. `requirements.txt` 설치, `railway.json`의 시작 명령 `python backend.py` 사용. 필요시 Railway UI에서 Start Command 지정.
3. **Variables** 에 다음 설정(절대 GitHub 공개 저장소에 입력하지 말 것):
   - `DASHBOARD_TOKEN`: 직접 만든 길고 예측 불가능한 개인 토큰 (32자 이상 권장)
   - `KORAIL_ID`: 코레일 로그인 ID
   - `KORAIL_PASSWORD`: 코레일 로그인 비밀번호
   - `FRONTEND_ORIGIN`: `https://harperddol.github.io` (기본값)
   - `POLL_SECONDS`: `60` (빠른 조회는 접속 제한 위험)
   - `ENABLE_LIVE_RESERVATION`: 처음엔 `false`로 유지. **본인 책임 하의 실예약 작동 확인 후** `true`로 변경.
   - 선택: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (보안상 반드시 Railway Variables에만 기록)
4. 서비스에 Railway **Public Networking domain** 생성 (예: `https://xxxx.up.railway.app`). `/health` 접속 시 `ok: true` 응답을 확인.
5. GitHub Pages 사이트 아래 **개인 서버 주소**에 Railway HTTPS URL을 입력하고 `DASHBOARD_TOKEN` 값을 입력. 브라우저는 토큰을 저장하지 않음.
6. 일반실+특실 포함 가능한 한 열차번호를 입력하고 **성인 1명, 실제 예약 동의** 체크 후 감시 시작. 감시상태는 서버 조회로 확인.
7. 좌석 확보시 텔레그램 메시지가 오거나 웹에서 상태가 `reserved`면 **코레일+ 앱에서 결제 기한을 확인하고 직접 결제**.

## 보안 및 운영

- 공개 GitHub Pages에 회원 ID/비밀번호를 입력하지 않음. 코레일 자격정보는 Railway 서버 환경변수에 보관.
- 백엔드 관리 API는 `DASHBOARD_TOKEN`이 있어야 시작·중지·조회 가능. 토큰을 타인과 공유하지 말 것.
- 코드와 Railway 환경변수가 유출되면 즉시 코레일 비밀번호, API 토큰을 변경.
- 서버 재시작/배포 시 감시 설정은 메모리에서 사라짐. *지속적인 재시작 복구/예약 결과 검증/감시 연속성*은 추가 개발 필요.
- 예약 내역이 이미 존재하는지를 더 정밀하게 검증하기 전에는 **중복 예약 방지를 완전하게 보장하지 못함**. 기존 예약 내역 조회 API를 호출하지만 결과 내용을 목표 열차와 비교하는 기능은 미완료.
- 안전장치상 감시는 1개만 실행. 판매, 대량 예매, 계정 공유, 우회 기능을 구현하지 않음.
- 개인용 비공식 예제이며 코레일/SR 및 KayRail과 무관합니다.

## 내부 파일

- `index.html`, `style.css`, `app.js`: 기존 화면 및 저장 기능
- `backend-ui.js`: Railway 백엔드 연결 화면
- `backend.py`: HTTP API, 단일 감시 스레드, 비공식 코레일 클라이언트
- `requirements.txt`, `railway.json`, `Procfile`: 서버 배포 설정
