#!/bin/bash

echo "================================"
echo "MariaDB 비밀번호 재설정"
echo "================================"

# 1. MariaDB 중지
echo "1. MariaDB 중지..."
sudo systemctl stop mariadb
sleep 2

# 2. mysqld_safe로 안전 모드 시작
echo "2. 안전 모드로 시작..."
sudo mysqld_safe --skip-grant-tables --skip-networking &
sleep 5

# 3. 비밀번호 재설정
echo "3. 비밀번호 재설정..."
mysql -u root << 'EOF'
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'gslts2024!@';
FLUSH PRIVILEGES;
EOF

# 4. mysqld_safe 종료
echo "4. 안전 모드 종료..."
sudo pkill -9 mysqld
sleep 3

# 5. MariaDB 정상 시작
echo "5. MariaDB 재시작..."
sudo systemctl start mariadb
sleep 3

# 6. 접속 테스트
echo "6. 접속 테스트..."
mysql -u root -p'gslts2024!@' -e "SELECT 'Success!' AS status;"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 비밀번호 재설정 완료!"
    echo "새 비밀번호: gslts2024!@"

    # 데이터베이스 생성
    echo ""
    echo "7. 데이터베이스 생성..."
    mysql -u root -p'gslts2024!@' << 'EOF'
CREATE DATABASE IF NOT EXISTS gslts_trading CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES LIKE 'gslts_trading';
EOF

    # 스키마 적용
    echo ""
    echo "8. 스키마 적용..."
    mysql -u root -p'gslts2024!@' gslts_trading < database/schema.sql

    # 테이블 확인
    echo ""
    echo "9. 테이블 확인..."
    mysql -u root -p'gslts2024!@' -e "USE gslts_trading; SHOW TABLES;"

    echo ""
    echo "================================"
    echo "✅ 모든 설정 완료!"
    echo "================================"
else
    echo ""
    echo "❌ 비밀번호 재설정 실패"
fi
