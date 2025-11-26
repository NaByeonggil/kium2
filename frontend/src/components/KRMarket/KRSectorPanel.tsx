import { useEffect, useState } from 'react';
import { krMarketApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import { getPriceColorClass, formatPrice } from '@/utils/format';
import { TrendingUp, ChevronRight, RefreshCw } from 'lucide-react';
import type { KRETFData, KRSectorPerformance } from '@/types';

export default function KRSectorPanel() {
  const [performance, setPerformance] = useState<KRSectorPerformance | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedETF, setSelectedETF] = useState<KRETFData | null>(null);
  const { setSelectedStock } = useTradingStore();

  // 섹터 데이터 로드
  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await krMarketApi.getPerformance();
      setPerformance(data);
    } catch (error) {
      console.error('KR Market load error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // 1분마다 갱신
    const interval = setInterval(loadData, 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // ETF 클릭 시 해당 ETF 선택
  const handleETFClick = (etf: KRETFData) => {
    setSelectedStock({
      stock_code: etf.code,
      stock_name: etf.name,
      market_type: 'ETF',
    });
  };

  // 관련 종목 클릭
  const handleRelatedStockClick = (stock: { code: string; name: string }) => {
    setSelectedStock({
      stock_code: stock.code,
      stock_name: stock.name,
      market_type: 'KRX',
    });
  };

  // 모든 섹터를 등락률 순으로 정렬 (로딩중인 데이터 제외)
  const getAllSectors = (): KRETFData[] => {
    if (!performance) return [];
    const allSectors = performance.all_sectors.filter(s => !s.is_loading);
    return allSectors.sort((a, b) => b.change_percent - a.change_percent);
  };

  if (isLoading && !performance) {
    return (
      <div className="card p-4 h-full flex items-center justify-center text-dark-muted">
        로딩중...
      </div>
    );
  }

  const allSectors = getAllSectors();

  return (
    <div className="card p-4 h-full flex flex-col">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-dark-muted" />
          <span className="font-semibold">KR ETF 섹터</span>
          <span className="text-xs text-dark-muted">({allSectors.length})</span>
        </div>
        <div className="flex items-center gap-2">
          {performance && (
            <span className="text-xs text-dark-muted">
              {new Date(performance.updated_at).toLocaleTimeString('ko-KR')}
            </span>
          )}
          <button
            onClick={loadData}
            disabled={isLoading}
            className="p-1 hover:bg-dark-border rounded transition-colors"
            title="새로고침"
          >
            <RefreshCw className={`w-4 h-4 text-dark-muted ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 전체 섹터 리스트 */}
      {performance && (
        <div className="flex-1 overflow-y-auto space-y-1">
          {allSectors.map((etf) => (
            <ETFRow
              key={etf.code}
              etf={etf}
              isSelected={selectedETF?.code === etf.code}
              onClick={() => setSelectedETF(selectedETF?.code === etf.code ? null : etf)}
              onDoubleClick={() => handleETFClick(etf)}
            />
          ))}
        </div>
      )}

      {/* 선택된 ETF의 관련 종목 */}
      {selectedETF && selectedETF.related_stocks && selectedETF.related_stocks.length > 0 && (
        <div className="mt-3 pt-3 border-t border-dark-border">
          <div className="text-sm text-dark-muted mb-2">
            {selectedETF.sector_kr} 관련 종목
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {selectedETF.related_stocks.map((stock) => (
              <button
                key={stock.code}
                className="w-full p-2 bg-dark-bg rounded hover:bg-dark-border flex items-center justify-between transition-colors"
                onClick={() => handleRelatedStockClick(stock)}
              >
                <span className="text-sm">{stock.name}</span>
                <ChevronRight className="w-4 h-4 text-dark-muted" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ETF 행 컴포넌트
function ETFRow({
  etf,
  isSelected,
  onClick,
  onDoubleClick,
}: {
  etf: KRETFData;
  isSelected: boolean;
  onClick: () => void;
  onDoubleClick: () => void;
}) {
  const colorClass = getPriceColorClass(etf.change_percent);
  const isPositive = etf.change_percent > 0;
  const isNegative = etf.change_percent < 0;

  return (
    <button
      className={`w-full p-2 rounded flex items-center justify-between transition-colors ${
        isSelected ? 'bg-dark-border' : 'bg-dark-bg hover:bg-dark-border/50'
      }`}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span className="text-xs text-dark-muted w-14 flex-shrink-0">{etf.code}</span>
        <span className="text-sm truncate">{etf.sector_kr}</span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-dark-muted">
          {etf.price > 0 ? formatPrice(etf.price) : '-'}
        </span>
        <span className={`text-sm font-medium w-16 text-right ${colorClass}`}>
          {etf.price > 0 ? (
            <>
              {isPositive ? '+' : ''}{etf.change_percent.toFixed(2)}%
            </>
          ) : (
            <span className="text-dark-muted">-</span>
          )}
        </span>
        {/* 등락 표시 바 */}
        <div className="w-12 h-1.5 bg-dark-border rounded overflow-hidden">
          <div
            className={`h-full ${isPositive ? 'bg-up' : isNegative ? 'bg-down' : 'bg-dark-muted'}`}
            style={{ width: `${Math.min(Math.abs(etf.change_percent) * 10, 100)}%` }}
          />
        </div>
      </div>
    </button>
  );
}
