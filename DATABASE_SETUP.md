# 데이터베이스 설정 가이드

MariaDB root 비밀번호가 이미 설정되어 있어, 직접 설정이 필요합니다.

## 방법 1: 비밀번호를 아는 경우

터미널에서 다음 명령어를 실행하세요:

```bash
# 대화형 설정 스크립트 실행
chmod +x setup_db_interactive.sh
./setup_db_interactive.sh
```

비밀번호를 입력하면 자동으로 데이터베이스가 설정됩니다.

---

## 방법 2: 비밀번호를 모르는 경우

### 옵션 A: 비밀번호 없이 시도

```bash
mysql -u root
```

접속이 되면:

```sql
CREATE DATABASE gslts_trading CHARACTER SET utf8mb4;
USE gslts_trading;
source database/schema.sql;
EXIT;
```

### 옵션 B: MariaDB 비밀번호 재설정

1. MariaDB 중지:
```bash
sudo systemctl stop mariadb
```

2. 안전 모드로 시작:
```bash
sudo mysqld_safe --skip-grant-tables &
```

3. 비밀번호 재설정:
```bash
mysql -u root
```

```sql
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'gslts2024!@';
FLUSH PRIVILEGES;
EXIT;
```

4. MariaDB 재시작:
```bash
sudo pkill mysqld
sudo systemctl start mariadb
```

5. 새 비밀번호로 접속:
```bash
mysql -u root -p'gslts2024!@'
```

6. 데이터베이스 생성:
```sql
CREATE DATABASE gslts_trading CHARACTER SET utf8mb4;
USE gslts_trading;
source database/schema.sql;
SHOW TABLES;
EXIT;
```

7. .env 파일 업데이트:
```bash
# .env 파일에서 DB_PASSWORD 수정
DB_PASSWORD=gslts2024!@
```

---

## 방법 3: 수동 SQL 실행

MariaDB에 접속한 후, 다음 SQL을 순서대로 실행하세요:

```sql
-- 1. 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS gslts_trading
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. 데이터베이스 선택
USE gslts_trading;

-- 3. 스키마 파일 실행
source /home/nbg/Desktop/kium2/database/schema.sql;

-- 4. 테이블 확인
SHOW TABLES;
```

결과:
```
+----------------------------+
| Tables_in_gslts_trading    |
+----------------------------+
| daily_ohlcv                |
| sectors                    |
| stock_master               |
| tick_data                  |
| trades                     |
| trading_signals            |
| trading_volume_rank        |
| us_sector_performance      |
+----------------------------+
```

---

## 설정 완료 후

### 1. 통합 테스트 실행

```bash
source venv/bin/activate
python tests/test_integration.py
```

예상 결과: **7/7 테스트 통과 (100%)**

### 2. Sub Server 실행

```bash
python sub_server/main.py
```

실행 확인:
```
============================================================
Sub Server 초기화
============================================================
모의투자 모드: False
✅ 초기화 완료

🌐 모니터링 대시보드 시작: http://localhost:8001/dashboard
📊 API 엔드포인트: http://localhost:8001/api/status

============================================================
🚀 Sub Server 시작
============================================================
📊 거래대금 TOP 50 종목 수집 중...
✅ 수집 대상: 50개 종목

✅ Sub Server 가동 중...
Ctrl+C로 종료
============================================================
```

### 3. 모니터링 대시보드 접속

브라우저에서 http://localhost:8001/dashboard 접속

---

## 문제 해결

### 에러: "Access denied for user 'root'@'localhost'"

MariaDB root 비밀번호가 설정되어 있습니다. 위의 **방법 2 옵션 B**를 따라 비밀번호를 재설정하세요.

### 에러: "Can't connect to local MySQL server"

MariaDB가 실행되지 않았습니다:

```bash
sudo systemctl start mariadb
sudo systemctl status mariadb
```

### 에러: "Database 'gslts_trading' doesn't exist"

데이터베이스가 생성되지 않았습니다. 위의 방법 중 하나를 따라 데이터베이스를 생성하세요.

---

## 빠른 설정 (권장)

비밀번호를 모르는 경우, 다음 명령어를 순서대로 실행:

```bash
# 1. MariaDB 안전 모드 비밀번호 재설정
sudo systemctl stop mariadb
sudo mysqld_safe --skip-grant-tables &
sleep 5

# 2. 비밀번호 재설정 및 데이터베이스 생성
mysql -u root << 'EOF'
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'gslts2024!@';
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS gslts_trading CHARACTER SET utf8mb4;
USE gslts_trading;
EXIT
EOF

# 3. MariaDB 재시작
sudo pkill mysqld
sleep 3
sudo systemctl start mariadb

# 4. 스키마 적용
mysql -u root -p'gslts2024!@' gslts_trading < database/schema.sql

# 5. 확인
mysql -u root -p'gslts2024!@' -e "USE gslts_trading; SHOW TABLES;"

# 6. .env 업데이트
sed -i 's/DB_PASSWORD=.*/DB_PASSWORD=gslts2024!@/' .env

echo "✅ 데이터베이스 설정 완료!"
```

---

**다음 단계**: `python sub_server/main.py` 실행
