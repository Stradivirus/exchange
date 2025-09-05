import React from 'react';

interface SectionContainerProps {
  children: React.ReactNode;
  title?: string; // 이렇게 ?를 추가
}

const SectionContainer: React.FC<SectionContainerProps> = ({ children, title }) => (
  <section style={{
    background: '#fff',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
    margin: '32px 0',
    padding: '24px',
    maxWidth: 700,
    width: '100%',
  }}>
    {title && <h2 style={{ borderBottom: '1px solid #eee', paddingBottom: 8, marginBottom: 16 }}>{title}</h2>}
    {children}
  </section>
);

export default SectionContainer;
