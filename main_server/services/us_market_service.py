"""
US Market 데이터 서비스

Yahoo Finance를 사용한 미국 ETF 섹터 데이터 조회
- Rate limit 대응을 위한 배치 처리
- 즉시 응답을 위한 기본 데이터 제공
"""

import logging
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# yfinance 설치 여부 확인
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance가 설치되지 않았습니다. pip install yfinance")


@dataclass
class USETFInfo:
    """US ETF 정보"""
    symbol: str
    name: str
    sector: str
    sector_kr: str


# US 섹터 ETF 매핑 (전체)
US_SECTOR_ETFS = [
    # 주요 지수
    USETFInfo("SPY", "SPDR S&P 500 ETF", "Index", "S&P500 지수"),
    USETFInfo("QQQ", "Invesco QQQ Trust", "Index", "나스닥100 지수"),
    USETFInfo("DIA", "SPDR Dow Jones Industrial", "Index", "다우존스 지수"),
    USETFInfo("IWM", "iShares Russell 2000", "Index", "러셀2000 소형주"),

    # 섹터 ETF (SPDR)
    USETFInfo("XLK", "Technology Select Sector", "Technology", "기술주"),
    USETFInfo("XLF", "Financial Select Sector", "Financial", "금융주"),
    USETFInfo("XLE", "Energy Select Sector", "Energy", "에너지/석유"),
    USETFInfo("XLV", "Health Care Select Sector", "Healthcare", "헬스케어/제약"),
    USETFInfo("XLI", "Industrial Select Sector", "Industrial", "산업재/제조"),
    USETFInfo("XLP", "Consumer Staples Select Sector", "Consumer Staples", "필수소비재"),
    USETFInfo("XLY", "Consumer Discretionary Select Sector", "Consumer Discretionary", "경기소비재"),
    USETFInfo("XLU", "Utilities Select Sector", "Utilities", "유틸리티/전력"),
    USETFInfo("XLB", "Materials Select Sector", "Materials", "소재/화학"),
    USETFInfo("XLRE", "Real Estate Select Sector", "Real Estate", "부동산/리츠"),
    USETFInfo("XLC", "Communication Services Select Sector", "Communication", "통신/미디어"),

    # 반도체
    USETFInfo("SOXX", "iShares Semiconductor ETF", "Semiconductor", "반도체"),
    USETFInfo("SMH", "VanEck Semiconductor ETF", "Semiconductor", "반도체(VanEck)"),
    USETFInfo("SOXL", "Direxion Semiconductor Bull 3X", "Semiconductor", "반도체 3배 레버리지"),

    # 기술/성장주
    USETFInfo("ARKK", "ARK Innovation ETF", "Innovation", "혁신성장주"),
    USETFInfo("IGV", "iShares Software ETF", "Software", "소프트웨어"),
    USETFInfo("CLOU", "Global X Cloud Computing", "Cloud", "클라우드 컴퓨팅"),
    USETFInfo("BOTZ", "Global X Robotics & AI", "AI/Robotics", "AI/로보틱스"),
    USETFInfo("SKYY", "First Trust Cloud Computing", "Cloud", "클라우드"),

    # 전기차/클린에너지
    USETFInfo("LIT", "Global X Lithium & Battery", "EV/Battery", "리튬/배터리"),
    USETFInfo("DRIV", "Global X Autonomous & EV", "EV", "자율주행/전기차"),
    USETFInfo("ICLN", "iShares Global Clean Energy", "Clean Energy", "클린에너지"),
    USETFInfo("TAN", "Invesco Solar ETF", "Solar", "태양광"),
    USETFInfo("QCLN", "First Trust Nasdaq Clean Edge", "Clean Energy", "청정에너지"),

    # 채권/안전자산
    USETFInfo("TLT", "iShares 20+ Year Treasury", "Bond", "미국 장기국채"),
    USETFInfo("IEF", "iShares 7-10 Year Treasury", "Bond", "미국 중기국채"),
    USETFInfo("LQD", "iShares Investment Grade Corp", "Bond", "투자등급 회사채"),
    USETFInfo("HYG", "iShares High Yield Corp", "Bond", "하이일드 회사채"),
    USETFInfo("GLD", "SPDR Gold Shares", "Commodity", "금"),
    USETFInfo("SLV", "iShares Silver Trust", "Commodity", "은"),

    # 국제/신흥국
    USETFInfo("EEM", "iShares MSCI Emerging", "International", "신흥국"),
    USETFInfo("EFA", "iShares MSCI EAFE", "International", "선진국(미국제외)"),
    USETFInfo("FXI", "iShares China Large-Cap", "China", "중국 대형주"),
    USETFInfo("EWJ", "iShares MSCI Japan", "Japan", "일본"),
    USETFInfo("EWY", "iShares MSCI South Korea", "Korea", "한국"),

    # 배당/가치주
    USETFInfo("VYM", "Vanguard High Dividend", "Dividend", "고배당주"),
    USETFInfo("SCHD", "Schwab US Dividend Equity", "Dividend", "미국배당주"),
    USETFInfo("DVY", "iShares Select Dividend", "Dividend", "배당 셀렉트"),

    # 변동성/헤지
    USETFInfo("VXX", "iPath VIX Short-Term", "Volatility", "변동성(VIX)"),
    USETFInfo("UVXY", "ProShares Ultra VIX", "Volatility", "VIX 1.5배"),
]

# US 섹터 → 한국 종목 매핑
SECTOR_KR_MAPPING = {
    "Technology": {
        "sector_kr": "IT/반도체",
        "stocks": [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
            {"code": "035420", "name": "NAVER"},
            {"code": "035720", "name": "카카오"},
        ]
    },
    "Semiconductor": {
        "sector_kr": "반도체",
        "stocks": [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
            {"code": "042700", "name": "한미반도체"},
            {"code": "403870", "name": "HPSP"},
        ]
    },
    "Financial": {
        "sector_kr": "금융",
        "stocks": [
            {"code": "105560", "name": "KB금융"},
            {"code": "055550", "name": "신한지주"},
            {"code": "086790", "name": "하나금융지주"},
            {"code": "316140", "name": "우리금융지주"},
        ]
    },
    "Energy": {
        "sector_kr": "에너지/정유",
        "stocks": [
            {"code": "096770", "name": "SK이노베이션"},
            {"code": "010950", "name": "S-Oil"},
            {"code": "267250", "name": "HD현대"},
        ]
    },
    "Healthcare": {
        "sector_kr": "제약/바이오",
        "stocks": [
            {"code": "207940", "name": "삼성바이오로직스"},
            {"code": "068270", "name": "셀트리온"},
            {"code": "326030", "name": "SK바이오팜"},
            {"code": "128940", "name": "한미약품"},
        ]
    },
    "Industrial": {
        "sector_kr": "산업재",
        "stocks": [
            {"code": "329180", "name": "HD현대중공업"},
            {"code": "009540", "name": "HD한국조선해양"},
            {"code": "034020", "name": "두산에너빌리티"},
        ]
    },
    "Consumer Staples": {
        "sector_kr": "필수소비재",
        "stocks": [
            {"code": "097950", "name": "CJ제일제당"},
            {"code": "271560", "name": "오리온"},
            {"code": "051900", "name": "LG생활건강"},
        ]
    },
    "Consumer Discretionary": {
        "sector_kr": "자동차/유통",
        "stocks": [
            {"code": "005380", "name": "현대차"},
            {"code": "000270", "name": "기아"},
            {"code": "023530", "name": "롯데쇼핑"},
        ]
    },
    "Utilities": {
        "sector_kr": "유틸리티",
        "stocks": [
            {"code": "015760", "name": "한국전력"},
            {"code": "036460", "name": "한국가스공사"},
        ]
    },
    "Materials": {
        "sector_kr": "화학/소재",
        "stocks": [
            {"code": "051910", "name": "LG화학"},
            {"code": "006400", "name": "삼성SDI"},
            {"code": "005490", "name": "POSCO홀딩스"},
        ]
    },
    "Communication": {
        "sector_kr": "통신",
        "stocks": [
            {"code": "017670", "name": "SK텔레콤"},
            {"code": "030200", "name": "KT"},
            {"code": "032640", "name": "LG유플러스"},
        ]
    },
}


class USMarketService:
    """US Market 데이터 서비스"""

    def __init__(self):
        """초기화"""
        self._cache: Dict[str, dict] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=30)
        self._is_loading = False
        self._load_lock = threading.Lock()
        # 시작 시 기본 데이터로 초기화
        self._init_with_defaults()

    def _init_with_defaults(self):
        """기본 데이터로 초기화 (즉시 응답 가능하도록)"""
        results = []
        for etf in US_SECTOR_ETFS:
            data = self._get_mock_data(etf.symbol)
            kr_mapping = SECTOR_KR_MAPPING.get(etf.sector, {})
            data["related_kr_stocks"] = self._convert_kr_stocks(kr_mapping.get("stocks", []))
            results.append(data)

        self._cache["all_sectors"] = results
        self._cache_time = datetime.now()
        logger.info(f"US Market 기본 데이터 초기화 완료 ({len(results)}개 ETF)")

    def _convert_kr_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """한국 종목 데이터를 프론트엔드 형식으로 변환"""
        return [
            {"stock_code": s.get("code", ""), "stock_name": s.get("name", "")}
            for s in stocks
        ]

    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if not self._cache_time:
            return False
        return datetime.now() - self._cache_time < self._cache_duration

    def get_etf_data(self, symbol: str) -> Optional[Dict]:
        """
        단일 ETF 데이터 조회

        Args:
            symbol: ETF 티커 (예: XLK, SPY)

        Returns:
            dict: ETF 데이터
        """
        if not YFINANCE_AVAILABLE:
            return self._get_mock_data(symbol)

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")

            if hist.empty:
                return self._get_mock_data(symbol)

            current = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current

            change = current - prev_close
            change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

            # ETF 정보 찾기
            etf_info = next((e for e in US_SECTOR_ETFS if e.symbol == symbol), None)

            return {
                "symbol": symbol,
                "name": etf_info.name if etf_info else symbol,
                "sector": etf_info.sector if etf_info else "Unknown",
                "sector_kr": etf_info.sector_kr if etf_info else "기타",
                "price": round(current, 2),
                "prev_close": round(prev_close, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
            }

        except Exception as e:
            logger.error(f"ETF 데이터 조회 실패 ({symbol}): {e}")
            return self._get_mock_data(symbol)

    def _load_real_data_background(self):
        """백그라운드에서 실제 데이터 로드 (rate limit 대응)"""
        if self._is_loading:
            return

        with self._load_lock:
            if self._is_loading:
                return
            self._is_loading = True

        try:
            logger.info("백그라운드 US Market 데이터 로드 시작...")
            results = []

            # 주요 ETF만 먼저 로드 (15개)
            priority_symbols = [
                "SPY", "QQQ", "DIA", "IWM",  # 지수
                "XLK", "XLF", "XLE", "XLV", "XLI",  # 섹터
                "SOXX", "SMH",  # 반도체
                "TLT", "GLD",  # 안전자산
                "EEM", "FXI"  # 신흥국
            ]

            # 우선순위 ETF 로드
            for symbol in priority_symbols:
                etf_info = next((e for e in US_SECTOR_ETFS if e.symbol == symbol), None)
                if etf_info:
                    data = self.get_etf_data(symbol)
                    if data:
                        kr_mapping = SECTOR_KR_MAPPING.get(etf_info.sector, {})
                        data["related_kr_stocks"] = self._convert_kr_stocks(kr_mapping.get("stocks", []))
                        results.append(data)
                    time.sleep(0.5)  # Rate limit 방지

            # 나머지 ETF는 모의 데이터로 채우기
            loaded_symbols = {r["symbol"] for r in results}
            for etf in US_SECTOR_ETFS:
                if etf.symbol not in loaded_symbols:
                    data = self._get_mock_data(etf.symbol)
                    kr_mapping = SECTOR_KR_MAPPING.get(etf.sector, {})
                    data["related_kr_stocks"] = self._convert_kr_stocks(kr_mapping.get("stocks", []))
                    results.append(data)

            # 캐시 업데이트
            self._cache["all_sectors"] = results
            self._cache_time = datetime.now()
            logger.info(f"US Market 데이터 로드 완료 (실제: {len(loaded_symbols)}, 모의: {len(results) - len(loaded_symbols)})")

        except Exception as e:
            logger.error(f"백그라운드 데이터 로드 실패: {e}")
        finally:
            self._is_loading = False

    def get_all_sectors(self) -> List[Dict]:
        """
        모든 섹터 ETF 데이터 조회 (즉시 응답)

        Returns:
            list: 섹터별 ETF 데이터 목록
        """
        # 캐시가 없으면 기본 데이터 초기화
        if "all_sectors" not in self._cache:
            self._init_with_defaults()

        # 캐시가 만료되었으면 백그라운드에서 실제 데이터 로드
        if not self._is_cache_valid() and not self._is_loading:
            thread = threading.Thread(target=self._load_real_data_background)
            thread.daemon = True
            thread.start()

        return self._cache.get("all_sectors", [])

    def get_sector_performance(self) -> Dict:
        """
        섹터 성과 요약

        Returns:
            dict: 섹터 성과 (상승/하락 순위)
        """
        sectors = self.get_all_sectors()

        # 변동률 기준 정렬
        sorted_sectors = sorted(sectors, key=lambda x: x.get('change_percent', 0), reverse=True)

        return {
            "updated_at": datetime.now().isoformat(),
            "top_gainers": sorted_sectors[:5],
            "top_losers": sorted_sectors[-5:][::-1],
            "all_sectors": sorted_sectors
        }

    def get_sector_with_kr_stocks(self, sector: str) -> Optional[Dict]:
        """
        섹터 + 관련 한국 종목

        Args:
            sector: 섹터명 (예: Technology, Healthcare)

        Returns:
            dict: 섹터 정보 + 한국 관련 종목
        """
        kr_mapping = SECTOR_KR_MAPPING.get(sector)

        if not kr_mapping:
            return None

        # 해당 섹터 ETF 찾기
        etf = next((e for e in US_SECTOR_ETFS if e.sector == sector), None)

        if etf:
            etf_data = self.get_etf_data(etf.symbol)
        else:
            etf_data = None

        return {
            "sector": sector,
            "sector_kr": kr_mapping["sector_kr"],
            "etf": etf_data,
            "kr_stocks": kr_mapping["stocks"]
        }

    def get_recommended_sectors(self) -> List[Dict]:
        """
        추천 섹터 (전일 상승률 기준)

        Returns:
            list: 추천 섹터 목록 (상위 3개)
        """
        performance = self.get_sector_performance()
        top_sectors = performance["top_gainers"][:3]

        recommendations = []
        for sector_data in top_sectors:
            sector = sector_data.get("sector")
            kr_mapping = SECTOR_KR_MAPPING.get(sector, {})

            recommendations.append({
                "sector": sector,
                "sector_kr": kr_mapping.get("sector_kr", sector_data.get("sector_kr")),
                "etf_symbol": sector_data["symbol"],
                "change_percent": sector_data["change_percent"],
                "recommendation": "강세 예상" if sector_data["change_percent"] > 1 else "상승 예상",
                "kr_stocks": kr_mapping.get("stocks", [])
            })

        return recommendations

    def _get_mock_data(self, symbol: str) -> Dict:
        """모의 데이터 반환 (yfinance 미설치 시)"""
        etf_info = next((e for e in US_SECTOR_ETFS if e.symbol == symbol), None)

        # 심볼별 가상 데이터
        mock_prices = {
            "SPY": 450.0, "QQQ": 380.0, "XLK": 180.0, "XLF": 38.0,
            "XLE": 85.0, "XLV": 140.0, "XLI": 110.0, "XLP": 75.0,
            "XLY": 175.0, "XLU": 65.0, "XLB": 80.0, "XLRE": 40.0,
            "XLC": 70.0, "SOXX": 220.0, "SMH": 200.0
        }

        import random
        price = mock_prices.get(symbol, 100.0)
        change_pct = random.uniform(-2.0, 3.0)
        change = price * change_pct / 100

        return {
            "symbol": symbol,
            "name": etf_info.name if etf_info else symbol,
            "sector": etf_info.sector if etf_info else "Unknown",
            "sector_kr": etf_info.sector_kr if etf_info else "기타",
            "price": round(price, 2),
            "prev_close": round(price - change, 2),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "volume": random.randint(1000000, 50000000),
            "is_mock": True
        }


# 서비스 싱글톤
_us_market_service: Optional[USMarketService] = None


def get_us_market_service() -> USMarketService:
    """US Market 서비스 싱글톤"""
    global _us_market_service
    if _us_market_service is None:
        _us_market_service = USMarketService()
    return _us_market_service
