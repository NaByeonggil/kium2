import { useEffect, useState } from 'react';
import { balanceApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import { formatPrice, formatChangeRate, getPriceColorClass } from '@/utils/format';
import { Wallet, TrendingUp, TrendingDown } from 'lucide-react';

export default function BalancePanel() {
  const { balance, setBalance, setSelectedStock } = useTradingStore();
  const [isLoading, setIsLoading] = useState(false);

  // 잔고 로드
  useEffect(() => {
    const loadBalance = async () => {
      setIsLoading(true);
      try {
        const data = await balanceApi.get();
        setBalance(data);
      } catch (error) {
        console.error('Balance load error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadBalance();
    // 30초마다 갱신
    const interval = setInterval(loadBalance, 30000);
    return () => clearInterval(interval);
  }, [setBalance]);

  if (isLoading && !balance) {
    return (
      <div className="card p-4 h-full flex items-center justify-center text-dark-muted">
        로딩중...
      </div>
    );
  }

  if (!balance) return null;

  const profitColor = getPriceColorClass(balance.total_profit_loss);

  return (
    <div className="card p-4 h-full flex flex-col">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-4">
        <Wallet className="w-5 h-5 text-dark-muted" />
        <span className="font-semibold">계좌 잔고</span>
      </div>

      {/* 요약 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-dark-bg rounded">
          <div className="text-sm text-dark-muted mb-1">총평가금액</div>
          <div className="text-lg font-bold">{formatPrice(balance.total_eval)}원</div>
        </div>
        <div className="p-3 bg-dark-bg rounded">
          <div className="text-sm text-dark-muted mb-1">예수금</div>
          <div className="text-lg font-bold">{formatPrice(balance.cash_balance)}원</div>
        </div>
      </div>

      {/* 총손익 */}
      <div className="p-4 bg-dark-bg rounded mb-4">
        <div className="flex items-center justify-between">
          <span className="text-dark-muted">총평가손익</span>
          <div className="flex items-center gap-2">
            {balance.total_profit_loss > 0 ? (
              <TrendingUp className="w-5 h-5 text-up" />
            ) : balance.total_profit_loss < 0 ? (
              <TrendingDown className="w-5 h-5 text-down" />
            ) : null}
            <span className={`text-xl font-bold ${profitColor}`}>
              {balance.total_profit_loss > 0 ? '+' : ''}
              {formatPrice(balance.total_profit_loss)}원
            </span>
          </div>
        </div>
        <div className="text-right mt-1">
          <span className={`text-sm ${profitColor}`}>
            ({formatChangeRate(balance.total_profit_rate)})
          </span>
        </div>
      </div>

      {/* 보유종목 */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="text-sm text-dark-muted mb-2">
          보유종목 ({balance.holdings.length}개)
        </div>

        {balance.holdings.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-dark-muted">
            보유 종목이 없습니다
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2">
            {balance.holdings.map((holding) => (
              <div
                key={holding.stock_code}
                className="p-3 bg-dark-bg rounded hover:bg-dark-border cursor-pointer transition-colors"
                onClick={() =>
                  setSelectedStock({
                    stock_code: holding.stock_code,
                    stock_name: holding.stock_name,
                    market_type: 'KRX',
                  })
                }
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-medium">{holding.stock_name}</div>
                    <div className="text-xs text-dark-muted">{holding.stock_code}</div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${getPriceColorClass(holding.profit_loss)}`}>
                      {holding.profit_loss > 0 ? '+' : ''}
                      {formatPrice(holding.profit_loss)}원
                    </div>
                    <div className={`text-sm ${getPriceColorClass(holding.profit_rate)}`}>
                      ({formatChangeRate(holding.profit_rate)})
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-3 text-xs text-dark-muted">
                  <div>
                    <span>수량: </span>
                    <span className="text-dark-text">{holding.quantity}주</span>
                  </div>
                  <div>
                    <span>평단: </span>
                    <span className="text-dark-text">{formatPrice(holding.avg_price)}</span>
                  </div>
                  <div>
                    <span>현재가: </span>
                    <span className="text-dark-text">{formatPrice(holding.current_price)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
