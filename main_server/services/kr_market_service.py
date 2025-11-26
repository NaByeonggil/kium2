"""
KR Market 데이터 서비스

키움 API를 사용한 한국 ETF 섹터 데이터 조회
"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KRETFInfo:
    """KR ETF 정보"""
    code: str
    name: str
    sector: str
    sector_kr: str


# 한국 섹터 ETF 매핑
KR_SECTOR_ETFS = [
    # 주요 지수
    KRETFInfo("069500", "KODEX 200", "Index", "코스피200"),
    KRETFInfo("229200", "KODEX 코스닥150", "Index", "코스닥150"),
    KRETFInfo("292190", "KODEX KRX300", "Index", "KRX300"),
    KRETFInfo("252670", "KODEX 200선물인버스2X", "Index", "인버스2X"),
    KRETFInfo("122630", "KODEX 레버리지", "Index", "레버리지2X"),

    # 반도체
    KRETFInfo("091160", "KODEX 반도체", "Semiconductor", "반도체"),
    KRETFInfo("395160", "KODEX 2차전지핵심소재10", "Semiconductor", "2차전지소재"),
    KRETFInfo("466920", "KODEX AI반도체핵심장비", "Semiconductor", "AI반도체장비"),

    # 2차전지/배터리
    KRETFInfo("305720", "KODEX 2차전지산업", "Battery", "2차전지"),
    KRETFInfo("371460", "TIGER 2차전지테마", "Battery", "2차전지테마"),
    KRETFInfo("455850", "KODEX 2차전지TOP10", "Battery", "2차전지TOP10"),

    # 자동차
    KRETFInfo("091180", "KODEX 자동차", "Auto", "자동차"),
    KRETFInfo("091220", "TIGER 은행", "Auto", "자동차부품"),

    # 금융
    KRETFInfo("091170", "KODEX 은행", "Financial", "은행"),
    KRETFInfo("140700", "KODEX 보험", "Financial", "보험"),
    KRETFInfo("157500", "TIGER 증권", "Financial", "증권"),

    # 철강/소재
    KRETFInfo("117680", "KODEX 철강", "Materials", "철강"),
    KRETFInfo("117460", "KODEX 에너지화학", "Materials", "에너지화학"),
    KRETFInfo("117690", "TIGER 화학", "Materials", "화학"),

    # 건설
    KRETFInfo("117700", "KODEX 건설", "Construction", "건설"),
    KRETFInfo("139220", "TIGER 건설기계", "Construction", "건설기계"),

    # 헬스케어/바이오
    KRETFInfo("266420", "KODEX 헬스케어", "Healthcare", "헬스케어"),
    KRETFInfo("244580", "KODEX 바이오", "Healthcare", "바이오"),
    KRETFInfo("227540", "TIGER 헬스케어", "Healthcare", "헬스케어(TIGER)"),

    # IT/소프트웨어
    KRETFInfo("266370", "KODEX IT", "Technology", "IT"),
    KRETFInfo("371470", "TIGER 게임산업", "Technology", "게임"),
    KRETFInfo("395750", "TIGER 미디어컨텐츠", "Technology", "미디어컨텐츠"),

    # 통신
    KRETFInfo("091230", "TIGER 통신", "Communication", "통신"),

    # 유틸리티/에너지
    KRETFInfo("117580", "KODEX 유틸리티", "Utilities", "유틸리티"),
    KRETFInfo("285000", "KODEX 신재생에너지", "Utilities", "신재생에너지"),

    # 소비재
    KRETFInfo("266390", "KODEX 미디어&엔터테인먼트", "Consumer", "미디어/엔터"),
    KRETFInfo("228790", "TIGER 화장품", "Consumer", "화장품"),
    KRETFInfo("227570", "TIGER 여행레저", "Consumer", "여행레저"),

    # 조선/운송
    KRETFInfo("139230", "TIGER 조선TOP10", "Industrial", "조선"),
    KRETFInfo("140710", "KODEX 운송", "Industrial", "운송"),
    KRETFInfo("460850", "KODEX K-친환경선박액티브", "Industrial", "친환경선박"),

    # 채권
    KRETFInfo("148070", "KODEX 국고채3년", "Bond", "국고채3년"),
    KRETFInfo("152380", "KODEX 국고채10년", "Bond", "국고채10년"),
    KRETFInfo("182490", "TIGER 미국채10년선물", "Bond", "미국채10년"),

    # 금/원자재
    KRETFInfo("132030", "KODEX 골드선물(H)", "Commodity", "금"),
    KRETFInfo("130680", "TIGER 원유선물Enhanced(H)", "Commodity", "원유"),

    # 해외(미국)
    KRETFInfo("360750", "TIGER 미국S&P500", "International", "S&P500"),
    KRETFInfo("133690", "TIGER 미국나스닥100", "International", "나스닥100"),
    KRETFInfo("381170", "TIGER 미국테크TOP10 INDXX", "International", "미국테크TOP10"),
    KRETFInfo("453850", "TIGER 미국필라델피아반도체나스닥", "International", "미국반도체"),

    # 해외(중국/신흥국)
    KRETFInfo("192090", "TIGER 차이나CSI300", "International", "중국CSI300"),
    KRETFInfo("371450", "TIGER 차이나전기차SOLACTIVE", "International", "중국전기차"),
    KRETFInfo("195930", "TIGER 인도니프티50", "International", "인도니프티50"),
]

# 섹터별 관련 종목
SECTOR_STOCKS = {
    "Semiconductor": [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"},
        {"code": "042700", "name": "한미반도체"},
        {"code": "403870", "name": "HPSP"},
    ],
    "Battery": [
        {"code": "006400", "name": "삼성SDI"},
        {"code": "051910", "name": "LG화학"},
        {"code": "373220", "name": "LG에너지솔루션"},
        {"code": "247540", "name": "에코프로비엠"},
    ],
    "Auto": [
        {"code": "005380", "name": "현대차"},
        {"code": "000270", "name": "기아"},
        {"code": "012330", "name": "현대모비스"},
    ],
    "Financial": [
        {"code": "105560", "name": "KB금융"},
        {"code": "055550", "name": "신한지주"},
        {"code": "086790", "name": "하나금융지주"},
    ],
    "Healthcare": [
        {"code": "207940", "name": "삼성바이오로직스"},
        {"code": "068270", "name": "셀트리온"},
        {"code": "326030", "name": "SK바이오팜"},
    ],
    "Technology": [
        {"code": "035420", "name": "NAVER"},
        {"code": "035720", "name": "카카오"},
        {"code": "263750", "name": "펄어비스"},
    ],
    "Industrial": [
        {"code": "329180", "name": "HD현대중공업"},
        {"code": "009540", "name": "HD한국조선해양"},
        {"code": "042660", "name": "한화오션"},
    ],
    "Materials": [
        {"code": "005490", "name": "POSCO홀딩스"},
        {"code": "010130", "name": "고려아연"},
        {"code": "051910", "name": "LG화학"},
    ],
    "Construction": [
        {"code": "000720", "name": "현대건설"},
        {"code": "034730", "name": "SK"},
        {"code": "000210", "name": "DL"},
    ],
    "Communication": [
        {"code": "017670", "name": "SK텔레콤"},
        {"code": "030200", "name": "KT"},
        {"code": "032640", "name": "LG유플러스"},
    ],
    "Utilities": [
        {"code": "015760", "name": "한국전력"},
        {"code": "036460", "name": "한국가스공사"},
    ],
    "Consumer": [
        {"code": "051900", "name": "LG생활건강"},
        {"code": "090430", "name": "아모레퍼시픽"},
        {"code": "352820", "name": "하이브"},
    ],
}


class KRMarketService:
    """KR Market 데이터 서비스"""

    def __init__(self, kiwoom_client=None):
        """초기화"""
        self._kiwoom_client = kiwoom_client
        self._cache: Dict[str, dict] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
        self._is_loading = False
        self._load_lock = threading.Lock()
        # 기본 데이터로 초기화
        self._init_with_defaults()

    def set_kiwoom_client(self, client):
        """키움 클라이언트 설정"""
        self._kiwoom_client = client

    def _init_with_defaults(self):
        """기본 데이터로 초기화"""
        results = []
        for etf in KR_SECTOR_ETFS:
            data = self._get_default_data(etf)
            related_stocks = SECTOR_STOCKS.get(etf.sector, [])
            data["related_stocks"] = related_stocks
            results.append(data)

        self._cache["all_sectors"] = results
        self._cache_time = datetime.now()
        logger.info(f"KR Market 기본 데이터 초기화 완료 ({len(results)}개 ETF)")

    def _get_default_data(self, etf: KRETFInfo) -> Dict:
        """기본 데이터 반환"""
        return {
            "code": etf.code,
            "name": etf.name,
            "sector": etf.sector,
            "sector_kr": etf.sector_kr,
            "price": 0,
            "prev_close": 0,
            "change": 0,
            "change_percent": 0.0,
            "volume": 0,
            "is_loading": True
        }

    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if not self._cache_time:
            return False
        return datetime.now() - self._cache_time < self._cache_duration

    def get_etf_data(self, code: str) -> Optional[Dict]:
        """단일 ETF 데이터 조회"""
        etf_info = next((e for e in KR_SECTOR_ETFS if e.code == code), None)
        if not etf_info:
            return None

        if not self._kiwoom_client:
            return self._get_default_data(etf_info)

        try:
            result = self._kiwoom_client.get_current_price(code)
            if result.get("success"):
                change = result.get("change_price", 0)
                prev_close = result.get("prev_close", 0)
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0

                return {
                    "code": code,
                    "name": etf_info.name,
                    "sector": etf_info.sector,
                    "sector_kr": etf_info.sector_kr,
                    "price": result.get("current_price", 0),
                    "prev_close": prev_close,
                    "change": change,
                    "change_percent": round(change_pct, 2),
                    "volume": result.get("volume", 0),
                    "is_loading": False
                }
        except Exception as e:
            logger.error(f"ETF 데이터 조회 실패 ({code}): {e}")

        return self._get_default_data(etf_info)

    def _load_real_data_background(self):
        """백그라운드에서 실제 데이터 로드"""
        if self._is_loading or not self._kiwoom_client:
            return

        with self._load_lock:
            if self._is_loading:
                return
            self._is_loading = True

        try:
            logger.info("백그라운드 KR Market 데이터 로드 시작...")
            results = []

            # 주요 ETF 우선 로드
            priority_codes = [
                "069500", "229200",  # 지수
                "091160", "305720",  # 반도체, 2차전지
                "091170", "117680",  # 은행, 철강
                "266420", "266370",  # 헬스케어, IT
                "360750", "133690",  # 미국S&P500, 나스닥
            ]

            import time
            for code in priority_codes:
                etf_info = next((e for e in KR_SECTOR_ETFS if e.code == code), None)
                if etf_info:
                    data = self.get_etf_data(code)
                    if data:
                        related_stocks = SECTOR_STOCKS.get(etf_info.sector, [])
                        data["related_stocks"] = related_stocks
                        results.append(data)
                    time.sleep(0.3)  # Rate limit 방지

            # 나머지 ETF
            loaded_codes = {r["code"] for r in results}
            for etf in KR_SECTOR_ETFS:
                if etf.code not in loaded_codes:
                    data = self.get_etf_data(etf.code)
                    if data:
                        related_stocks = SECTOR_STOCKS.get(etf.sector, [])
                        data["related_stocks"] = related_stocks
                        results.append(data)
                    time.sleep(0.2)

            self._cache["all_sectors"] = results
            self._cache_time = datetime.now()
            logger.info(f"KR Market 데이터 로드 완료 ({len(results)}개 ETF)")

        except Exception as e:
            logger.error(f"백그라운드 데이터 로드 실패: {e}")
        finally:
            self._is_loading = False

    def get_all_sectors(self) -> List[Dict]:
        """모든 섹터 ETF 데이터 조회"""
        if "all_sectors" not in self._cache:
            self._init_with_defaults()

        # 캐시 만료 시 백그라운드 로드
        if not self._is_cache_valid() and not self._is_loading:
            thread = threading.Thread(target=self._load_real_data_background)
            thread.daemon = True
            thread.start()

        return self._cache.get("all_sectors", [])

    def get_sector_performance(self) -> Dict:
        """섹터 성과 요약"""
        sectors = self.get_all_sectors()

        # 로딩 중인 데이터 제외하고 정렬
        valid_sectors = [s for s in sectors if not s.get("is_loading", True)]
        sorted_sectors = sorted(valid_sectors, key=lambda x: x.get('change_percent', 0), reverse=True)

        return {
            "updated_at": datetime.now().isoformat(),
            "top_gainers": sorted_sectors[:5] if sorted_sectors else [],
            "top_losers": sorted_sectors[-5:][::-1] if len(sorted_sectors) > 5 else [],
            "all_sectors": sectors
        }

    def get_sectors_by_category(self) -> Dict:
        """카테고리별 섹터 분류"""
        sectors = self.get_all_sectors()

        categories = {
            "index": {"name": "지수", "etfs": []},
            "semiconductor": {"name": "반도체/2차전지", "etfs": []},
            "industry": {"name": "산업재", "etfs": []},
            "finance": {"name": "금융", "etfs": []},
            "consumer": {"name": "소비재/헬스케어", "etfs": []},
            "overseas": {"name": "해외", "etfs": []},
            "bond": {"name": "채권/원자재", "etfs": []},
        }

        sector_category_map = {
            "Index": "index",
            "Semiconductor": "semiconductor",
            "Battery": "semiconductor",
            "Auto": "industry",
            "Industrial": "industry",
            "Construction": "industry",
            "Materials": "industry",
            "Financial": "finance",
            "Healthcare": "consumer",
            "Consumer": "consumer",
            "Technology": "consumer",
            "Communication": "industry",
            "Utilities": "industry",
            "International": "overseas",
            "Bond": "bond",
            "Commodity": "bond",
        }

        for etf in sectors:
            sector = etf.get("sector", "")
            category = sector_category_map.get(sector, "industry")
            if category in categories:
                categories[category]["etfs"].append(etf)

        return {
            "updated_at": datetime.now().isoformat(),
            "categories": categories
        }


# 서비스 싱글톤
_kr_market_service: Optional[KRMarketService] = None


def get_kr_market_service() -> KRMarketService:
    """KR Market 서비스 싱글톤"""
    global _kr_market_service
    if _kr_market_service is None:
        _kr_market_service = KRMarketService()
    return _kr_market_service
