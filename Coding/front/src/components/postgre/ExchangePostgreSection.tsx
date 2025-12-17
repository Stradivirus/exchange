import React from 'react';

interface ExchangePostgreDto {
	date: string;
	usd: number | null;
	jpy: number | null;
	eur: number | null;
	cny: number | null;
}

interface Props {
	data: ExchangePostgreDto[];
	onBack?: () => void;
}

const ExchangePostgreSection: React.FC<Props> = ({ data, onBack }) => {
	return (
		<div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 2px 8px #0001', minWidth: 400 }}>
			<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
				<span style={{ fontWeight: 700, fontSize: '1.5rem' }}>환율 (최신 30일)</span>
				{onBack && (
					<button onClick={onBack} style={{ fontSize: 14, padding: '4px 12px' }}>돌아가기</button>
				)}
			</div>
			<div style={{ overflowX: 'auto' }}>
				<table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
					<thead>
						<tr style={{ background: '#f2f2f2' }}>
							<th style={{ padding: 8, border: '1px solid #eee' }}>날짜</th>
							<th style={{ padding: 8, border: '1px solid #eee' }}>USD</th>
							<th style={{ padding: 8, border: '1px solid #eee' }}>JPY</th>
							<th style={{ padding: 8, border: '1px solid #eee' }}>EUR</th>
							<th style={{ padding: 8, border: '1px solid #eee' }}>CNY</th>
						</tr>
					</thead>
					<tbody>
						{data && data.length > 0 ? (
							data.map((row, idx) => (
								<tr key={row.date} style={{ background: idx % 2 === 0 ? '#fff' : '#fafbfc' }}>
									<td style={{ padding: 8, border: '1px solid #eee', fontWeight: 500 }}>{row.date}</td>
									<td style={{ padding: 8, border: '1px solid #eee' }}>{row.usd?.toFixed(2) ?? '-'}</td>
									<td style={{ padding: 8, border: '1px solid #eee' }}>{row.jpy?.toFixed(2) ?? '-'}</td>
									<td style={{ padding: 8, border: '1px solid #eee' }}>{row.eur?.toFixed(2) ?? '-'}</td>
									<td style={{ padding: 8, border: '1px solid #eee' }}>{row.cny?.toFixed(2) ?? '-'}</td>
								</tr>
							))
						) : (
							<tr>
								<td colSpan={5} style={{ textAlign: 'center', padding: 16, color: '#888' }}>데이터 없음</td>
							</tr>
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
};

export default ExchangePostgreSection;