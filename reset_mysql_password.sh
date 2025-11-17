#!/bin/bash

# MariaDB root 비밀번호 재설정 스크립트

SUDO_PASSWORD="1234"
NEW_PASSWORD="gslts2024!@"

echo "================================"
echo "MariaDB 비밀번호 재설정"
echo "================================"
echo ""

echo "1. MariaDB 중지..."
echo "$SUDO_PASSWORD" | sudo -S systemctl stop mariadb

echo "2. 안전 모드로 MariaDB 시작..."
echo "$SUDO_PASSWORD" | sudo -S mysqld_safe --skip-grant-tables --skip-networking &
sleep 5

echo "3. 비밀번호 재설정..."
mysql -u root << EOF
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY '$NEW_PASSWORD';
FLUSH PRIVILEGES;
EOF

echo "4. MariaDB 재시작..."
echo "$SUDO_PASSWORD" | sudo -S pkill mysqld
sleep 3
echo "$SUDO_PASSWORD" | sudo -S systemctl start mariadb

echo ""
echo "✅ 비밀번호 재설정 완료!"
echo "새 비밀번호: $NEW_PASSWORD"
echo ""
