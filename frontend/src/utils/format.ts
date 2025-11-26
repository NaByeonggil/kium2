// 숫자 포맷팅

// 가격 포맷 (천 단위 콤마)
export function formatPrice(price: number): string {
  return price.toLocaleString('ko-KR');
}

// 거래량 포맷 (억/만 단위)
export function formatVolume(volume: number): string {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(1)}억`;
  }
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(0)}만`;
  }
  return volume.toLocaleString('ko-KR');
}

// 거래대금 포맷 (조/억 단위)
export function formatTradingValue(value: number): string {
  if (value >= 1000000000000) {
    return `${(value / 1000000000000).toFixed(2)}조`;
  }
  if (value >= 100000000) {
    return `${(value / 100000000).toFixed(0)}억`;
  }
  return value.toLocaleString('ko-KR');
}

// 등락률 포맷
export function formatChangeRate(rate: number): string {
  const sign = rate > 0 ? '+' : '';
  return `${sign}${rate.toFixed(2)}%`;
}

// 등락 가격 포맷
export function formatChangePrice(price: number): string {
  const sign = price > 0 ? '+' : '';
  return `${sign}${formatPrice(price)}`;
}

// 수익률 클래스
export function getPriceColorClass(value: number): string {
  if (value > 0) return 'text-up';
  if (value < 0) return 'text-down';
  return 'text-dark-muted';
}

// 날짜 포맷
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ko-KR');
}

// 시간 포맷
export function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
}

// 퍼센트 바 너비 계산
export function calculateBarWidth(volume: number, maxVolume: number): number {
  if (maxVolume === 0) return 0;
  return Math.min((volume / maxVolume) * 100, 100);
}
