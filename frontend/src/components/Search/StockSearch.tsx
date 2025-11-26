import { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import { stocksApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import type { StockInfo } from '@/types';

export default function StockSearch() {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState<StockInfo[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { selectedStock, setSelectedStock } = useTradingStore();

  // 검색
  useEffect(() => {
    if (keyword.length < 1) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const { stocks } = await stocksApi.search(keyword, 15);
        setResults(stocks);
        setIsOpen(true);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [keyword]);

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 종목 선택
  const handleSelect = (stock: StockInfo) => {
    setSelectedStock(stock);
    setKeyword('');
    setIsOpen(false);
  };

  // 선택 해제
  const handleClear = () => {
    setSelectedStock(null);
    setKeyword('');
    inputRef.current?.focus();
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      {/* 검색 입력 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-muted" />
        <input
          ref={inputRef}
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onFocus={() => keyword && setIsOpen(true)}
          placeholder="종목명 또는 종목코드 검색"
          className="input w-full pl-10 pr-10"
        />
        {(keyword || selectedStock) && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-muted hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* 선택된 종목 표시 */}
      {selectedStock && !keyword && (
        <div className="mt-2 p-2 bg-dark-card border border-dark-border rounded flex items-center justify-between">
          <div>
            <span className="font-medium">{selectedStock.stock_name}</span>
            <span className="text-dark-muted ml-2">{selectedStock.stock_code}</span>
            <span className="text-xs text-dark-muted ml-2 px-1.5 py-0.5 bg-dark-bg rounded">
              {selectedStock.market_type}
            </span>
          </div>
        </div>
      )}

      {/* 검색 결과 드롭다운 */}
      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-dark-card border border-dark-border rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {results.map((stock) => (
            <button
              key={stock.stock_code}
              onClick={() => handleSelect(stock)}
              className="w-full px-4 py-3 text-left hover:bg-dark-border transition-colors flex items-center justify-between"
            >
              <div>
                <span className="font-medium">{stock.stock_name}</span>
                <span className="text-dark-muted ml-2">{stock.stock_code}</span>
              </div>
              <span className="text-xs text-dark-muted px-2 py-0.5 bg-dark-bg rounded">
                {stock.market_type}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* 로딩 */}
      {isLoading && (
        <div className="absolute z-50 w-full mt-1 bg-dark-card border border-dark-border rounded-lg p-4 text-center text-dark-muted">
          검색 중...
        </div>
      )}

      {/* 결과 없음 */}
      {isOpen && keyword && !isLoading && results.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-dark-card border border-dark-border rounded-lg p-4 text-center text-dark-muted">
          검색 결과가 없습니다
        </div>
      )}
    </div>
  );
}
