import React, { useEffect, useState } from 'react';
import { fetchExchangePricesByPeriod, ExchangePrice } from '../api/exchangePrice';
import styles from './ExchangePriceChart.module.css';

const PERIODS = [
  { label: '12시간', hours: 12 },
  { label: '1일', hours: 24 },
  { label: '1주일', hours: 24 * 7 },
  { label: '1달', hours: 24 * 30 },
  // { label: '3달', hours: 24 * 30 * 3 },
  // { label: '6달', hours: 24 * 30 * 6 },
  // { label: '1년', hours: 24 * 365 },
];

function getPeriodRange(hours: number) {
  const end = new Date();
  end.setHours(end.getHours() + 1); // 1시간 넉넉하게
  const start = new Date(end.getTime() - hours * 60 * 60 * 1000);
  return {
    start: start.toISOString(),
    end: end.toISOString(),
  };
}

const ExchangePriceChart: React.FC = () => {
  const [periodIdx, setPeriodIdx] = useState(1); // 기본 1일
  const [data, setData] = useState<ExchangePrice[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const { start, end } = getPeriodRange(PERIODS[periodIdx].hours);
    setLoading(true);
    setError(null);
    fetchExchangePricesByPeriod(start, end)
      .then(setData)
      .catch(() => setError('데이터를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [periodIdx]);

  return (
    <div className={styles.chartContainerWide}>
      <h2 className={styles.chartTitle}>환율 추이 그래프</h2>
      <div className={styles.topBar}>
        {/* 좌: 최고/최저 */}
        <div className={styles.sideInfo}>
          {!loading && !error && data.length > 0 && (() => {
            const minIdx = data.reduce((minI, d, i, arr) => d.price < arr[minI].price ? i : minI, 0);
            const maxIdx = data.reduce((maxI, d, i, arr) => d.price > arr[maxI].price ? i : maxI, 0);
            return <>
              <div className={styles.infoMax}>
                최고 <b>{data[maxIdx].price.toLocaleString()}원</b><br />
                <span className={styles.infoDate}>({new Date(data[maxIdx].datetime).toLocaleString()})</span>
              </div>
              <div className={styles.infoMin}>
                최저 <b>{data[minIdx].price.toLocaleString()}원</b><br />
                <span className={styles.infoDate}>({new Date(data[minIdx].datetime).toLocaleString()})</span>
              </div>
            </>;
          })()}
        </div>
        {/* 중앙: 현재가 */}
        <div className={styles.centerInfo}>
          {!loading && !error && data.length > 0 && (() => {
            const last = data[data.length - 1];
            const d = new Date(last.datetime);
            return <>
              <div className={styles.infoCurrentBig}>
                현재가 <b>{last.price.toLocaleString()}원</b>
              </div>
              <div className={styles.infoDateBig}>
                {(() => {
                  let hour = d.getHours();
                  if (d.getMinutes() >= 30) hour += 1;
                  if (hour === 24) hour = 0;
                  return `(${d.getMonth() + 1}.${d.getDate()} ${hour}시)`;
                })()}
              </div>
            </>;
          })()}
        </div>
        {/* 우: 기간 버튼 */}
        <div className={styles.sideButtons}>
          <div className={styles.periodButtons}>
            {PERIODS.map((p, i) => (
              <button
                key={p.label}
                onClick={() => setPeriodIdx(i)}
                className={periodIdx === i ? `${styles.periodButton} ${styles.periodButtonActive}` : styles.periodButton}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>
  {loading && <div className={styles.loading}>로딩 중...</div>}
  {error && <div className={styles.error}>{error}</div>}
  {!loading && !error && data.length === 0 && <div className={styles.noData}>데이터가 없습니다.</div>}
      {!loading && !error && data.length > 0 && (() => {
        // 최고/최저점 계산
        const minIdx = data.reduce((minI, d, i, arr) => d.price < arr[minI].price ? i : minI, 0);
        const maxIdx = data.reduce((maxI, d, i, arr) => d.price > arr[maxI].price ? i : maxI, 0);
        const min = Math.min(...data.map(d => d.price));
        const max = Math.max(...data.map(d => d.price));
        const range = max - min || 1;
  const svgWidth = 900;
  const svgLeft = 50;
  const svgRight = svgWidth - 50;
  const stepX = (svgRight - svgLeft) / (data.length - 1);
        // 최고점
  const maxX = svgLeft + maxIdx * stepX;
  const maxY = 270 - ((data[maxIdx].price - min) / range) * 230;
  // 최저점
  const minX = svgLeft + minIdx * stepX;
  const minY = 270 - ((data[minIdx].price - min) / range) * 230;
        // x축 날짜선/라벨 표시 여부
        const showDateGrid = periodIdx >= 2; // 1주일 이상
        // 날짜/월별로 인덱스 찾기
  let dateGrid: { x: number, date: string }[] = [];
        if (showDateGrid && data.length > 0) {
          let prevDate = '';
          let lastLabelIdx = -1;
          for (let i = 0; i < data.length; i++) {
            const d = new Date(data[i].datetime);
            let dateStr = `${d.getMonth() + 1}.${d.getDate()}`;
            if (periodIdx === 4 || periodIdx === 5 || periodIdx === 6) { // 3달, 6달, 1년
              if (d.getDate() === 1 || d.getDate() === 15 || i === 0) {
                // pass
              } else if (i === data.length - 1) {
                // 마지막 데이터는 일단 추가 후보로 남김
                lastLabelIdx = i;
                continue;
              } else {
                continue;
              }
            } else if (periodIdx === 3) { // 1달
              if (!(d.getDate() % 3 === 1 || i === 0)) {
                if (i === data.length - 1) {
                  lastLabelIdx = i;
                }
                continue;
              }
            }
            if (dateStr !== prevDate) {
              const x = svgLeft + i * stepX;
              dateGrid.push({ x, date: dateStr });
              prevDate = dateStr;
            }
          }
          // 마지막 데이터가 이미 라벨로 추가되어 있지 않으면 추가
          if (lastLabelIdx === data.length - 1) {
            const d = new Date(data[lastLabelIdx].datetime);
            const dateStr = `${d.getMonth() + 1}.${d.getDate()}`;
            if (dateGrid.length === 0 || dateGrid[dateGrid.length - 1].date !== dateStr) {
              const x = 50 + lastLabelIdx * stepX;
              dateGrid.push({ x, date: dateStr });
            }
          }
        }
        return (
          <svg width="100%" height="300" viewBox={`0 0 ${svgWidth} 300`} style={{ background: '#f7fafd', borderRadius: 8, border: '1px solid #e3e3e3' }}>
            {/* y축 5단위마다 희미한 기준선 및 라벨 (얇게) */}
            {(() => {
              const lines = [];
              const minYValue = Math.floor(min / 5) * 5;
              const maxYValue = Math.ceil(max / 5) * 5;
              for (let v = minYValue; v <= maxYValue; v += 5) {
                const y = 270 - ((v - min) / range) * 230;
                lines.push(
                  <g key={v}>
                    <line x1={svgLeft} y1={y} x2={svgRight} y2={y} stroke="#bbb" strokeWidth="0.7" opacity="0.25" />
                    <text x={svgLeft - 12} y={y + 4} fontSize="12" fill="#bbb" textAnchor="end">{v.toLocaleString()}</text>
                  </g>
                );
              }
              return lines;
            })()}

            {/* x축 날짜별 세로선 및 라벨 (1주일/1달, 얇게) */}
            {showDateGrid && dateGrid.map(({ x, date }, idx) => (
              <g key={date}>
                <line x1={x} y1="20" x2={x} y2="270" stroke="#bbb" strokeWidth="0.7" opacity="0.18" />
                <text x={x} y="290" fontSize="12" fill="#888" textAnchor="middle">{date}</text>
              </g>
            ))}

            {/* 축 (얇게) */}
            <line x1={svgLeft} y1="20" x2={svgLeft} y2="270" stroke="#bbb" strokeWidth="0.7" />
            <line x1={svgLeft} y1="270" x2={svgRight} y2="270" stroke="#bbb" strokeWidth="0.7" />
            {/* 데이터 라인 (얇게) */}
            {(() => {
              const points = data.map((d, i) => {
                const x = svgLeft + i * stepX;
                const y = 270 - ((d.price - min) / range) * 230;
                return `${x},${y}`;
              }).join(' ');
              return <polyline fill="none" stroke="#1976d2" strokeWidth="1.2" points={points} />;
            })()}
            {/* 점 (데이터 개수에 따라 크기 자동 조절) */}
            {(() => {
              // 50개 이하: 5, 51~150: 4, 151~300: 3, 301~600: 2, 601이상: 1.5
              let r = 5;
              if (data.length > 600) r = 1.5;
              else if (data.length > 300) r = 2;
              else if (data.length > 150) r = 3;
              else if (data.length > 50) r = 4;
              return data.map((d, i) => {
                const x = svgLeft + i * stepX;
                const y = 270 - ((d.price - min) / range) * 230;
                return <circle key={d.id} cx={x} cy={y} r={r} fill="#1976d2" />;
              });
            })()}
            {/* 최고점/최저점 원만 강조 (데이터 많으면 작게) */}
            {(() => {
              // 최고/최저점은 일반 점보다 2배 크게, 단 최소 4 최대 10
              let r = 5;
              if (data.length > 600) r = 1.5;
              else if (data.length > 300) r = 2;
              else if (data.length > 150) r = 3;
              else if (data.length > 50) r = 4;
              const big = Math.max(4, Math.min(10, r * 2));
              return [
                <circle key="max" cx={maxX} cy={maxY} r={big} fill="#ff5252" stroke="#fff" strokeWidth={2} />, 
                <circle key="min" cx={minX} cy={minY} r={big} fill="#009688" stroke="#fff" strokeWidth={2} />
              ];
            })()}
            {/* x축 라벨 (12시간/1일: 날짜 바뀔 때만 날짜+시, 그 외는 시만) */}
            {!showDateGrid && data.length > 0 && (() => {
              const interval = periodIdx === 0 ? 2 : 2;
              const labels = [];
              let prevDate = '';
              for (let i = 0; i < data.length; i++) {
                if (i % interval === 0 || i === data.length - 1) {
                  const d = new Date(data[i].datetime);
                  let hour = d.getHours();
                  if (d.getMinutes() >= 30) hour += 1;
                  if (hour === 24) hour = 0;
                  const x = svgLeft + i * stepX;
                  const dateStr = `${d.getMonth() + 1}.${d.getDate()}`;
                  if (dateStr !== prevDate) {
                    labels.push(
                      <text key={i} x={x} y="290" fontSize="12" fill="#888" textAnchor="middle">
                        {`${dateStr} ${hour}시`}
                      </text>
                    );
                    prevDate = dateStr;
                  } else {
                    labels.push(
                      <text key={i} x={x} y="290" fontSize="12" fill="#888" textAnchor="middle">
                        {`${hour}시`}
                      </text>
                    );
                  }
                }
              }
              return labels;
            })()}
          </svg>
        );
      })()}
    </div>
  );
};

export default ExchangePriceChart;
