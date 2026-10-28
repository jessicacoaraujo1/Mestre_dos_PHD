import type { Metadata } from 'next';
import React from 'react';

export const metadata: Metadata = {
  title: 'Edital Hub · Monitor de Doutorados',
  description: 'Plataforma inteligente de monitoramento de editais de doutorado.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, padding: 0, backgroundColor: '#F5F5F7' }}>{children}</body>
    </html>
  );
}
