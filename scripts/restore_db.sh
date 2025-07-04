#!/bin/bash
set -e

echo "开始还原 MySQL 数据库..."

# 环境变量由 Actions 注入
# MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

# 自动查找 data 目录下唯一的 .sql 文件
SQL_FILE=${1:-$(ls data/*.sql 2>/dev/null | head -n1)}
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ 没有找到 SQL 备份文件: $SQL_FILE"
    exit 1
fi

echo "还原 SQL 文件: $SQL_FILE"
echo "连接参数: host=${MYSQL_HOST:-127.0.0.1}, port=${MYSQL_PORT:-3306}, user=${MYSQL_USER:-root}, db=${MYSQL_DATABASE:-lotto_ai3_v2}"

mysql -h"${MYSQL_HOST:-127.0.0.1}" \
      -P"${MYSQL_PORT:-3306}" \
      -u"${MYSQL_USER:-root}" \
      -p"${MYSQL_PASSWORD:-password}" \
      -e "CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE:-lotto_ai3_v2}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

mysql -h"${MYSQL_HOST:-127.0.0.1}" \
      -P"${MYSQL_PORT:-3306}" \
      -u"${MYSQL_USER:-root}" \
      -p"${MYSQL_PASSWORD:-password}" \
      "${MYSQL_DATABASE:-lotto_ai3_v2}" < "$SQL_FILE"


echo "✅ MySQL 数据库还原完成！"
