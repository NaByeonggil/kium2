#!/bin/bash

# GSLTS 데이터베이스 대화형 설정 스크립트

echo "================================"
echo "GSLTS 데이터베이스 설정"
echo "================================"
echo ""

# MariaDB root 비밀번호 입력
echo "MariaDB root 비밀번호를 입력하세요."
echo "(비밀번호가 없으면 그냥 Enter를 누르세요)"
read -s -p "비밀번호: " DB_PASSWORD
echo ""

# 비밀번호가 없으면 빈 문자열로 처리
if [ -z "$DB_PASSWORD" ]; then
    MYSQL_CMD="mysql -u root"
else
    MYSQL_CMD="mysql -u root -p$DB_PASSWORD"
fi

echo ""
echo "1. MariaDB 접속 테스트..."
$MYSQL_CMD -e "SELECT 'MariaDB 접속 성공!' AS status;" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ MariaDB 접속 실패. 비밀번호를 확인하세요."
    echo ""
    echo "💡 비밀번호를 모르시나요?"
    echo "   다음 방법을 시도해보세요:"
    echo "   1. sudo mysql (sudo로 접속)"
    echo "   2. MariaDB 비밀번호 재설정"
    exit 1
fi

echo "✅ MariaDB 접속 성공"

echo ""
echo "2. 데이터베이스 생성..."
$MYSQL_CMD -e "
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
echo "3. 스키마 적용..."
$MYSQL_CMD gslts_trading < database/schema.sql

if [ $? -eq 0 ]; then
    echo "✅ 스키마 적용 완료"
else
    echo "❌ 스키마 적용 실패"
    exit 1
fi

echo ""
echo "4. 테이블 확인..."
$MYSQL_CMD -e "USE gslts_trading; SHOW TABLES;"

echo ""
echo "5. .env 파일 업데이트..."
if [ -z "$DB_PASSWORD" ]; then
    sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=/" .env
else
    sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
fi

echo ""
echo "================================"
echo "✅ 데이터베이스 설정 완료!"
echo "================================"
echo ""
echo "설정 정보:"
echo "  데이터베이스: gslts_trading"
echo "  사용자: root"
echo ""
echo "다음 단계:"
echo "  source venv/bin/activate"
echo "  python sub_server/main.py"
echo ""
echo "모니터링 대시보드:"
echo "  http://localhost:8001/dashboard"
echo ""
