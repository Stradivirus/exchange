import axios from 'axios';

// 오늘자 정보 전체 조회 API
export async function fetchTodayInfo() {
  const response = await axios.get('/api/mongo/latest');
  return response.data;
}

// PostgreSQL 환율 최신 30개 조회 API
export async function fetchLatestExchangeFromPostgre() {
  const response = await axios.get('/api/postgre/exchange/latest30');
  return response.data;
}

// PostgreSQL 곡물 최신 30개 조회 API
export async function fetchLatestGrainsFromPostgre() {
  const response = await axios.get('/api/postgre/grains/latest30');
  return response.data;
}

// PostgreSQL 원자재 최신 30개 조회 API
export async function fetchLatestCommoditiesFromPostgre() {
  const response = await axios.get('/api/postgre/commodities/latest30');
  return response.data;
}

// PostgreSQL 지수 최신 30개 조회 API
export async function fetchLatestCommoditiesIndexFromPostgre() {
  const response = await axios.get('/api/postgre/commodities_index/latest30');
  return response.data;
}

// PostgreSQL 주식 최신 30개 조회 API
export async function fetchLatestStockFromPostgre() {
  const response = await axios.get('/api/postgre/stock/latest30');
  return response.data;
}
