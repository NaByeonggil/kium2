#!/bin/bash

# GSLTS 데이터베이스 설정 스크립트

echo "================================"
echo "GSLTS 데이터베이스 설정"
echo "================================"
echo ""

# sudo 비밀번호
SUDO_PASSWORD="1234"

# MariaDB root 비밀번호 설정
DB_ROOT_PASSWORD="gslts2024!@"

echo "1. MariaDB 접속 확인 중..."
# sudo mysql로 접속 (unix_socket 인증)
echo "$SUDO_PASSWORD" | sudo -S mysql -e "SELECT 'MariaDB 접속 성공!' AS status;" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ MariaDB 접속 실패"
    exit 1
fi

echo "✅ MariaDB 접속 성공"

echo ""
echo "2. MariaDB root 비밀번호 설정 중..."
echo "$SUDO_PASSWORD" | sudo -S mysql -e "
ALTER USER 'root'@'localhost' IDENTIFIED BY '$DB_ROOT_PASSWORD';
FLUSH PRIVILEGES;
"

if [ $? -eq 0 ]; then
    echo "✅ root 비밀번호 설정 완료"
else
    echo "⚠️ root 비밀번호 이미 설정되어 있을 수 있음"
fi

echo ""
echo "3. 데이터베이스 생성 중..."
echo "$SUDO_PASSWORD" | sudo -S mysql -e "
CREATE DATABASE IF NOT EXISTS gslts_trading
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
"

if [ $? -eq 0 ]; then
    echo "✅ 데이터베이스 생성 완료"
else
    echo "❌ 데이터베이스 생성 실패"
    exit 1
fi

echo ""
echo "4. 스키마 적용 중..."
echo "$SUDO_PASSWORD" | sudo -S mysql gslts_trading < database/schema.sql

if [ $? -eq 0 ]; then
    echo "✅ 스키마 적용 완료"
else
    echo "❌ 스키마 적용 실패"
    exit 1
fi

echo ""
echo "5. 테이블 확인..."
echo "$SUDO_PASSWORD" | sudo -S mysql -e "USE gslts_trading; SHOW TABLES;"

echo ""
echo "6. .env 파일 업데이트..."
sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_ROOT_PASSWORD/" .env

echo ""
echo "================================"
echo "✅ 데이터베이스 설정 완료!"
echo "================================"
echo ""
echo "설정 정보:"
echo "  데이터베이스: gslts_trading"
echo "  사용자: root"
echo "  비밀번호: $DB_ROOT_PASSWORD"
echo ""
echo "다음 단계:"
echo "  1. python sub_server/main.py 실행"
echo "  2. http://localhost:8001/dashboard 접속"
echo ""
