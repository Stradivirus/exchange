// 환율 관련 API 함수 모음
import axios from 'axios';

// 가장 최근 환율 1건 조회 (기존 유지)
export interface ExchangePrice {
  id: string;
  datetime: string;
  price: number;
}

export async function fetchLatestExchangePrice() {
  const res = await axios.get('/api/exchange-price');
  if (Array.isArray(res.data) && res.data.length > 0) {
    return res.data.sort((a, b) => new Date(b.datetime).getTime() - new Date(a.datetime).getTime())[0];
  }
  return null;
}
