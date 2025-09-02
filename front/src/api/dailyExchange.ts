// 일별 집계 환율/금/유가/지수/금리 API
import axios from 'axios';

export interface DailyExchange {
  date: string; // yyyy-MM-dd
  dollar: number;
  gold: number;
  oil: number;
  dxy: number;
  baseRate: number;
  usBaseRate: number;
}

// 가장 최근 1일치 데이터 조회
export async function fetchLatestDailyExchange(): Promise<DailyExchange | null> {
  const res = await axios.get('/api/daily-exchange/latest');
  return res.data ?? null;
}

// (추후 확장) 기간별 데이터 조회 등도 추가 가능
