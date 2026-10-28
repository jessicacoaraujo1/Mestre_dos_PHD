"use client";

import { useEffect, useState, type FormEvent } from 'react';

interface ProgramaDoutorado {
  id: string;
  sigla: string;
  programa: string;
  uf: string;
  area: string;
  notaCapes: number;
  status: 'Aberto' | 'Iminente' | 'Acompanhando';
  previsao: string;
}

const API_BASE = 'http://127.0.0.1:8000';

export default function DashboardApple() {
  const [programas, setProgramas] = useState<ProgramaDoutorado[]>([]);
  const [subpastas, setSubpastas] = useState<string[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [form, setForm] = useState({
    nome_completo: '',
    cpf: '',
    email: '',
    nome_concurso: 'Doutorado em Economia e Desenvolvimento - UFPA 2026',
  });
  const [gerando, setGerando] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/programas?uf=SP`)
      .then((res) => res.json())
      .then((data) => {
        const mapped: ProgramaDoutorado[] = Array.isArray(data)
          ? data.map((item: any, index: number) => ({
              id: String(item.id ?? index),
              sigla: item.instituicao_sigla ?? 'SIGLA',
              programa: item.programa_nome ?? 'Programa',
              uf: item.uf ?? 'SP',
              area: item.area_avaliacao ?? 'Área',
              notaCapes: Number(item.nota_capes ?? 0),
              status: 'Acompanhando' as const,
              previsao: item.previsao ?? 'Aguardando Edital',
            }))
          : [];
        setProgramas(mapped);
        setCarregando(false);
      })
      .catch(() => setCarregando(false));
  }, []);

  const adicionarSubpasta = (nome: string) => {
    if (!subpastas.includes(nome)) setSubpastas([...subpastas, nome]);
  };

  const gerarApostila = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setGerando(true);
    try {
      const payload = {
        nome_completo: form.nome_completo,
        cpf: form.cpf,
        email: form.email,
        nome_concurso: form.nome_concurso,
        modulos: [
          {
            titulo: 'Módulo I: Tópicos Avançados do Edital',
            resumo: 'Síntese direcionada para o processo seletivo com foco na bibliografia oficial e nos itens estratégicos do edital.',
            topicos: [
              { nome: 'Metodologia e Marcos Regulatórios', prioridade: 'Alta' },
              { nome: 'Análise Qualitativa e Quantitativa de Políticas Públicas', prioridade: 'Alta' },
            ],
          },
        ],
      };

      const response = await fetch(`${API_BASE}/api/apostila/gerar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Erro ao gerar a apostila no servidor.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Apostila_ProjetoGigante_${form.nome_completo.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      alert('Apostila gerada e baixada com sucesso.');
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Falha ao gerar a apostila.');
    } finally {
      setGerando(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#F5F5F7', color: '#1d1d1f', fontFamily: 'sans-serif', padding: '32px' }}>
      <header style={{ maxWidth: '1200px', margin: '0 auto', borderBottom: '1px solid #e5e5e7', paddingBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase', color: '#86868b' }}>
            EditalHub · Monitor Nacional de Doutorados
          </span>
          <h1 style={{ fontSize: '32px', fontWeight: 700, margin: '8px 0 0 0' }}>
            Painel de Editais (Economia, Direito, RI & Ciência Política)
          </h1>
        </div>
        <div style={{ backgroundColor: '#ffffff', padding: '8px 16px', borderRadius: '20px', border: '1px solid #e5e5e7', fontSize: '12px', fontWeight: 600 }}>
          🟢 API Python & Telegram Conectados
        </div>
      </header>

      <main style={{ maxWidth: '1200px', margin: '32px auto 0 auto' }}>
        <section style={{ backgroundColor: '#111827', color: '#f8fafc', borderRadius: '24px', padding: '24px', border: '1px solid #334155', marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div>
              <div style={{ fontSize: '12px', letterSpacing: '1px', textTransform: 'uppercase', color: '#93c5fd', fontWeight: 700 }}>Proteção e Geração de Apostilas</div>
              <h2 style={{ margin: '8px 0 0', fontSize: '28px' }}>Gerar apostila protegida com marca-d'água e rastreio</h2>
            </div>
          </div>

          <form onSubmit={gerarApostila} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#cbd5e1', marginBottom: '8px' }}>Nome completo</label>
              <input value={form.nome_completo} onChange={(event) => setForm({ ...form, nome_completo: event.target.value })} required placeholder="Seu nome completo" style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '12px', padding: '12px 14px', fontSize: '14px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#cbd5e1', marginBottom: '8px' }}>CPF</label>
              <input value={form.cpf} onChange={(event) => setForm({ ...form, cpf: event.target.value })} required placeholder="000.000.000-00" style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '12px', padding: '12px 14px', fontSize: '14px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#cbd5e1', marginBottom: '8px' }}>E-mail</label>
              <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required placeholder="seu@email.com" style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '12px', padding: '12px 14px', fontSize: '14px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button type="submit" disabled={gerando} style={{ width: '100%', background: gerando ? '#1d4ed8' : '#2563eb', color: '#fff', border: 'none', borderRadius: '12px', padding: '12px 18px', fontWeight: 700, cursor: 'pointer' }}>
                {gerando ? 'Gerando PDF...' : 'Baixar apostila'}
              </button>
            </div>
          </form>
        </section>

        {subpastas.length > 0 && (
          <section style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '18px', border: '1px solid #e5e5e7', marginBottom: '32px' }}>
            <h2 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#86868b', margin: '0 0 12px 0' }}>
              Subpastas de Acompanhamento ({subpastas.length})
            </h2>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {subpastas.map((item, idx) => (
                <div key={idx} style={{ backgroundColor: '#e8f2ff', color: '#0066cc', padding: '6px 14px', borderRadius: '12px', fontSize: '13px', fontWeight: 600 }}>
                  📁 Workspace: {item}
                </div>
              ))}
            </div>
          </section>
        )}

        {carregando ? (
          <p style={{ color: '#86868b' }}>Carregando dados nacionais da CAPES/MEC...</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
            {programas.map((prog) => (
              <div
                key={prog.id}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '20px',
                  padding: '24px',
                  border: '1px solid #e5e5e7',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.03)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <span style={{
                      backgroundColor: prog.status === 'Aberto' ? '#e6f4ea' : '#fff7e6',
                      color: prog.status === 'Aberto' ? '#137333' : '#b06000',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}>
                      {prog.status}
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: '#86868b' }}>
                      CAPES {prog.notaCapes}
                    </span>
                  </div>

                  <span style={{ fontSize: '12px', fontWeight: 600, color: '#86868b' }}>{prog.sigla} · {prog.uf}</span>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '6px 0 0 0' }}>{prog.programa}</h3>
                </div>

                <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #f5f5f7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: '#86868b' }}>Previsão: {prog.previsao}</span>
                  <button
                    onClick={() => adicionarSubpasta(prog.programa)}
                    style={{
                      backgroundColor: '#0066cc',
                      color: '#ffffff',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '16px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Seguir ➔
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
