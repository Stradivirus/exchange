import axios from 'axios';

// 오늘자 정보 전체 조회 API
export async function fetchTodayInfo() {
  const response = await axios.get('/api/mongo/latest');
  return response.data;
}

// [수정] 환율 최신 30개 조회 API (Mongo)
export async function fetchLatestExchange() {
  const response = await axios.get('/api/mongo/exchange/latest30');
  return response.data;
}

// [수정] 곡물 최신 30개 조회 API (Mongo)
export async function fetchLatestGrains() {
  const response = await axios.get('/api/mongo/grains/latest30');
  return response.data;
}

// [수정] 원자재 최신 30개 조회 API (Mongo)
export async function fetchLatestCommodities() {
  const response = await axios.get('/api/mongo/commodities/latest30');
  return response.data;
}

// [수정] 지수 최신 30개 조회 API (Mongo)
export async function fetchLatestCommoditiesIndex() {
  const response = await axios.get('/api/mongo/commodities_index/latest30');
  return response.data;
}

// [수정] 주식 최신 30개 조회 API (Mongo)
export async function fetchLatestStock() {
  const response = await axios.get('/api/mongo/stock/latest30');
  return response.data;
}