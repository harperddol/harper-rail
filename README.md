# Harper Rail · 출퇴근용 웹사이트

대전 ↔ 수서 등 기차 여정 입력과 브라우저 저장, 코레일 공식 예매 사이트 바로가기를 지원하는 **정적 웹사이트**입니다.

## 현재 구현된 기능
- 출발역 / 도착역 교체, 날짜, 시간, 열차번호, 일반실/특실, 인원 설정
- 브라우저 내 여정 저장 및 불러오기·삭제
- 코레일 공식 로그인 및 예매 페이지 링크
- 코레일 공식 예약대기 제도 안내

## 구현되지 않은 기능
- 코레일 자동 로그인 또는 로그인 상태 공유
- 코레일 실시간 좌석 조회, 10초 간격 폴링
- 취소표 자동예약, 좌석 보류, 결제 URL 발급

> **주의:** 열차 잔여석을 조회하는 기능이 없으므로 이 사이트가 자동예약을 실행하거나 알림을 보낸다고 가정하면 안 됩니다. 코레일 비밀번호는 입력하지 마세요.

## GitHub에 업로드
1. GitHub의 `harperddol/harper-rail` 저장소에 로그인합니다.
2. **Add file → Upload files** 클릭합니다. 저장소가 비어 있으면 중앙의 **uploading an existing file** 링크를 사용해도 됩니다.
3. 이 폴더의 `index.html`, `style.css`, `app.js`, `README.md` 네 파일을 **루트(최상위 폴더)에** 업로드합니다. ZIP 파일 그대로 업로드하면 실행되지 않습니다.
4. **Commit changes**를 누릅니다.
5. **Settings → Pages → Build and deployment → Deploy from a branch → main / (root) → Save**를 선택합니다.
6. 배포가 끝나면 `https://harperddol.github.io/harper-rail/` 주소에서 접속할 수 있습니다. Pages 활성화 및 배포는 GitHub 쪽에서 완료되어야 합니다.

### GitHub 저장소 비공개(Private) 주의
GitHub Pages를 이용하려면 계정 플랜과 저장소 공개/비공개 조건을 확인해야 합니다. 무료 개인 계정에서 Pages를 쓰려면 저장소를 **Public**으로 바꾸는 것이 일반적입니다. 소스 코드에는 인증 비밀정보를 넣지 않았지만 Public 전환 시 전체 코드가 공개됩니다.

## 로컬 실행
`index.html`을 더블클릭하면 주요 기능을 사용할 수 있습니다. 프라이빗 브라우징이나 파일 URL 브라우저 정책에 따라 localStorage가 제한될 수 있습니다. GitHub Pages에 올려 사용하는 방법을 권장합니다.

## 공식 참조
- https://www.korail.com/ticket/login
- https://www.korail.com/ticket/main
- https://www.korail.go.kr/ticket/reserve/guide/faq

사이트는 한국철도공사 또는 SR과 제휴·공식 연동된 서비스가 아닙니다.
