"use client";

import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const tabs = [
  { id: 'home', label: 'Home' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'cadastro', label: 'Cadastro' },
  { id: 'login', label: 'Login' },
  { id: 'pagamento', label: 'Pagamento' },
];

const metrics = [
  { value: '2.4k', label: 'programas mapeados' },
  { value: '98%', label: 'alertas relevantes' },
  { value: '6h', label: 'varredura automática' },
  { value: '24/7', label: 'acompanhamento' },
];

const features = [
  {
    icon: '◎',
    title: 'Monitoramento inteligente',
    text: 'Rastreio contínuo de editais, universidades e oportunidades com alertas automáticos e filtros por área e UF.',
  },
  {
    icon: '▣',
    title: 'Dashboard premium',
    text: 'Uma experiência visual clara, forte e orientada à decisão em segundos.',
  },
  {
    icon: '✦',
    title: 'Material de estudo',
    text: 'Crie apostilas e organize um plano de estudos em um único ecossistema.',
  },
];

const programaCards = [
  { name: 'Mestrado em Economia', uf: 'SP', score: '5.0', status: 'Abertas' },
  { name: 'Doutorado em Direito', uf: 'RJ', score: '4.9', status: 'Em breve' },
  { name: 'Mestrado em Administração', uf: 'PA', score: '4.8', status: 'Acompanhando' },
];

const pricing = [
  {
    name: 'Starter',
    price: 'R$ 29',
    description: 'Para começar com organização e acompanhamento sem complicação.',
    feature: 'Acesso ao dashboard e 3 alertas mensais.',
    highlight: false,
  },
  {
    name: 'Pro',
    price: 'R$ 79',
    description: 'Para quem quer acompanhar editais com profundidade e eficiência.',
    feature: 'Monitoramento avançado + apostilas personalizadas.',
    highlight: true,
  },
  {
    name: 'Elite',
    price: 'R$ 149',
    description: 'Para quem quer máxima performance, suporte e visão estratégica.',
    feature: 'Tudo do Pro + relatórios e área de estudo completa.',
    highlight: false,
  },
];

const defaultDashboard = {
  summary: [
    { label: 'Programas salvos', value: '24', delta: '+6 esta semana' },
    { label: 'Alertas ativos', value: '12', delta: '3 críticos' },
    { label: 'Taxa de resposta', value: '98%', delta: 'em tempo real' },
    { label: 'Apostilas geradas', value: '08', delta: '+2 hoje' },
  ],
  alerts: [
    { title: 'Mestrado em Economia - USP', status: 'Abriu inscrição', time: 'Há 1h' },
    { title: 'Doutorado em Direito - UFRJ', status: 'Prazo em 5 dias', time: 'Hoje' },
    { title: 'Pós em Administração - UFPA', status: 'Nova revisão de edital', time: 'Ontem' },
  ],
  favorites: [
    { name: 'Mestrado em Economia', uf: 'SP', score: '5.0', track: 'Alta prioridade' },
    { name: 'Doutorado em Direito', uf: 'RJ', score: '4.9', track: 'Em alerta' },
    { name: 'Pós em Administração', uf: 'PA', score: '4.8', track: 'Acompanhando' },
  ],
  studyPlan: [
    { subject: 'Economia', progress: '82%' },
    { subject: 'Direito', progress: '65%' },
    { subject: 'Metodologia', progress: '49%' },
  ],
};

export default function PremiumLandingPage() {
  const [activeTab, setActiveTab] = useState('home');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [user, setUser] = useState<{ name: string; email: string; plan?: string; premium?: boolean } | null>(null);
  const [authForm, setAuthForm] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [checkoutForm, setCheckoutForm] = useState({
    cardName: '',
    cardNumber: '',
    expiry: '',
    cvv: '',
    cpf: '',
  });
  const [dashboardData, setDashboardData] = useState(defaultDashboard);

  useEffect(() => {
    const stored = localStorage.getItem('editalhub-user');
    if (stored) {
      setUser(JSON.parse(stored));
      setActiveTab('dashboard');
    }
  }, []);

  useEffect(() => {
    if (!user) {
      return;
    }

    const loadDashboard = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/dashboard/overview`);
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        }
      } catch {
        setDashboardData(defaultDashboard);
      }
    };

    loadDashboard();
  }, [user]);

  const signIn = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authForm.email, password: authForm.password }),
      });

      const data = await response.json();
      if (!response.ok) {
        alert(data.detail || 'Erro ao entrar.');
        return;
      }

      const nextUser = {
        name: data.name || 'Usuário',
        email: data.email || authForm.email,
        plan: 'Starter',
        premium: false,
      };
      localStorage.setItem('editalhub-user', JSON.stringify(nextUser));
      setUser(nextUser);
      setActiveTab('dashboard');
      alert('Login realizado com sucesso!');
    } catch {
      alert('Não foi possível conectar ao backend.');
    }
  };

  const signUp = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: authForm.name,
          email: authForm.email,
          password: authForm.password,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        alert(data.detail || 'Erro ao cadastrar.');
        return;
      }

      const nextUser = {
        name: data.name || authForm.name,
        email: data.email || authForm.email,
        plan: 'Starter',
        premium: false,
      };
      localStorage.setItem('editalhub-user', JSON.stringify(nextUser));
      setUser(nextUser);
      setActiveTab('dashboard');
      alert('Conta criada com sucesso!');
    } catch {
      alert('Não foi possível conectar ao backend.');
    }
  };

  const handleCheckout = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/payments/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: 'Pro',
          amount: 79,
          email: user?.email || authForm.email || 'cliente@editalhub.com',
          cardName: checkoutForm.cardName,
          cardNumber: checkoutForm.cardNumber,
          expiry: checkoutForm.expiry,
          cvv: checkoutForm.cvv,
          cpf: checkoutForm.cpf,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        alert(data.detail || 'Erro no checkout.');
        return;
      }

      const nextUser = { ...(user || { name: 'Cliente', email: authForm.email || 'cliente@editalhub.com' }), plan: 'Pro', premium: true };
      setUser(nextUser);
      localStorage.setItem('editalhub-user', JSON.stringify(nextUser));
      alert(`Pagamento confirmado: ${data.status || 'sucesso'}.`);
      setActiveTab('dashboard');
      setCheckoutForm({
        cardName: '',
        cardNumber: '',
        expiry: '',
        cvv: '',
        cpf: '',
      });
    } catch {
      alert('Checkout indisponível no momento.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('editalhub-user');
    setUser(null);
    setActiveTab('home');
  };

  return (
    <div className="page-shell">
      <div className="aurora aurora-one" />
      <div className="aurora aurora-two" />
      <div className="grid-glow" />

      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">E</div>
          <div>
            <span className="brand-name">EditalHub</span>
            <small>Primeiro nível</small>
          </div>
        </div>

        <nav className="nav">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              className={activeTab === item.id ? 'tab-button active' : 'tab-button'}
              onClick={() => setActiveTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="nav-actions">
          <button className="ghost-button" type="button" onClick={() => setActiveTab('login')}>Entrar</button>
          <button className="primary-button" type="button" onClick={() => setActiveTab('cadastro')}>Começar</button>
        </div>
      </header>

      <main className="content">
        {activeTab === 'home' && (
          <>
            <section className="hero">
              <div className="hero-copy">
                <span className="eyebrow">Monitoramento acadêmico premium</span>
                <h1>
                  O melhor <span>ecossistema</span> para planejar a sua pós-graduação.
                </h1>
                <p>
                  Acompanhe editais, encontre programas alinhados ao seu perfil, priorize seus estudos e transforme
                  oportunidades em decisões inteligentes com velocidade, rigor e clareza.
                </p>

                <div className="cta-row">
                  <button className="primary-button large" type="button" onClick={() => setActiveTab('cadastro')}>Começar agora</button>
                  <button className="secondary-button large" type="button" onClick={() => setActiveTab('login')}>Ver demonstração</button>
                </div>

                <div className="social-proof">
                  {metrics.map((metric) => (
                    <div key={metric.label} className="proof-item">
                      <strong>{metric.value}</strong>
                      <span>{metric.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="hero-visual">
                <div className="dashboard-window">
                  <div className="window-bar">
                    <span className="dot red" />
                    <span className="dot yellow" />
                    <span className="dot green" />
                  </div>

                  <div className="window-body">
                    <aside className="sidebar-mini">
                      <div className="mini-pill active">Programas</div>
                      <div className="mini-pill">Portais</div>
                      <div className="mini-pill">Apostilas</div>
                    </aside>

                    <div className="window-panel">
                      <div className="panel-header">
                        <div>
                          <p className="panel-label">Painel geral</p>
                          <h3>Oportunidades de pós-graduação</h3>
                        </div>
                        <button className="mini-button" type="button">Atualizar</button>
                      </div>

                      <div className="metrics-row">
                        <div className="metric-card primary">
                          <span>Programas</span>
                          <strong>2.4k</strong>
                        </div>
                        <div className="metric-card">
                          <span>Abertos</span>
                          <strong>184</strong>
                        </div>
                        <div className="metric-card">
                          <span>Alertas</span>
                          <strong>26</strong>
                        </div>
                      </div>

                      <div className="program-list">
                        {programaCards.map((card) => (
                          <div className="program-item" key={card.name}>
                            <div>
                              <strong>{card.name}</strong>
                              <small>{card.uf}</small>
                            </div>
                            <div className="program-meta">
                              <span>Nota {card.score}</span>
                              <em>{card.status}</em>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="feature-band">
              {features.map((feature) => (
                <article key={feature.title} className="feature-card">
                  <div className="feature-icon">{feature.icon}</div>
                  <h3>{feature.title}</h3>
                  <p>{feature.text}</p>
                </article>
              ))}
            </section>

            <section className="showcase">
              <div className="section-header">
                <span className="eyebrow muted">Por que EditalHub</span>
                <h2>Decisão mais clara, planejamento mais rápido e execução mais forte.</h2>
              </div>

              <div className="showcase-grid">
                <div className="glass-panel tall-panel">
                  <div className="panel-kicker">Acompanhamento</div>
                  <h3>O ecossistema que organiza tudo o que vai impactar o seu futuro.</h3>
                  <ul>
                    <li>Monitoramento contínuo de portais e editais.</li>
                    <li>Filtros precisos por área, cidade, nível e instituição.</li>
                    <li>Alertas com foco para agir com raciocínio e previsão.</li>
                  </ul>
                </div>

                <div className="glass-panel stack-panel">
                  <div className="tiny-chart">
                    <span className="bar b1" />
                    <span className="bar b2" />
                    <span className="bar b3" />
                    <span className="bar b4" />
                  </div>
                  <div className="mini-stats">
                    <div>
                      <strong>+31%</strong>
                      <span>maior eficiência</span>
                    </div>
                    <div>
                      <strong>6h</strong>
                      <span>varredura automática</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="pricing-section">
              <div className="section-header center">
                <span className="eyebrow muted">Planos</span>
                <h2>Escolha a experiência que combina com seu momento.</h2>
              </div>

              <div className="pricing-grid">
                {pricing.map((plan) => (
                  <article key={plan.name} className={plan.highlight ? 'pricing-card highlight' : 'pricing-card'}>
                    <span className="plan-tag">{plan.name}</span>
                    <h3>
                      {plan.price}
                      <small>/mês</small>
                    </h3>
                    <p>{plan.description}</p>
                    <ul>
                      <li>{plan.feature}</li>
                      <li>Acesso às ferramentas de estudo</li>
                      <li>Suporte com prioridade</li>
                    </ul>
                    <button className={plan.highlight ? 'primary-button wide' : 'secondary-button wide'} type="button" onClick={() => setActiveTab('pagamento')}>
                      Assinar
                    </button>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}

        {activeTab === 'cadastro' && (
          <section className="auth-section">
            <div className="auth-panel form-panel">
              <span className="eyebrow muted">Cadastro</span>
              <h2>Crie sua conta e comece a planejar com estratégia.</h2>
              <div className="auth-switcher">
                <button className={authMode === 'register' ? 'switch active' : 'switch'} type="button" onClick={() => setAuthMode('register')}>Cadastrar</button>
                <button className={authMode === 'login' ? 'switch active' : 'switch'} type="button" onClick={() => setAuthMode('login')}>Entrar</button>
              </div>
              <form className="form-grid" onSubmit={(event) => { event.preventDefault(); signUp(); }}>
                <input type="text" placeholder="Nome completo" value={authForm.name} onChange={(event) => setAuthForm({ ...authForm, name: event.target.value })} />
                <input type="email" placeholder="E-mail" value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} />
                <input type="password" placeholder="Senha" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} />
                <input type="text" placeholder="Universidade / objetivo" />
                <button className="primary-button large" type="submit">Criar conta</button>
              </form>
            </div>

            <div className="auth-panel benefit-panel">
              <div className="mini-badge">Incluído</div>
              <h3>Com a conta premium você desbloqueia:</h3>
              <ul>
                <li>Alertas personalizados em segundo plano</li>
                <li>Busca inteligente por programas e requisitos</li>
                <li>Material de estudo e apostilas integradas</li>
                <li>Accesso ao painel de acompanhamento do seu progresso</li>
              </ul>
            </div>
          </section>
        )}

        {activeTab === 'login' && (
          <section className="auth-section single-form">
            <div className="auth-panel form-panel centered">
              <span className="eyebrow muted">Login</span>
              <h2>Bem-vindo de volta.</h2>
              <div className="auth-switcher">
                <button className={authMode === 'register' ? 'switch active' : 'switch'} type="button" onClick={() => setAuthMode('register')}>Cadastrar</button>
                <button className={authMode === 'login' ? 'switch active' : 'switch'} type="button" onClick={() => setAuthMode('login')}>Entrar</button>
              </div>
              <form className="form-grid compact" onSubmit={(event) => { event.preventDefault(); signIn(); }}>
                <input type="email" placeholder="Seu e-mail" value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} />
                <input type="password" placeholder="Sua senha" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} />
                <label className="remember-row">
                  <input type="checkbox" defaultChecked />
                  <span>Lembrar de mim</span>
                </label>
                <button className="primary-button large" type="submit">Entrar</button>
              </form>
            </div>
          </section>
        )}

        {activeTab === 'pagamento' && (
          <section className="checkout-section">
            <div className="checkout-plan">
              <span className="eyebrow muted">Pagamento</span>
              <h2>Finalize sua assinatura em segundos.</h2>
              <div className="selected-plan">
                <span>Plano</span>
                <strong>Pro</strong>
                <small>R$ 79/mês</small>
              </div>
            </div>

            <div className="auth-panel form-panel">
              <form className="form-grid compact" onSubmit={(event) => { event.preventDefault(); handleCheckout(); }}>
                <input type="text" placeholder="Nome no cartão" value={checkoutForm.cardName} onChange={(event) => setCheckoutForm({ ...checkoutForm, cardName: event.target.value })} />
                <input type="text" placeholder="Número do cartão" value={checkoutForm.cardNumber} onChange={(event) => setCheckoutForm({ ...checkoutForm, cardNumber: event.target.value })} />
                <div className="two-columns">
                  <input type="text" placeholder="MM/AA" value={checkoutForm.expiry} onChange={(event) => setCheckoutForm({ ...checkoutForm, expiry: event.target.value })} />
                  <input type="text" placeholder="CVV" value={checkoutForm.cvv} onChange={(event) => setCheckoutForm({ ...checkoutForm, cvv: event.target.value })} />
                </div>
                <input type="text" placeholder="CPF / CNPJ" value={checkoutForm.cpf} onChange={(event) => setCheckoutForm({ ...checkoutForm, cpf: event.target.value })} />
                <button className="primary-button large" type="submit">Pagar agora</button>
              </form>
            </div>
          </section>
        )}

        {activeTab === 'dashboard' && user && (
          <section className="dashboard-shell">
            <div className="dashboard-header">
              <div>
                <span className="eyebrow muted">Painel do cliente</span>
                <h2>Bem-vindo, {user.name.split(' ')[0]}.</h2>
              </div>
              <div className="dashboard-actions">
                <span className="badge-plan">{user.plan || 'Starter'}</span>
                <button className="secondary-button" type="button" onClick={handleLogout}>Sair</button>
              </div>
            </div>

            <div className="dashboard-grid">
              {dashboardData.summary.map((item) => (
                <div key={item.label} className="dashboard-card">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                  <small>{item.delta}</small>
                </div>
              ))}
            </div>

            <div className="dashboard-main">
              <div className="glass-panel">
                <div className="panel-header compact-header">
                  <div>
                    <p className="panel-label">Alertas</p>
                    <h3>Oportunidades em tempo real</h3>
                  </div>
                  <button className="mini-button" type="button">Ver tudo</button>
                </div>
                <div className="alert-list">
                  {dashboardData.alerts.map((alert) => (
                    <div key={alert.title} className="list-row">
                      <div>
                        <strong>{alert.title}</strong>
                        <small>{alert.status}</small>
                      </div>
                      <span>{alert.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-panel">
                <div className="panel-header compact-header">
                  <div>
                    <p className="panel-label">Favoritos</p>
                    <h3>Programas em foco</h3>
                  </div>
                </div>
                <div className="favorites-list">
                  {dashboardData.favorites.map((program) => (
                    <div key={program.name} className="favorite-item">
                      <div>
                        <strong>{program.name}</strong>
                        <small>{program.uf}</small>
                      </div>
                      <div className="favorite-meta">
                        <span>Nota {program.score}</span>
                        <em>{program.track}</em>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="study-panel glass-panel">
              <div className="panel-header compact-header">
                <div>
                  <p className="panel-label">Estudos</p>
                  <h3>Plano de revisão</h3>
                </div>
              </div>
              <div className="study-list">
                {dashboardData.studyPlan.map((item) => (
                  <div key={item.subject} className="study-item">
                    <div className="study-topline">
                      <span>{item.subject}</span>
                      <strong>{item.progress}</strong>
                    </div>
                    <div className="progress-bar">
                      <span style={{ width: item.progress }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
