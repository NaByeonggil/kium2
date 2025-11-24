"""
키움증권 REST API 클라이언트

Official API Documentation: https://openapi.kiwoom.com
"""

import requests
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class KiwoomAPIClient:
    """키움증권 REST API 클라이언트"""

    def __init__(self, appkey: str, secretkey: str, is_mock: bool = False):
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
            response = requests.post(url, headers=headers, json=body)

            if response.status_code == 200:
                data = response.json()
                if data.get('return_code') == 0:
                    self.token = data['token']
                    # 만료 시간 설정 (24시간 - 1시간 여유)
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
        params: Optional[Dict] = None
    ) -> Dict:
        """
        API 요청 공통 메서드

        Args:
            method: HTTP 메서드 (GET, POST)
            url: API 엔드포인트
            api_id: API ID
            body: Request Body
            params: Query Parameters

        Returns:
            dict: API 응답
        """
        self._ensure_token()

        headers = {
            "api-id": api_id,
            "authorization": f"Bearer {self.token}",
            "Content-Type": "application/json;charset=UTF-8"
        }

        full_url = f"{self.base_url}{url}"

        try:
            if method.upper() == "POST":
                response = requests.post(full_url, headers=headers, json=body)
            else:
                response = requests.get(full_url, headers=headers, params=params)

            return response.json()
        except Exception as e:
            logger.error(f"❌ API 요청 실패: {e}")
            raise

    # ========== 계좌 정보 ==========

    def get_balance(self, qry_tp: str = "1", exchange: str = "KRX") -> Dict:
        """
        계좌 평가 잔고 조회

        Args:
            qry_tp: 조회구분 (1:합산, 2:개별)
            exchange: 거래소 (KRX, NXT)

        Returns:
            dict: 계좌 잔고 정보
        """
        body = {
            "qry_tp": qry_tp,
            "dmst_stex_tp": exchange
        }

        return self._make_request("POST", "/api/dostk/acnt", "kt00018", body)

    def get_open_orders(self, stock_code: str = "", exchange: str = "KRX") -> Dict:
        """
        미체결 주문 조회

        Args:
            stock_code: 종목코드 (빈값이면 전체)
            exchange: 거래소
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }

        return self._make_request("POST", "/api/dostk/acnt", "ka10075", body)

    def get_executed_orders(self, stock_code: str = "", exchange: str = "KRX") -> Dict:
        """체결 주문 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }

        return self._make_request("POST", "/api/dostk/acnt", "ka10076", body)

    # ========== 주문 ==========

    def buy(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "3",
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
            dict: 주문 결과 (ord_no 포함)
        """
        body = {
            "dmst_stex_tp": exchange,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": order_type,
            "cond_uv": ""
        }

        return self._make_request("POST", "/api/dostk/ordr", "kt10000", body)

    def sell(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "3",
        exchange: str = "KRX"
    ) -> Dict:
        """매도 주문"""
        body = {
            "dmst_stex_tp": exchange,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": order_type,
            "cond_uv": ""
        }

        return self._make_request("POST", "/api/dostk/ordr", "kt10001", body)

    def modify_order(
        self,
        org_order_no: str,
        stock_code: str,
        quantity: int,
        price: int,
        order_type: str = "0",
        exchange: str = "KRX"
    ) -> Dict:
        """주문 정정"""
        body = {
            "dmst_stex_tp": exchange,
            "org_ord_no": org_order_no,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price),
            "trde_tp": order_type
        }

        return self._make_request("POST", "/api/dostk/ordr", "kt10002", body)

    def cancel_order(
        self,
        org_order_no: str,
        stock_code: str,
        quantity: int,
        exchange: str = "KRX"
    ) -> Dict:
        """주문 취소"""
        body = {
            "dmst_stex_tp": exchange,
            "org_ord_no": org_order_no,
            "stk_cd": stock_code,
            "ord_qty": str(quantity)
        }

        return self._make_request("POST", "/api/dostk/ordr", "kt10003", body)

    # ========== 시세 정보 ==========

    def get_current_price(self, stock_code: str, exchange: str = "KRX") -> Dict:
        """현재가 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }

        return self._make_request("POST", "/api/dostk/stkinfo", "ka10001", body)

    def get_orderbook(self, stock_code: str, exchange: str = "KRX") -> Dict:
        """호가 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }

        return self._make_request("POST", "/api/dostk/mrkcond", "ka10004", body)

    # ========== 차트 데이터 ==========

    def get_daily_chart(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        exchange: str = "KRX"
    ) -> Dict:
        """
        일봉 차트 조회

        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            exchange: 거래소
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange,
            "inqr_strt_dt": start_date,
            "inqr_end_dt": end_date
        }

        return self._make_request("POST", "/api/dostk/chart", "ka10081", body)

    def get_minute_chart(
        self,
        stock_code: str,
        date: str,
        time_type: str = "1",
        exchange: str = "KRX"
    ) -> Dict:
        """
        분봉 차트 조회

        Args:
            stock_code: 종목코드
            date: 조회일 (YYYYMMDD)
            time_type: 시간구분 (1:1분, 3:3분, 5:5분, 10:10분, 30:30분, 60:60분)
            exchange: 거래소
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange,
            "time_tp": time_type,
            "inqr_strt_dt": date,
            "inqr_end_dt": date
        }

        return self._make_request("POST", "/api/dostk/chart", "ka10080", body)

    # ========== 종목 정보 ==========

    def get_stock_list(self, market_type: str = "0") -> Dict:
        """
        종목 리스트 조회

        Args:
            market_type: 시장구분
                - "0": 전체
                - "1": 코스피
                - "2": 코스닥
                - "3": ETF
                - "4": ETN
        """
        body = {
            "mrkt_tp": market_type
        }

        return self._make_request("POST", "/api/dostk/stkinfo", "ka10099", body)

    # ========== 순위/랭킹 정보 ==========

    def get_top_trading_value(
        self,
        market_type: str = "0",
        sort_type: str = "1",
        target_type: str = "0",
        limit: int = 50
    ) -> List[Dict]:
        """
        거래대금 상위 종목 조회 (ka10032)

        Args:
            market_type: 시장구분
                - "0": 전체
                - "1": 코스피
                - "2": 코스닥
            sort_type: 정렬구분
                - "1": 거래대금 순
                - "2": 거래량 순
            target_type: 대상구분
                - "0": 전체
                - "1": 관리종목 제외
            limit: 조회할 종목 수 (기본: 50)

        Returns:
            list: 상위 종목 리스트
                [
                    {
                        "stk_cd": "005930",  # 종목코드
                        "stk_nm": "삼성전자",  # 종목명
                        "cur_pr": "75000",  # 현재가
                        "chg_rt": "1.35",  # 등락율
                        "trde_val": "500000000000",  # 거래대금
                        "trde_vol": "10000000",  # 거래량
                    },
                    ...
                ]
        """
        body = {
            "mrkt_tp": market_type,
            "sort_tp": sort_type,
            "tgt_tp": target_type
        }

        result = self._make_request("POST", "/api/dostk/rank", "ka10032", body)

        # output에서 상위 N개만 추출
        if result.get('return_code') == 0:
            output_list = result.get('output', [])
            return output_list[:limit]
        else:
            logger.warning(f"⚠️ 거래대금 조회 실패: {result.get('return_msg')}")
            return []

    def get_top_volume_increase(
        self,
        market_type: str = "0",
        limit: int = 50
    ) -> List[Dict]:
        """
        거래량 급증 종목 조회 (ka10023)

        Args:
            market_type: 시장구분 (0:전체, 1:코스피, 2:코스닥)
            limit: 조회할 종목 수

        Returns:
            list: 거래량 급증 종목 리스트
        """
        body = {
            "mrkt_tp": market_type
        }

        result = self._make_request("POST", "/api/dostk/rank", "ka10023", body)

        if result.get('return_code') == 0:
            output_list = result.get('output', [])
            return output_list[:limit]
        else:
            logger.warning(f"⚠️ 거래량 급증 조회 실패: {result.get('return_msg')}")
            return []
