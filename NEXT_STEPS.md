# 📝 다음 단계 가이드

> Phase 0 완료! 이제 실제로 키움 API를 연결하고 테스트해봅시다.

## ✅ 완료된 작업

- [x] 프로젝트 디렉토리 구조 생성
- [x] Git 저장소 초기화
- [x] 키움 REST API 클라이언트 구현
- [x] WebSocket 클라이언트 구현 (재연결 로직 포함)
- [x] 데이터베이스 스키마 설계
- [x] 환경변수 템플릿 작성
- [x] API 연결 테스트 스크립트 작성
- [x] 프로젝트 문서화

## 🎯 즉시 할 일 (오늘, 30분)

### 1️⃣ 키움증권 REST API 신청

**순서**:
1. 키움증권 홈페이지 로그인
   - URL: https://www.kiwoom.com

2. REST API 신청 페이지 이동
   ```
   경로 1: 트레이딩 채널 → 키움 REST API
   경로 2: 고객서비스 → 다운로드 → Open API → 키움 REST API
   ```

3. **모의투자 App Key 발급**
   - 메뉴: `모의투자 App Key 관리`
   - App Key 발급 클릭
   - Secret Key 발급 클릭
   - **즉시 복사해서 안전한 곳에 저장!** (한 번만 보임)

4. **IP 주소 등록**
   ```bash
   # 현재 IP 확인
   curl ifconfig.me
   ```
   - 출력된 IP 주소를 키움 사이트에 등록

### 2️⃣ 환경변수 설정

```bash
# .env 파일 열기
nano .env

# 아래 값 수정
KIWOOM_APP_KEY=발급받은_실제_APP_KEY
KIWOOM_SECRET_KEY=발급받은_실제_SECRET_KEY
KIWOOM_IS_MOCK=true  # 모의투자는 true

# 저장: Ctrl+O, 엔터, Ctrl+X
```

### 3️⃣ Python 패키지 설치

```bash
# 가상환경 활성화 (아직 안했다면)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 4️⃣ API 연결 테스트

```bash
# 테스트 실행
python tests/test_kiwoom_api.py
```

**성공 시 출력**:
```
✅ 토큰 발급 성공!
✅ 삼성전자 현재가 조회 성공!
   종목명: 삼성전자
   현재가: 75000원
   전일대비: +1000원 (+1.35%)

🎉 다음 단계: Sub Server 개발
```

## 🚨 문제 해결

### ❌ "등록되지 않은 IP입니다"
**해결**:
1. 현재 IP 확인: `curl ifconfig.me`
2. 키움 사이트에서 IP 등록 (최대 10개)
3. 10분 후 재시도

### ❌ "App Key가 유효하지 않습니다"
**해결**:
1. `.env` 파일에서 App Key/Secret Key 다시 확인
2. 공백이나 따옴표 없이 입력했는지 확인
3. 키움 사이트에서 키 재발급

### ❌ "ModuleNotFoundError"
**해결**:
```bash
# 가상환경 확인
which python  # venv/bin/python 이어야 함

# 패키지 재설치
pip install --upgrade -r requirements.txt
```

## 📅 이번 주 계획 (Phase 1 시작)

### DAY 1-2: 틱데이터 수집 엔진 (완료 예정: 16h)

**파일**: `sub_server/collectors/tick_collector.py`

**목표**:
- WebSocket으로 실시간 틱 수신
- 10,000건 버퍼링
- DB 일괄 저장

**실행**:
```bash
# 다음에 구현할 코드
python sub_server/main.py
```

### DAY 3-4: 데이터베이스 연동 (완료 예정: 12h)

**파일**: `sub_server/services/storage_service.py`

**목표**:
- MariaDB 연결
- 틱데이터 bulk insert
- 파티셔닝 설정

### DAY 5: 통합 테스트 (완료 예정: 8h)

**목표**:
- 50개 종목 동시 수집
- 분당 5,000~10,000건 저장
- 메모리 사용량 < 500MB

## 🎓 학습 자료

### 키움 API 문서
- `키움증권_REST_API_완전가이드.md` - 완전한 API 레퍼런스
- `PRD.md` - 프로젝트 요구사항 명세
- `EXECUTION_PLAN_REST_API (1).md` - 실행 계획서

### 코드 구조
- `sub_server/api/kiwoom_client.py` - REST API 클라이언트
- `sub_server/api/websocket_client.py` - WebSocket 클라이언트
- `database/schema.sql` - DB 스키마

## 💡 팁

### 개발 환경 설정
```bash
# 코드 자동 포맷팅
black sub_server/

# 타입 체크
mypy sub_server/

# 테스트 실행
pytest tests/
```

### Git 워크플로우
```bash
# 작업 전 항상 커밋 확인
git status

# 변경사항 커밋
git add .
git commit -m "작업 내용"

# 브랜치 생성 (새 기능 개발 시)
git checkout -b feature/tick-collector
```

## 🚀 다음 커밋 목표

**제목**: "Phase 1: Tick data collector implementation"

**포함 내용**:
- [ ] `sub_server/collectors/tick_collector.py` 구현
- [ ] `sub_server/services/storage_service.py` 구현
- [ ] `sub_server/main.py` 메인 엔트리포인트
- [ ] 통합 테스트 추가

## 📞 도움이 필요하면

1. **키움 API 문의**: https://openapi.kiwoom.com
2. **GitHub Issues**: 프로젝트 이슈 페이지
3. **가이드 문서**: `README.md`, `키움증권_REST_API_완전가이드.md`

---

**현재 버전**: 0.1.0 (Phase 0 완료)
**다음 마일스톤**: Phase 1 - Sub Server 기본 구축
**예상 소요 시간**: 2주 (60시간)

🎉 **수고하셨습니다! API 신청 후 테스트 성공하면 다음 단계로 넘어갑시다!**
