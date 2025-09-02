import React, { useEffect, useState } from 'react';
import { fetchLatestDailyExchange, DailyExchange } from '../api/dailyExchange';
import axios from 'axios';

const labelMap: Record<keyof DailyExchange, string> = {
  date: '날짜',
  dollar: '달러 환율',
  gold: '금 가격',
  oil: '유가',
  dxy: 'DXY',
  baseRate: '한국 기준금리',
  usBaseRate: '미국 기준금리',
};

const numberFormat = (v: number) => v.toLocaleString('ko-KR', { maximumFractionDigits: 4 });


const DailyExchangeChart: React.FC = () => {
  const [data, setData] = useState<DailyExchange | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");

  // 날짜별 데이터 조회 함수
  const fetchByDate = async (date: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`/api/daily-exchange/${date}`);
      setData(res.data ?? null);
    } catch {
      setError('데이터를 불러오지 못했습니다.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDate) {
      fetchByDate(selectedDate);
    } else {
      fetchLatestDailyExchange()
        .then(setData)
        .catch(() => setError('데이터를 불러오지 못했습니다.'))
        .finally(() => setLoading(false));
    }
    // eslint-disable-next-line
  }, [selectedDate]);

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div style={{ maxWidth: 600, margin: '32px auto', background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px #0001', padding: 32 }}>
      <h2 style={{ textAlign: 'center', marginBottom: 24 }}>일별 집계 데이터</h2>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <input
          type="date"
          value={selectedDate}
          max={today}
          onChange={e => setSelectedDate(e.target.value)}
          style={{ fontSize: 18, padding: '4px 12px', borderRadius: 6, border: '1px solid #ccc' }}
        />
        {selectedDate && (
          <button onClick={() => setSelectedDate("")} style={{ marginLeft: 12, fontSize: 16 }}>오늘로</button>
        )}
      </div>
      {loading && <div>로딩 중...</div>}
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {!loading && !error && !data && <div>데이터 없음</div>}
      {!loading && !error && data && (
        <table style={{ width: '100%', fontSize: 18, borderCollapse: 'collapse' }}>
          <tbody>
            {Object.entries(data).map(([key, value]) => (
              <tr key={key}>
                <td style={{ fontWeight: 600, padding: '8px 0', borderBottom: '1px solid #eee', width: 180 }}>{labelMap[key as keyof DailyExchange]}</td>
                <td style={{ padding: '8px 0', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                  {typeof value === 'number' ? numberFormat(value) : value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DailyExchangeChart;
