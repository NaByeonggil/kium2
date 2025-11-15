-- ============================================
-- GSLTS 거래 시스템 데이터베이스 스키마
-- ============================================

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS gslts_trading
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE gslts_trading;

-- ============================================
-- 1. 종목 마스터 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS stock_master (
    stock_code VARCHAR(10) PRIMARY KEY COMMENT '종목코드',
    stock_name VARCHAR(100) NOT NULL COMMENT '종목명',
    market_type VARCHAR(10) NOT NULL COMMENT '시장구분 (KOSPI, KOSDAQ, ETF)',
    sector VARCHAR(50) COMMENT '섹터',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 여부',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '등록일',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',

    INDEX idx_market (market_type),
    INDEX idx_sector (sector),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='종목 마스터';

-- ============================================
-- 2. 틱데이터 테이블 (시계열 데이터)
-- ============================================

CREATE TABLE IF NOT EXISTS tick_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL COMMENT '종목코드',
    tick_time DATETIME(3) NOT NULL COMMENT '체결시간 (밀리초)',
    price INT NOT NULL COMMENT '체결가',
    volume INT NOT NULL COMMENT '체결량',
    change_rate DECIMAL(10,2) COMMENT '등락율',
    high_price INT COMMENT '고가',
    low_price INT COMMENT '저가',
    open_price INT COMMENT '시가',
    accumulated_volume BIGINT COMMENT '누적거래량',

    INDEX idx_stock_time (stock_code, tick_time),
    INDEX idx_time (tick_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='실시간 틱데이터'
PARTITION BY RANGE (TO_DAYS(tick_time)) (
    PARTITION p_202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
    PARTITION p_202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
    PARTITION p_202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p_202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p_202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- ============================================
-- 3. 분봉 데이터 (틱 집계)
-- ============================================

CREATE TABLE IF NOT EXISTS minute_candle (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    candle_time DATETIME NOT NULL COMMENT '분봉 시간',
    time_unit TINYINT NOT NULL COMMENT '시간단위 (1, 3, 5, 10, 30, 60분)',
    open_price INT NOT NULL COMMENT '시가',
    high_price INT NOT NULL COMMENT '고가',
    low_price INT NOT NULL COMMENT '저가',
    close_price INT NOT NULL COMMENT '종가',
    volume BIGINT NOT NULL COMMENT '거래량',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_stock_time_unit (stock_code, candle_time, time_unit),
    INDEX idx_stock_time (stock_code, candle_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='분봉 데이터';

-- ============================================
-- 4. 일봉 데이터
-- ============================================

CREATE TABLE IF NOT EXISTS daily_candle (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL COMMENT '거래일',
    open_price INT NOT NULL COMMENT '시가',
    high_price INT NOT NULL COMMENT '고가',
    low_price INT NOT NULL COMMENT '저가',
    close_price INT NOT NULL COMMENT '종가',
    volume BIGINT NOT NULL COMMENT '거래량',
    trading_value BIGINT COMMENT '거래대금',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_stock_date (stock_code, trade_date),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='일봉 데이터';

-- ============================================
-- 5. 거래대금 랭킹 (10분마다 갱신)
-- ============================================

CREATE TABLE IF NOT EXISTS trading_volume_rank (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(100),
    trading_value BIGINT NOT NULL COMMENT '거래대금',
    rank_position INT NOT NULL COMMENT '순위',
    current_price INT COMMENT '현재가',
    change_rate DECIMAL(10,2) COMMENT '등락율',
    volume BIGINT COMMENT '거래량',
    collected_at DATETIME NOT NULL COMMENT '수집시간',

    INDEX idx_collected (collected_at),
    INDEX idx_rank (rank_position),
    INDEX idx_stock (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='거래대금 랭킹';

-- ============================================
-- 6. 주문 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(20) UNIQUE NOT NULL COMMENT '주문번호',
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(100),
    order_type ENUM('BUY', 'SELL') NOT NULL COMMENT '주문구분',
    order_price INT COMMENT '주문가격',
    order_quantity INT NOT NULL COMMENT '주문수량',
    executed_quantity INT DEFAULT 0 COMMENT '체결수량',
    order_status ENUM('PENDING', 'PARTIAL', 'COMPLETED', 'CANCELLED') DEFAULT 'PENDING' COMMENT '주문상태',
    trade_type VARCHAR(10) COMMENT '매매구분 (3:시장가, 0:지정가 등)',
    order_time DATETIME NOT NULL COMMENT '주문시간',
    executed_time DATETIME COMMENT '체결시간',

    INDEX idx_stock (stock_code),
    INDEX idx_status (order_status),
    INDEX idx_time (order_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='주문 내역';

-- ============================================
-- 7. 미국 섹터 데이터
-- ============================================

CREATE TABLE IF NOT EXISTS us_sector_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sector_name VARCHAR(50) NOT NULL COMMENT '섹터명 (Technology, Healthcare 등)',
    etf_symbol VARCHAR(10) COMMENT 'ETF 심볼 (XLK, XLV 등)',
    close_price DECIMAL(10,2) NOT NULL COMMENT '종가',
    change_amount DECIMAL(10,2) COMMENT '전일대비',
    change_rate DECIMAL(10,2) COMMENT '등락율',
    volume BIGINT COMMENT '거래량',
    trade_date DATE NOT NULL COMMENT '거래일',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_sector_date (sector_name, trade_date),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='미국 섹터 데이터';

-- ============================================
-- 8. 섹터 매핑 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS sector_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    us_sector VARCHAR(50) NOT NULL COMMENT '미국 섹터',
    kr_sector VARCHAR(50) NOT NULL COMMENT '한국 섹터',
    correlation DECIMAL(5,4) DEFAULT 0.7000 COMMENT '상관계수 (0~1)',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_us_sector (us_sector)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='미국-한국 섹터 매핑';

-- 기본 매핑 데이터 삽입
INSERT INTO sector_mapping (us_sector, kr_sector, correlation) VALUES
('Technology', 'IT', 0.75),
('Technology', '반도체', 0.80),
('Financial', '금융', 0.65),
('Energy', '에너지', 0.70),
('Energy', '정유', 0.72),
('Healthcare', '제약', 0.60),
('Healthcare', '바이오', 0.62),
('Industrial', '산업재', 0.68),
('Consumer Staples', '필수소비재', 0.55),
('Consumer Discretionary', '자동차', 0.58),
('Materials', '화학', 0.63),
('Real Estate', '부동산', 0.50),
('Communication', '통신', 0.60)
ON DUPLICATE KEY UPDATE correlation=VALUES(correlation);

-- ============================================
-- 9. 시스템 로그 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    log_level VARCHAR(10) NOT NULL COMMENT 'INFO, WARNING, ERROR',
    log_message TEXT NOT NULL,
    module_name VARCHAR(100) COMMENT '모듈명',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_level (log_level),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='시스템 로그';

-- ============================================
-- 뷰 (View) 생성
-- ============================================

-- 최신 거래대금 TOP 50
CREATE OR REPLACE VIEW v_top_trading_stocks AS
SELECT
    stock_code,
    stock_name,
    trading_value,
    rank_position,
    current_price,
    change_rate,
    volume,
    collected_at
FROM trading_volume_rank
WHERE collected_at = (SELECT MAX(collected_at) FROM trading_volume_rank)
  AND rank_position <= 50
ORDER BY rank_position;

-- 오늘의 틱데이터 통계
CREATE OR REPLACE VIEW v_today_tick_stats AS
SELECT
    stock_code,
    COUNT(*) as tick_count,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price,
    SUM(volume) as total_volume
FROM tick_data
WHERE DATE(tick_time) = CURDATE()
GROUP BY stock_code;

-- ============================================
-- 인덱스 최적화
-- ============================================

-- 틱데이터 복합 인덱스 (자주 조회되는 패턴)
-- ALTER TABLE tick_data ADD INDEX idx_stock_time_price (stock_code, tick_time, price);

-- ============================================
-- 완료
-- ============================================

-- 테이블 목록 확인
SHOW TABLES;

-- 스키마 생성 완료 메시지
SELECT '✅ 데이터베이스 스키마 생성 완료!' AS message;
