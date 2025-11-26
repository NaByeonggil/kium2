import { useEffect, useState } from 'react';
import { usMarketApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import { getPriceColorClass } from '@/utils/format';
import { Globe, ChevronRight, RefreshCw } from 'lucide-react';
import type { USETFData, SectorPerformance } from '@/types';

export default function USSectorPanel() {
  const [performance, setPerformance] = useState<SectorPerformance | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSector, setSelectedSector] = useState<USETFData | null>(null);
  const { setSelectedStock } = useTradingStore();

  // 섹터 데이터 로드
  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await usMarketApi.getPerformance();
      setPerformance(data);
    } catch (error) {
      console.error('US Market load error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // 5분마다 갱신
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 관련 한국 종목 선택
  const handleKRStockClick = (stock: { code: string; name: string }) => {
    setSelectedStock({
      stock_code: stock.code,
      stock_name: stock.name,
      market_type: 'KRX',
    });
  };

  // 모든 섹터를 등락률 순으로 정렬
  const getAllSectors = (): USETFData[] => {
    if (!performance) return [];
    const allSectors = [...performance.top_gainers, ...performance.top_losers];
    // 중복 제거 후 등락률 순 정렬
    const uniqueSectors = allSectors.filter(
      (sector, index, self) => index === self.findIndex((s) => s.symbol === sector.symbol)
    );
    return uniqueSectors.sort((a, b) => b.change_percent - a.change_percent);
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
          <Globe className="w-5 h-5 text-dark-muted" />
          <span className="font-semibold">US ETF 섹터</span>
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
          {allSectors.map((sector) => (
            <SectorRow
              key={sector.symbol}
              sector={sector}
              isSelected={selectedSector?.symbol === sector.symbol}
              onClick={() => setSelectedSector(selectedSector?.symbol === sector.symbol ? null : sector)}
            />
          ))}
        </div>
      )}

      {/* 선택된 섹터의 관련 한국 종목 */}
      {selectedSector && selectedSector.related_kr_stocks && selectedSector.related_kr_stocks.length > 0 && (
        <div className="mt-3 pt-3 border-t border-dark-border">
          <div className="text-sm text-dark-muted mb-2">
            {selectedSector.sector_kr} 관련 한국 종목
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {selectedSector.related_kr_stocks.map((stock) => (
              <button
                key={stock.stock_code}
                className="w-full p-2 bg-dark-bg rounded hover:bg-dark-border flex items-center justify-between transition-colors"
                onClick={() => handleKRStockClick({ code: stock.stock_code, name: stock.stock_name })}
              >
                <span className="text-sm">{stock.stock_name}</span>
                <ChevronRight className="w-4 h-4 text-dark-muted" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// 섹터 행 컴포넌트
function SectorRow({
  sector,
  isSelected,
  onClick,
}: {
  sector: USETFData;
  isSelected: boolean;
  onClick: () => void;
}) {
  const colorClass = getPriceColorClass(sector.change_percent);
  const isPositive = sector.change_percent > 0;
  const isNegative = sector.change_percent < 0;

  return (
    <button
      className={`w-full p-2 rounded flex items-center justify-between transition-colors ${
        isSelected ? 'bg-dark-border' : 'bg-dark-bg hover:bg-dark-border/50'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span className="text-xs text-dark-muted w-10 flex-shrink-0">{sector.symbol}</span>
        <span className="text-sm truncate">{sector.sector_kr}</span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-dark-muted">${sector.price.toFixed(2)}</span>
        <span className={`text-sm font-medium w-16 text-right ${colorClass}`}>
          {isPositive ? '+' : ''}{sector.change_percent.toFixed(2)}%
        </span>
        {/* 등락 표시 바 */}
        <div className="w-12 h-1.5 bg-dark-border rounded overflow-hidden">
          <div
            className={`h-full ${isPositive ? 'bg-up' : isNegative ? 'bg-down' : 'bg-dark-muted'}`}
            style={{ width: `${Math.min(Math.abs(sector.change_percent) * 10, 100)}%` }}
          />
        </div>
      </div>
    </button>
  );
}
