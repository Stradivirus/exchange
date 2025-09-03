import axios from 'axios';

// 오늘자 정보 전체 조회 API
export async function fetchTodayInfo() {
  const response = await axios.get('http://localhost:8080/api/mongo/latest');
  return response.data;
}
