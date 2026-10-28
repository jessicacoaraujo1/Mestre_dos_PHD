import React, { useState, useEffect } from 'react';
import { LayoutDashboard, BookOpen, Globe, Bell, Plus, Trash2, RefreshCw } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";

export default function EditalHubDashboard() {
  const [abaAtiva, setAbaAtiva] = useState('programas');
  const [programas, setProgramas] = useState([]);
  const [urlsMonitoradas, setUrlsMonitoradas] = useState([]);
  const [statusSistema, setStatusSistema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [novaUrl, setNovaUrl] = useState('');

  // Filtros
  const [filtroUf, setFiltroUf] = useState('');
  const [filtroBusca, setFiltroBusca] = useState('');

  const carregarDados = async () => {
    setLoading(true);
    try {
      // Carregar Status
      const resStatus = await fetch(`${API_BASE}/api/sistema/dashboard-status`);
      const dataStatus = await resStatus.json();
      setStatusSistema(dataStatus);

      // Carregar URLs Monitoradas
      const resUrls = await fetch(`${API_BASE}/api/sistema/urls`);
      const dataUrls = await resUrls.json();
      setUrlsMonitoradas(dataUrls.urls_monitoradas || []);

      // Carregar Programas CAPES
      const params = new URLSearchParams();
      if (filtroUf) params.append('uf', filtroUf);
      if (filtroBusca) params.append('busca', filtroBusca);
      
      const resProg = await fetch(`${API_BASE}/api/programas?${params.toString()}`);
      const dataProg = await resProg.json();
      setProgramas(dataProg || []);
    } catch (err) {
      console.error("Erro ao conectar com a API FastAPI:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarDados();
  }, [filtroUf, filtroBusca]);

  const handleAdicionarUrl = async (e) => {
    e.preventDefault();
    if (!novaUrl) return;
    
    try {
      await fetch(`${API_BASE}/api/monitorar-pagina`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: novaUrl })
      });
      setNovaUrl('');
      carregarDados();
    } catch (err) {
      alert("Erro ao cadastrar URL");
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* NAVEGAÇÃO SUPERIOR / HEADER */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 p-2 rounded-lg text-white font-bold">EH</div>
          <div>
            <h1 className="text-xl font-bold tracking-wide">EditalHub Control Center</h1>
            <p className="text-xs text-slate-400">Sistema de Monitoramento Acadêmico 24/7</p>
          </div>
        </div>

        <button 
          onClick={carregarDados}
          className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md text-sm transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Sincronizar
        </button>
      </header>

      <div className="flex flex-1">
        {/* BARRA LATERAL DE ABAS */}
        <aside className="w-64 bg-slate-800/50 border-r border-slate-800 p-4 space-y-2">
          <button
            onClick={() => setAbaAtiva('programas')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition ${
              abaAtiva === 'programas' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-5 h-5" /> Programas CAPES
          </button>

          <button
            onClick={() => setAbaAtiva('urls')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition ${
              abaAtiva === 'urls' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <Globe className="w-5 h-5" /> Portais Monitorados
          </button>

          <button
            onClick={() => setAbaAtiva('status')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition ${
              abaAtiva === 'status' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="w-5 h-5" /> Status do Servidor
          </button>
        </aside>

        {/* CONTEÚDO PRINCIPAL DAS ABAS */}
        <main className="flex-1 p-6 overflow-y-auto">
          {/* ABA 1: PROGRAMAS CAPES */}
          {abaAtiva === 'programas' && (
            <div className="space-y-6">
              <div className="flex flex-wrap gap-4 bg-slate-800 p-4 rounded-xl border border-slate-700">
                <input
                  type="text"
                  placeholder="Buscar por Universidade ou Programa..."
                  value={filtroBusca}
                  onChange={(e) => setFiltroBusca(e.target.value)}
                  className="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-sm flex-1 focus:outline-none focus:border-blue-500"
                />
                <select
                  value={filtroUf}
                  onChange={(e) => setFiltroUf(e.target.value)}
                  className="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="">Todos os Estados (UF)</option>
                  <option value="PA">Pará (PA)</option>
                  <option value="SP">São Paulo (SP)</option>
                  <option value="RJ">Rio de Janeiro (RJ)</option>
                  <option value="DF">Distrito Federal (DF)</option>
                  <option value="MG">Minas Gerais (MG)</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {programas.map((prog) => (
                  <div key={prog.id} className="bg-slate-800 border border-slate-700/60 p-5 rounded-xl hover:border-blue-500/50 transition">
                    <div className="flex justify-between items-start mb-3">
                      <span className="bg-blue-900/60 text-blue-300 text-xs font-semibold px-2.5 py-1 rounded-md border border-blue-700/50">
                        {prog.sigla_ies} • {prog.uf}
                      </span>
                      <span className="text-xs font-medium text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/50">
                        Nota CAPES: {prog.nota_capes}
                      </span>
                    </div>
                    <h3 className="font-semibold text-slate-100 text-base mb-1">{prog.programa}</h3>
                    <p className="text-xs text-slate-400 mb-4">{prog.area_avaliacao} • {prog.nivel}</p>
                    <div className="pt-3 border-t border-slate-700/50 flex justify-between items-center text-xs text-slate-400">
                      <span>Status: <strong className="text-amber-400">{prog.previsao_edital}</strong></span>
                      <a href={prog.link_busca} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">Buscar Edital →</a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ABA 2: PORTAIS MONITORADOS */}
          {abaAtiva === 'urls' && (
            <div className="space-y-6">
              <form onSubmit={handleAdicionarUrl} className="flex gap-3 bg-slate-800 p-4 rounded-xl border border-slate-700">
                <input
                  type="url"
                  placeholder="https://sua-universidade.edu.br/editais"
                  value={novaUrl}
                  onChange={(e) => setNovaUrl(e.target.value)}
                  className="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-sm flex-1 focus:outline-none focus:border-blue-500"
                  required
                />
                <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition">
                  <Plus className="w-4 h-4" /> Adicionar Portal
                </button>
              </form>

              <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-900/60 text-slate-400 uppercase text-xs">
                    <tr>
                      <th className="p-4">URL do Portal</th>
                      <th className="p-4">Última Checagem</th>
                      <th className="p-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {urlsMonitoradas.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-700/30">
                        <td className="p-4 font-mono text-xs text-blue-400">{item.url}</td>
                        <td className="p-4 text-xs text-slate-400">{item.ultima_verificacao || 'Aguardando...'}</td>
                        <td className="p-4">
                          <span className="bg-emerald-900/50 text-emerald-300 text-xs px-2.5 py-1 rounded-full border border-emerald-700/50">
                            {item.status_edital}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ABA 3: STATUS DO SERVIDOR */}
          {abaAtiva === 'status' && statusSistema && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl">
                <p className="text-xs text-slate-400 mb-1">Status da API</p>
                <p className="text-lg font-bold text-emerald-400">{statusSistema.status_servidor}</p>
              </div>
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl">
                <p className="text-xs text-slate-400 mb-1">Agendador 24h</p>
                <p className="text-lg font-bold text-blue-400">{statusSistema.agendador}</p>
              </div>
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl">
                <p className="text-xs text-slate-400 mb-1">Integração Telegram</p>
                <p className="text-lg font-bold text-purple-400">{statusSistema.telegram_bot}</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
// Função para deletar uma URL no frontend
const handleDeletarUrl = async (id) => {
  if (!confirm("Tem certeza que deseja remover este portal do monitoramento?")) return;

  try {
    const res = await fetch(`${API_BASE}/api/sistema/urls/${id}`, {
      method: 'DELETE',
    });
    if (res.ok) {
      carregarDados(); // Recarrega a tabela automaticamente
    } else {
      alert("Erro ao remover o portal.");
    }
  } catch (err) {
    console.error("Erro na requisição DELETE:", err);
  }
};

// Trecho da tabela atualizada com o botão de excluir
<tbody className="divide-y divide-slate-700/50">
  {urlsMonitoradas.map((item) => (
    <tr key={item.id} className="hover:bg-slate-700/30">
      <td className="p-4 font-mono text-xs text-blue-400">{item.url}</td>
      <td className="p-4 text-xs text-slate-400">{item.ultima_verificacao || 'Aguardando varredura...'}</td>
      <td className="p-4">
        <span className="bg-emerald-900/50 text-emerald-300 text-xs px-2.5 py-1 rounded-full border border-emerald-700/50">
          {item.status_edital}
        </span>
      </td>
      <td className="p-4 text-right">
        <button
          onClick={() => handleDeletarUrl(item.id)}
          className="text-rose-400 hover:text-rose-300 p-1 rounded hover:bg-rose-950/40 transition"
          title="Remover portal"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </td>
    </tr>
  ))}
</tbody>