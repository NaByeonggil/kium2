"""
키움증권 REST API 트레이딩 클라이언트

Main Server용 - 매매 및 실시간 조회 전용
Sub Server의 kiwoom_client.py를 기반으로 트레이딩 기능 최적화
"""

import requests
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KiwoomTradingClient:
    """키움증권 REST API 트레이딩 클라이언트"""

    def __init__(self, appkey: str, secretkey: str, is_mock: bool = True):
        """
        초기화

        Args:
            appkey: App Key
            secretkey: Secret Key
            is_mock: True면 모의투자 환경
        """
        self.appkey = appkey
        self.secretkey = secretkey
        self.is_mock = is_mock

        # Base URL 설정
        if is_mock:
            self.base_url = "https://mockapi.kiwoom.com"
        else:
            self.base_url = "https://api.kiwoom.com"

        # 토큰 정보
        self.token = None
        self.token_expires = None

        # 종목 캐시
        self._stock_list_cache: List[Dict] = []
        self._market_cache: Dict[str, str] = {}

        # 초기 토큰 발급
        self._get_token()

    def _ensure_token(self):
        """토큰 확인 및 자동 갱신"""
        if not self.token or datetime.now() >= self.token_expires:
            logger.info("토큰 갱신 필요")
            self._get_token()

    def _get_token(self):
        """접근 토큰 발급"""
        url = f"{self.base_url}/oauth2/token"

        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }

        body = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "secretkey": self.secretkey
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('return_code') == 0:
                    self.token = data['token']
                    self.token_expires = datetime.now() + timedelta(hours=23)
                    logger.info(f"✅ 토큰 발급 성공 (만료: {self.token_expires})")
                else:
                    raise Exception(f"Token Error: {data.get('return_msg')}")
            else:
                raise Exception(f"HTTP Error: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 토큰 발급 실패: {e}")
            raise

    def _make_request(
        self,
        method: str,
        url: str,
        api_id: str,
        body: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 10
    ) -> Dict:
        """API 요청 공통 메서드"""
        self._ensure_token()

        headers = {
            "api-id": api_id,
            "authorization": f"Bearer {self.token}",
            "Content-Type": "application/json;charset=UTF-8"
        }

        full_url = f"{self.base_url}{url}"

        try:
            if method.upper() == "POST":
                response = requests.post(full_url, headers=headers, json=body, timeout=timeout)
            else:
                response = requests.get(full_url, headers=headers, params=params, timeout=timeout)

            return response.json()
        except requests.Timeout:
            logger.error(f"❌ API 요청 타임아웃: {api_id}")
            return {"return_code": -1, "return_msg": "Request timeout"}
        except Exception as e:
            logger.error(f"❌ API 요청 실패: {e}")
            return {"return_code": -1, "return_msg": str(e)}

    # ========== 호가 조회 (10호가) ==========

    def get_orderbook(self, stock_code: str, exchange: str = "KRX") -> Dict:
        """
        실시간 호가 조회 (10호가)

        Args:
            stock_code: 종목코드
            exchange: 거래소 (KRX)

        Returns:
            dict: 호가 데이터
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }

        result = self._make_request("POST", "/api/dostk/mrkcond", "ka10004", body)

        if result.get('return_code') == 0:
            def parse_price(val):
                """가격 문자열 파싱"""
                if not val:
                    return 0
                try:
                    return int(str(val).replace('+', '').replace('-', '').replace(',', ''))
                except:
                    return 0

            # 호가 데이터 파싱 - 응답 필드명에 맞춤
            # 매도호가: sel_1th~sel_10th (1th는 sel_fpr), 매수호가: buy_1th~buy_10th (1th는 buy_fpr)
            asks = []
            bids = []

            # 매도 1호가 (최우선)
            asks.append({
                "price": parse_price(result.get('sel_fpr_bid', 0)),
                "volume": parse_price(result.get('sel_fpr_req', 0))
            })
            # 매도 2~10호가
            for i in range(2, 11):
                suffix = f'{i}th' if i != 3 else '3th'
                asks.append({
                    "price": parse_price(result.get(f'sel_{suffix}_pre_bid', 0)),
                    "volume": parse_price(result.get(f'sel_{suffix}_pre_req', 0))
                })

            # 매수 1호가 (최우선)
            bids.append({
                "price": parse_price(result.get('buy_fpr_bid', 0)),
                "volume": parse_price(result.get('buy_fpr_req', 0))
            })
            # 매수 2~10호가
            for i in range(2, 11):
                suffix = f'{i}th' if i != 3 else '3th'
                bids.append({
                    "price": parse_price(result.get(f'buy_{suffix}_pre_bid', 0)),
                    "volume": parse_price(result.get(f'buy_{suffix}_pre_req', 0))
                })

            return {
                "success": True,
                "stock_code": stock_code,
                "stock_name": "",
                "current_price": 0,
                "asks": asks,
                "bids": bids,
                "total_ask_volume": parse_price(result.get('tot_sel_req', 0)),
                "total_bid_volume": parse_price(result.get('tot_buy_req', 0)),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.get('return_msg', 'Unknown error')
            }

    # ========== 현재가 조회 ==========

    def get_current_price(self, stock_code: str, exchange: str = "KRX") -> Dict:
        """현재가 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }

        result = self._make_request("POST", "/api/dostk/stkinfo", "ka10001", body)

        if result.get('return_code') == 0:
            # 응답 데이터가 최상위에 직접 있음
            def parse_price(val):
                """가격 문자열 파싱 (+/-부호 포함)"""
                if not val:
                    return 0
                try:
                    return int(str(val).replace('+', '').replace(',', ''))
                except:
                    return 0

            return {
                "success": True,
                "stock_code": stock_code,
                "stock_name": result.get('stk_nm', ''),
                "current_price": parse_price(result.get('cur_prc', 0)),
                "change_price": parse_price(result.get('pred_pre', 0)),
                "change_rate": float(str(result.get('flu_rt', 0) or 0).replace('+', '')),
                "volume": parse_price(result.get('trde_qty', 0)),
                "trading_value": 0,  # 별도 필드 없음
                "high_price": parse_price(result.get('high_pric', 0)),
                "low_price": parse_price(result.get('low_pric', 0)),
                "open_price": parse_price(result.get('open_pric', 0)),
                "prev_close": parse_price(result.get('base_pric', 0)),
            }
        else:
            return {
                "success": False,
                "error": result.get('return_msg', 'Unknown error')
            }

    # ========== 매매 주문 ==========

    def buy(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "0",
        exchange: str = "KRX"
    ) -> Dict:
        """
        매수 주문

        Args:
            stock_code: 종목코드
            quantity: 주문수량
            price: 주문가격 (0이면 시장가)
            order_type: 매매구분 (0:지정가, 3:시장가)
            exchange: 거래소

        Returns:
            dict: 주문 결과
        """
        # 시장가 주문 처리
        if price == 0:
            order_type = "3"

        body = {
            "dmst_stex_tp": exchange,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": order_type,
            "cond_uv": ""
        }

        result = self._make_request("POST", "/api/dostk/ordr", "kt10000", body)

        if result.get('return_code') == 0:
            return {
                "success": True,
                "order_no": result.get('output', {}).get('ord_no', ''),
                "message": "매수 주문이 접수되었습니다",
                "stock_code": stock_code,
                "side": "buy",
                "quantity": quantity,
                "price": price if price > 0 else None
            }
        else:
            return {
                "success": False,
                "order_no": None,
                "message": result.get('return_msg', '주문 실패'),
                "stock_code": stock_code,
                "side": "buy",
                "quantity": quantity,
                "price": price if price > 0 else None
            }

    def sell(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "0",
        exchange: str = "KRX"
    ) -> Dict:
        """매도 주문"""
        if price == 0:
            order_type = "3"

        body = {
            "dmst_stex_tp": exchange,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": order_type,
            "cond_uv": ""
        }

        result = self._make_request("POST", "/api/dostk/ordr", "kt10001", body)

        if result.get('return_code') == 0:
            return {
                "success": True,
                "order_no": result.get('output', {}).get('ord_no', ''),
                "message": "매도 주문이 접수되었습니다",
                "stock_code": stock_code,
                "side": "sell",
                "quantity": quantity,
                "price": price if price > 0 else None
            }
        else:
            return {
                "success": False,
                "order_no": None,
                "message": result.get('return_msg', '주문 실패'),
                "stock_code": stock_code,
                "side": "sell",
                "quantity": quantity,
                "price": price if price > 0 else None
            }

    def modify_order(
        self,
        order_no: str,
        stock_code: str,
        quantity: int,
        price: int,
        order_type: str = "0",
        exchange: str = "KRX"
    ) -> Dict:
        """주문 정정"""
        body = {
            "dmst_stex_tp": exchange,
            "org_ord_no": order_no,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price),
            "trde_tp": order_type
        }

        result = self._make_request("POST", "/api/dostk/ordr", "kt10002", body)

        if result.get('return_code') == 0:
            return {
                "success": True,
                "order_no": result.get('output', {}).get('ord_no', ''),
                "message": "주문이 정정되었습니다"
            }
        else:
            return {
                "success": False,
                "order_no": None,
                "message": result.get('return_msg', '정정 실패')
            }

    def cancel_order(
        self,
        order_no: str,
        stock_code: str,
        quantity: int,
        exchange: str = "KRX"
    ) -> Dict:
        """주문 취소"""
        body = {
            "dmst_stex_tp": exchange,
            "org_ord_no": order_no,
            "stk_cd": stock_code,
            "ord_qty": str(quantity)
        }

        result = self._make_request("POST", "/api/dostk/ordr", "kt10003", body)

        if result.get('return_code') == 0:
            return {
                "success": True,
                "message": "주문이 취소되었습니다"
            }
        else:
            return {
                "success": False,
                "message": result.get('return_msg', '취소 실패')
            }

    # ========== 계좌 조회 ==========

    def get_balance(self, exchange: str = "KRX") -> Dict:
        """
        계좌 잔고 조회

        Returns:
            dict: 계좌 잔고 정보
        """
        body = {
            "qry_tp": "1",
            "dmst_stex_tp": exchange
        }

        result = self._make_request("POST", "/api/dostk/acnt", "kt00018", body)

        if result.get('return_code') == 0:
            # 응답 데이터가 최상위에 직접 있음
            def parse_amount(val):
                """금액 문자열 파싱"""
                if not val:
                    return 0
                try:
                    return int(str(val).replace(',', '').lstrip('0') or '0')
                except:
                    return 0

            # 보유 종목 파싱 (acnt_evlt_remn_indv_tot 배열)
            holdings = []
            holdings_list = result.get('acnt_evlt_remn_indv_tot', [])
            for item in holdings_list:
                holding = {
                    "stock_code": item.get('stk_cd', ''),
                    "stock_name": item.get('stk_nm', ''),
                    "quantity": parse_amount(item.get('hld_qty', 0)),
                    "avg_price": parse_amount(item.get('buy_avg_pric', 0)),
                    "current_price": parse_amount(item.get('cur_pric', 0)),
                    "eval_amount": parse_amount(item.get('evlt_amt', 0)),
                    "profit_loss": parse_amount(item.get('evlt_pl', 0)),
                    "profit_rate": float(str(item.get('prft_rt', 0) or 0).replace('+', '').replace('-', '')),
                }
                if holding["stock_code"]:
                    holdings.append(holding)

            return {
                "success": True,
                "total_eval": parse_amount(result.get('tot_evlt_amt', 0)),
                "total_profit_loss": parse_amount(result.get('tot_evlt_pl', 0)),
                "total_profit_rate": float(str(result.get('tot_prft_rt', 0) or 0).replace('+', '')),
                "cash_balance": parse_amount(result.get('prsm_dpst_aset_amt', 0)),
                "holdings": holdings
            }
        else:
            return {
                "success": False,
                "error": result.get('return_msg', 'Unknown error')
            }

    def get_open_orders(self, stock_code: str = "", exchange: str = "KRX") -> Dict:
        """미체결 주문 조회"""
        # stock_code가 빈 문자열이면 전체 미체결 조회
        body = {
            "dmst_stex_tp": exchange,
            "stex_tp": "01",     # 거래소구분: 01-한국거래소
            "all_stk_tp": "0",   # 0: 전체, 1: 특정종목
            "trde_tp": "0",      # 0: 전체, 1: 매도, 2: 매수
            "ccls_tp": "0",      # 0: 전체, 1: 체결, 2: 미체결
            "inqr_sqno": "0",    # 조회순번
            "cnt": "50"          # 조회건수
        }
        # stock_code가 있으면 해당 종목만 조회
        if stock_code and stock_code.strip():
            body["stk_cd"] = stock_code.strip()
            body["all_stk_tp"] = "1"

        result = self._make_request("POST", "/api/dostk/acnt", "ka10075", body)

        if result.get('return_code') == 0:
            output_list = result.get('output', [])

            orders = []
            for item in output_list:
                order = {
                    "order_no": item.get('ord_no', ''),
                    "stock_code": item.get('stk_cd', ''),
                    "stock_name": item.get('stk_nm', ''),
                    "side": "buy" if item.get('sll_buy_tp') == "2" else "sell",
                    "order_type": "limit" if item.get('ord_tp') == "0" else "market",
                    "order_price": int(item.get('ord_uv', 0) or 0),
                    "order_quantity": int(item.get('ord_qty', 0) or 0),
                    "filled_quantity": int(item.get('ccls_qty', 0) or 0),
                    "remaining_quantity": int(item.get('rmn_qty', 0) or 0),
                    "order_time": item.get('ord_tm', ''),
                }
                if order["order_no"]:
                    orders.append(order)

            return {
                "success": True,
                "orders": orders
            }
        else:
            return {
                "success": False,
                "error": result.get('return_msg', 'Unknown error'),
                "orders": []
            }

    # ========== 차트 데이터 ==========

    def get_daily_chart(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        exchange: str = "KRX"
    ) -> Dict:
        """일봉 차트 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange,
            "base_dt": end_date,
            "upd_stkpc_tp": "0",  # 수정주가
            "cnt": "100"
        }

        result = self._make_request("POST", "/api/dostk/chart", "ka10081", body)

        if result.get('return_code') == 0:
            def parse_price(val):
                if not val:
                    return 0
                try:
                    return int(str(val).replace('+', '').replace('-', '').replace(',', ''))
                except:
                    return 0

            # stk_dt_pole_chart_qry 배열에서 데이터 추출
            output_list = result.get('stk_dt_pole_chart_qry', []) or []

            candles = []
            for item in output_list:
                dt = item.get('dt', '')
                # 날짜 형식 변환 YYYYMMDD -> YYYY-MM-DD
                if len(dt) == 8:
                    dt = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}"

                candle = {
                    "time": dt,
                    "open": parse_price(item.get('open_pric', 0)),
                    "high": parse_price(item.get('high_pric', 0)),
                    "low": parse_price(item.get('low_pric', 0)),
                    "close": parse_price(item.get('cur_prc', 0)),
                    "volume": parse_price(item.get('trde_qty', 0)),
                }
                candles.append(candle)

            # 날짜 역순 정렬 (오래된 순)
            candles.reverse()

            return {
                "success": True,
                "stock_code": stock_code,
                "candles": candles,
                "chart_type": "daily"
            }
        else:
            return {
                "success": False,
                "error": result.get('return_msg', 'Unknown error')
            }

    def get_minute_chart(
        self,
        stock_code: str,
        date: str,
        time_type: str = "1",
        exchange: str = "KRX"
    ) -> Dict:
        """분봉 차트 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange,
            "base_dt": date,
            "base_tm": "153000",  # 장 마감 시간
            "upd_stkpc_tp": "0",
            "tic_scope": time_type,  # 분봉 간격
            "cnt": "200"
        }

        result = self._make_request("POST", "/api/dostk/chart", "ka10080", body)

        if result.get('return_code') == 0:
            def parse_price(val):
                if not val:
                    return 0
                try:
                    return int(str(val).replace('+', '').replace('-', '').replace(',', ''))
                except:
                    return 0

            # stk_min_pole_chart_qry 배열에서 데이터 추출
            output_list = result.get('stk_min_pole_chart_qry', []) or []

            candles = []
            for item in output_list:
                # cntr_tm: 20251126103300 형식
                cntr_tm = item.get('cntr_tm', '')
                if len(cntr_tm) >= 12:
                    time_str = f"{cntr_tm[:4]}-{cntr_tm[4:6]}-{cntr_tm[6:8]} {cntr_tm[8:10]}:{cntr_tm[10:12]}"
                else:
                    time_str = cntr_tm

                candle = {
                    "time": time_str,
                    "open": parse_price(item.get('open_pric', 0)),
                    "high": parse_price(item.get('high_pric', 0)),
                    "low": parse_price(item.get('low_pric', 0)),
                    "close": parse_price(item.get('cur_prc', 0)),
                    "volume": parse_price(item.get('trde_qty', 0)),
                }
                candles.append(candle)

            # 시간 역순 정렬 (오래된 순)
            candles.reverse()

            return {
                "success": True,
                "stock_code": stock_code,
                "candles": candles,
                "chart_type": f"minute_{time_type}"
            }
        else:
            return {
                "success": False,
                "error": result.get('return_msg', 'Unknown error')
            }

    # ========== 종목 검색 ==========

    def get_stock_list(self, market_type: str = "0") -> Dict:
        """종목 리스트 조회"""
        body = {
            "mrkt_tp": market_type
        }

        return self._make_request("POST", "/api/dostk/stkinfo", "ka10099", body)

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """종목 검색"""
        if not self._stock_list_cache:
            self._load_stock_list_cache()

        if not self._stock_list_cache:
            return []

        keyword_upper = keyword.upper()
        results = []

        for stock in self._stock_list_cache:
            code = stock.get('stock_code', '')
            name = stock.get('stock_name', '')

            if keyword in code or keyword in name or keyword_upper in name.upper():
                results.append(stock)

            if len(results) >= limit:
                break

        return results

    def _load_stock_list_cache(self):
        """전체 종목 리스트 캐시 로드"""
        self._stock_list_cache = []

        try:
            # 코스피
            kospi_result = self.get_stock_list("1")
            if kospi_result.get('return_code') == 0:
                stock_list = kospi_result.get('list') or kospi_result.get('output') or []
                if stock_list:
                    for item in stock_list:
                        code = item.get('stk_cd', '')
                        name = item.get('stk_nm', '')
                        if code and name:
                            self._stock_list_cache.append({
                                'stock_code': code,
                                'stock_name': name,
                                'market_type': 'KOSPI'
                            })
                            self._market_cache[code] = 'KOSPI'

            # 코스닥
            kosdaq_result = self.get_stock_list("2")
            if kosdaq_result.get('return_code') == 0:
                stock_list = kosdaq_result.get('list') or kosdaq_result.get('output') or []
                if stock_list:
                    for item in stock_list:
                        code = item.get('stk_cd', '')
                        name = item.get('stk_nm', '')
                        if code and name:
                            self._stock_list_cache.append({
                                'stock_code': code,
                                'stock_name': name,
                                'market_type': 'KOSDAQ'
                            })
                            self._market_cache[code] = 'KOSDAQ'

            # ETF
            etf_result = self.get_stock_list("3")
            if etf_result.get('return_code') == 0:
                stock_list = etf_result.get('list') or etf_result.get('output') or []
                if stock_list:
                    for item in stock_list:
                        code = item.get('stk_cd', '')
                        name = item.get('stk_nm', '')
                        if code and name:
                            self._stock_list_cache.append({
                                'stock_code': code,
                                'stock_name': name,
                                'market_type': 'ETF'
                            })
                            self._market_cache[code] = 'ETF'

            logger.info(f"📊 종목 캐시 로드 완료: {len(self._stock_list_cache)}개")

        except Exception as e:
            logger.warning(f"⚠️ 종목 리스트 캐시 로드 실패: {e}")

        # API에서 데이터를 가져오지 못한 경우 기본 종목 데이터 사용
        if not self._stock_list_cache:
            logger.info("📊 기본 종목 데이터 사용")
            self._load_default_stocks()

    def _load_default_stocks(self):
        """기본 종목 데이터 로드 (API 실패 시 사용)"""
        default_stocks = [
            # 코스피 대형주
            {"stock_code": "005930", "stock_name": "삼성전자", "market_type": "KOSPI"},
            {"stock_code": "000660", "stock_name": "SK하이닉스", "market_type": "KOSPI"},
            {"stock_code": "005380", "stock_name": "현대차", "market_type": "KOSPI"},
            {"stock_code": "000270", "stock_name": "기아", "market_type": "KOSPI"},
            {"stock_code": "005490", "stock_name": "POSCO홀딩스", "market_type": "KOSPI"},
            {"stock_code": "035420", "stock_name": "NAVER", "market_type": "KOSPI"},
            {"stock_code": "035720", "stock_name": "카카오", "market_type": "KOSPI"},
            {"stock_code": "051910", "stock_name": "LG화학", "market_type": "KOSPI"},
            {"stock_code": "006400", "stock_name": "삼성SDI", "market_type": "KOSPI"},
            {"stock_code": "003670", "stock_name": "포스코퓨처엠", "market_type": "KOSPI"},
            {"stock_code": "105560", "stock_name": "KB금융", "market_type": "KOSPI"},
            {"stock_code": "055550", "stock_name": "신한지주", "market_type": "KOSPI"},
            {"stock_code": "086790", "stock_name": "하나금융지주", "market_type": "KOSPI"},
            {"stock_code": "096770", "stock_name": "SK이노베이션", "market_type": "KOSPI"},
            {"stock_code": "010950", "stock_name": "S-Oil", "market_type": "KOSPI"},
            {"stock_code": "034730", "stock_name": "SK", "market_type": "KOSPI"},
            {"stock_code": "003550", "stock_name": "LG", "market_type": "KOSPI"},
            {"stock_code": "066570", "stock_name": "LG전자", "market_type": "KOSPI"},
            {"stock_code": "032830", "stock_name": "삼성생명", "market_type": "KOSPI"},
            {"stock_code": "015760", "stock_name": "한국전력", "market_type": "KOSPI"},
            {"stock_code": "207940", "stock_name": "삼성바이오로직스", "market_type": "KOSPI"},
            {"stock_code": "068270", "stock_name": "셀트리온", "market_type": "KOSPI"},
            {"stock_code": "012330", "stock_name": "현대모비스", "market_type": "KOSPI"},
            {"stock_code": "028260", "stock_name": "삼성물산", "market_type": "KOSPI"},
            {"stock_code": "017670", "stock_name": "SK텔레콤", "market_type": "KOSPI"},
            {"stock_code": "030200", "stock_name": "KT", "market_type": "KOSPI"},
            {"stock_code": "009150", "stock_name": "삼성전기", "market_type": "KOSPI"},
            {"stock_code": "000810", "stock_name": "삼성화재", "market_type": "KOSPI"},
            {"stock_code": "316140", "stock_name": "우리금융지주", "market_type": "KOSPI"},
            {"stock_code": "033780", "stock_name": "KT&G", "market_type": "KOSPI"},
            {"stock_code": "018260", "stock_name": "삼성에스디에스", "market_type": "KOSPI"},
            {"stock_code": "011200", "stock_name": "HMM", "market_type": "KOSPI"},
            {"stock_code": "329180", "stock_name": "HD현대중공업", "market_type": "KOSPI"},
            {"stock_code": "009540", "stock_name": "HD한국조선해양", "market_type": "KOSPI"},
            {"stock_code": "042700", "stock_name": "한미반도체", "market_type": "KOSPI"},
            # 코스닥
            {"stock_code": "247540", "stock_name": "에코프로비엠", "market_type": "KOSDAQ"},
            {"stock_code": "086520", "stock_name": "에코프로", "market_type": "KOSDAQ"},
            {"stock_code": "091990", "stock_name": "셀트리온헬스케어", "market_type": "KOSDAQ"},
            {"stock_code": "328130", "stock_name": "루닛", "market_type": "KOSDAQ"},
            {"stock_code": "293490", "stock_name": "카카오게임즈", "market_type": "KOSDAQ"},
            {"stock_code": "263750", "stock_name": "펄어비스", "market_type": "KOSDAQ"},
            {"stock_code": "036570", "stock_name": "엔씨소프트", "market_type": "KOSDAQ"},
            {"stock_code": "112040", "stock_name": "위메이드", "market_type": "KOSDAQ"},
            {"stock_code": "041510", "stock_name": "에스엠", "market_type": "KOSDAQ"},
            {"stock_code": "352820", "stock_name": "하이브", "market_type": "KOSDAQ"},
            {"stock_code": "122870", "stock_name": "와이지엔터테인먼트", "market_type": "KOSDAQ"},
            {"stock_code": "095340", "stock_name": "ISC", "market_type": "KOSDAQ"},
            {"stock_code": "357780", "stock_name": "솔브레인", "market_type": "KOSDAQ"},
            {"stock_code": "196170", "stock_name": "알테오젠", "market_type": "KOSDAQ"},
            {"stock_code": "145020", "stock_name": "휴젤", "market_type": "KOSDAQ"},
            {"stock_code": "060250", "stock_name": "NHN KCP", "market_type": "KOSDAQ"},
            {"stock_code": "181710", "stock_name": "NHN", "market_type": "KOSDAQ"},
            {"stock_code": "035760", "stock_name": "CJ ENM", "market_type": "KOSDAQ"},
            {"stock_code": "067160", "stock_name": "아프리카TV", "market_type": "KOSDAQ"},
            {"stock_code": "039030", "stock_name": "이오테크닉스", "market_type": "KOSDAQ"},
            {"stock_code": "403870", "stock_name": "HPSP", "market_type": "KOSDAQ"},
            {"stock_code": "078930", "stock_name": "GS", "market_type": "KOSPI"},
            {"stock_code": "036460", "stock_name": "한국가스공사", "market_type": "KOSPI"},
            {"stock_code": "032640", "stock_name": "LG유플러스", "market_type": "KOSPI"},
            {"stock_code": "010130", "stock_name": "고려아연", "market_type": "KOSPI"},
            {"stock_code": "000880", "stock_name": "한화", "market_type": "KOSPI"},
            {"stock_code": "009830", "stock_name": "한화솔루션", "market_type": "KOSPI"},
            {"stock_code": "010620", "stock_name": "현대미포조선", "market_type": "KOSPI"},
            {"stock_code": "267250", "stock_name": "HD현대", "market_type": "KOSPI"},
            {"stock_code": "034020", "stock_name": "두산에너빌리티", "market_type": "KOSPI"},
            {"stock_code": "047050", "stock_name": "포스코인터내셔널", "market_type": "KOSPI"},
            {"stock_code": "326030", "stock_name": "SK바이오팜", "market_type": "KOSPI"},
            {"stock_code": "128940", "stock_name": "한미약품", "market_type": "KOSPI"},
            {"stock_code": "097950", "stock_name": "CJ제일제당", "market_type": "KOSPI"},
            {"stock_code": "271560", "stock_name": "오리온", "market_type": "KOSPI"},
            {"stock_code": "051900", "stock_name": "LG생활건강", "market_type": "KOSPI"},
            {"stock_code": "023530", "stock_name": "롯데쇼핑", "market_type": "KOSPI"},
            # ETF
            {"stock_code": "069500", "stock_name": "KODEX 200", "market_type": "ETF"},
            {"stock_code": "229200", "stock_name": "KODEX 코스닥150", "market_type": "ETF"},
            {"stock_code": "102110", "stock_name": "TIGER 200", "market_type": "ETF"},
            {"stock_code": "252670", "stock_name": "KODEX 200선물인버스2X", "market_type": "ETF"},
            {"stock_code": "122630", "stock_name": "KODEX 레버리지", "market_type": "ETF"},
            {"stock_code": "233740", "stock_name": "KODEX 코스닥150레버리지", "market_type": "ETF"},
            {"stock_code": "114800", "stock_name": "KODEX 인버스", "market_type": "ETF"},
            {"stock_code": "091160", "stock_name": "KODEX 반도체", "market_type": "ETF"},
            {"stock_code": "091170", "stock_name": "KODEX 은행", "market_type": "ETF"},
            {"stock_code": "305720", "stock_name": "KODEX 2차전지산업", "market_type": "ETF"},
            {"stock_code": "364980", "stock_name": "KODEX Fn반도체TOP10", "market_type": "ETF"},
            {"stock_code": "381180", "stock_name": "TIGER 미국테크TOP10 INDXX", "market_type": "ETF"},
            {"stock_code": "133690", "stock_name": "TIGER 미국나스닥100", "market_type": "ETF"},
            {"stock_code": "360750", "stock_name": "TIGER 미국S&P500", "market_type": "ETF"},
            {"stock_code": "379800", "stock_name": "KODEX 미국S&P500TR", "market_type": "ETF"},
        ]

        self._stock_list_cache = default_stocks
        for stock in default_stocks:
            self._market_cache[stock["stock_code"]] = stock["market_type"]

        logger.info(f"📊 기본 종목 {len(default_stocks)}개 로드 완료")

    def get_market_type(self, stock_code: str) -> str:
        """종목의 시장 구분 조회"""
        if not self._market_cache:
            self._load_stock_list_cache()
        return self._market_cache.get(stock_code, "KRX")

    # ========== 거래대금 랭킹 ==========

    def get_top_trading_value(
        self,
        market_type: str = "0",
        limit: int = 50
    ) -> List[Dict]:
        """거래대금 상위 종목 조회"""
        body = {
            "mrkt_tp": market_type,
            "sort_tp": "1",
            "tgt_tp": "1"
        }

        result = self._make_request("POST", "/api/dostk/rank", "ka10032", body)

        if result.get('return_code') == 0:
            output_list = result.get('output', [])
            return output_list[:limit]
        else:
            return []
