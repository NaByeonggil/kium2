#!/bin/bash

# sudo 비밀번호 미리 입력
sudo -v

# MariaDB 데이터베이스 설정
sudo mysql << 'EOF'
CREATE DATABASE IF NOT EXISTS gslts_trading CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'gslts2024!@';
FLUSH PRIVILEGES;
SHOW DATABASES LIKE 'gslts_trading';
EOF

echo ""
echo "✅ 데이터베이스 생성 완료"
echo ""

# 스키마 적용
echo "스키마 적용 중..."
sudo mysql gslts_trading < database/schema.sql

echo ""
echo "✅ 스키마 적용 완료"
echo ""

# 테이블 확인
sudo mysql -e "USE gslts_trading; SHOW TABLES;"

echo ""
echo "================================"
echo "✅ 데이터베이스 설정 완료!"
echo "================================"
