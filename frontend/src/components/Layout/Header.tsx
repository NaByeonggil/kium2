import { useState, useEffect } from 'react';
import { Activity, Wifi, WifiOff } from 'lucide-react';
import StockSearch from '@/components/Search/StockSearch';
import { subServerApi } from '@/services/api';

export default function Header() {
  const [subServerStatus, setSubServerStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  // Sub Server 상태 체크
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const result = await subServerApi.healthCheck();
        setSubServerStatus(result.connected ? 'connected' : 'disconnected');
      } catch {
        setSubServerStatus('disconnected');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-dark-card border-b border-dark-border px-4 flex items-center justify-between">
      {/* 로고 */}
      <div className="flex items-center gap-3">
        <Activity className="w-6 h-6 text-up" />
        <span className="text-xl font-bold">GSLTS</span>
        <span className="text-xs text-dark-muted">Trading Dashboard</span>
      </div>

      {/* 종목 검색 */}
      <div className="flex-1 max-w-xl mx-8">
        <StockSearch />
      </div>

      {/* 상태 표시 */}
      <div className="flex items-center gap-4">
        {/* Sub Server 상태 */}
        <div className="flex items-center gap-2">
          {subServerStatus === 'connected' ? (
            <Wifi className="w-4 h-4 text-green-500" />
          ) : subServerStatus === 'disconnected' ? (
            <WifiOff className="w-4 h-4 text-red-500" />
          ) : (
            <Wifi className="w-4 h-4 text-dark-muted animate-pulse" />
          )}
          <span className="text-xs text-dark-muted">
            Sub Server: {subServerStatus === 'connected' ? '연결됨' : subServerStatus === 'disconnected' ? '연결 안됨' : '확인 중'}
          </span>
        </div>

        {/* 시간 */}
        <Clock />
      </div>
    </header>
  );
}

// 시계 컴포넌트
function Clock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-sm text-dark-muted">
      {time.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
    </div>
  );
}
