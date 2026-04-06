'use client';
import { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, fmt } from '@/lib/api';

const MESES_NOMBRE = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const ESTADO_CONFIG = {
    TRAMITE:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '⏳', label: 'En Trámite' },
    EMITIDA:   { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '✅', label: 'Emitida' },
    PAGADA:    { color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', icon: '💰', label: 'Pagada' },
    RECHAZADA: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '❌', label: 'Rechazada' },
    CANCELADA: { color: '#6b7280', bg: 'rgba(107,114,128,0.12)', icon: '🚫', label: 'Cancelada' },
};

const fmtNum = (n) => {
    if (n == null) return '0';
    return new Intl.NumberFormat('es-MX').format(n);
};

export default function PipelineSolicitudes() {
    const [stats, setStats] = useState(null);
    const [solicitudes, setSolicitudes] = useState([]);
    const [alertas, setAlertas] = useState(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('pipeline');
    const [filtroEstado, setFiltroEstado] = useState('');
    const [filtroRamo, setFiltroRamo] = useState('');
    const [buscar, setBuscar] = useState('');
    const [selectedSol, setSelectedSol] = useState(null);
    const [trazabilidad, setTrazabilidad] = useState(null);
    const [loadingTraza, setLoadingTraza] = useState(false);

    // Load pipeline stats
    useEffect(() => {
        setLoading(true);
        Promise.all([
            apiFetch('/solicitudes/pipeline-stats'),
            apiFetch('/solicitudes?limit=100'),
            apiFetch('/solicitudes/alertas'),
        ]).then(([s, solResp, a]) => {
            setStats(s);
            setSolicitudes(solResp.solicitudes || []);
            setAlertas(a);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    // Load filtered list
    const loadFiltered = useCallback(() => {
        const params = new URLSearchParams({ limit: '200' });
        if (filtroEstado) params.set('estado', filtroEstado);
        if (filtroRamo) params.set('ramo', filtroRamo);
        apiFetch(`/solicitudes?${params}`).then(r => setSolicitudes(r.solicitudes || []));
    }, [filtroEstado, filtroRamo]);

    useEffect(() => { loadFiltered(); }, [loadFiltered]);

    // Load trazabilidad
    const openTrazabilidad = (nosol) => {
        setLoadingTraza(true);
        setSelectedSol(nosol);
        apiFetch(`/solicitudes/${nosol}/trazabilidad`)
            .then(t => { setTrazabilidad(t); setLoadingTraza(false); })
            .catch(() => setLoadingTraza(false));
    };

    if (loading) return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <div className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
                    <div className="pipeline-loading">
                        <div className="pipeline-loading-spinner" />
                        <p style={{ color: 'var(--text-secondary)', marginTop: 16 }}>Cargando Pipeline...</p>
                    </div>
                </div>
            </main>
        </div>
    );

    const s = stats || {};
    const funnel = s.funnel || {};
    const maxFunnel = Math.max(funnel.ingresadas || 1, 1);

    // Filter for search
    const filteredSols = solicitudes.filter(sol => {
        if (!buscar) return true;
        const q = buscar.toLowerCase();
        return (sol.nosol || '').toLowerCase().includes(q) ||
               (sol.contratante_nombre || '').toLowerCase().includes(q) ||
               (sol.idagente || '').toLowerCase().includes(q) ||
               (sol.agente_nombre || '').toLowerCase().includes(q);
    });

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <div className="page-content fade-in">

                {/* ── HEADER ── */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
                    <div>
                        <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.5px' }}>
                            Pipeline de Solicitudes
                        </h1>
                        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
                            Trazabilidad completa: Solicitud → Póliza → Pagos
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span className="badge badge-blue">📋 {fmtNum(s.total)} solicitudes</span>
                        {(s.atoradas || 0) > 0 && (
                            <span className="badge badge-rose" style={{ animation: 'pulse 2s infinite' }}>
                                ⚠️ {s.atoradas} atoradas
                            </span>
                        )}
                    </div>
                </div>

                {/* ── KPI CARDS ── */}
                <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                    <div className="kpi-card blue">
                        <span className="kpi-icon">📋</span>
                        <div className="kpi-label">Total Solicitudes</div>
                        <div className="kpi-value">{fmtNum(s.total)}</div>
                        <div className="kpi-sub">
                            Vida: {fmtNum(s.por_ramo?.vida)} · GMM: {fmtNum(s.por_ramo?.gmm)}
                        </div>
                    </div>
                    <div className="kpi-card emerald">
                        <span className="kpi-icon">✅</span>
                        <div className="kpi-label">Emitidas</div>
                        <div className="kpi-value">{fmtNum(s.emitida)}</div>
                        <div className="kpi-sub">
                            <span className="kpi-trend up">▲ {s.tasa_conversion}% conversión</span>
                        </div>
                    </div>
                    <div className="kpi-card amber">
                        <span className="kpi-icon">⏳</span>
                        <div className="kpi-label">En Trámite</div>
                        <div className="kpi-value">{fmtNum(s.tramite)}</div>
                        <div className="kpi-sub">{s.dias_promedio}d promedio</div>
                    </div>
                    <div className="kpi-card rose">
                        <span className="kpi-icon">❌</span>
                        <div className="kpi-label">Rechazadas</div>
                        <div className="kpi-value">{fmtNum(s.rechazada)}</div>
                        <div className="kpi-sub">
                            {s.total ? ((s.rechazada / s.total) * 100).toFixed(1) : 0}% tasa rechazo
                        </div>
                    </div>
                    <div className="kpi-card purple">
                        <span className="kpi-icon">⚠️</span>
                        <div className="kpi-label">Atoradas</div>
                        <div className="kpi-value">{fmtNum(s.atoradas)}</div>
                        <div className="kpi-sub">&gt;15 días sin movimiento</div>
                    </div>
                    <div className="kpi-card cyan">
                        <span className="kpi-icon">⏱️</span>
                        <div className="kpi-label">Días Promedio</div>
                        <div className="kpi-value">{s.dias_promedio || 0}<span style={{ fontSize: 14, opacity: 0.6 }}>d</span></div>
                        <div className="kpi-sub">Tiempo trámite</div>
                    </div>
                </div>

                {/* ── FUNNEL DE CONVERSIÓN ── */}
                <div className="card" style={{ marginBottom: 24, padding: '24px 28px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                        <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                            Funnel de Conversión
                        </h3>
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            Tasa de conversión: <strong style={{ color: 'var(--accent-emerald)' }}>{s.tasa_conversion}%</strong>
                        </span>
                    </div>
                    <div className="pipeline-funnel">
                        {[
                            { label: 'Ingresadas', value: funnel.ingresadas, color: '#3b82f6' },
                            { label: 'En Proceso', value: funnel.en_proceso, color: '#f59e0b' },
                            { label: 'Emitidas', value: funnel.emitidas, color: '#10b981' },
                            { label: 'Pagadas', value: funnel.pagadas, color: '#6366f1' },
                        ].map((step, i) => {
                            const pct = maxFunnel > 0 ? ((step.value || 0) / maxFunnel * 100) : 0;
                            return (
                                <div key={i} className="pipeline-funnel-step">
                                    <div className="pipeline-funnel-bar-wrap">
                                        <div className="pipeline-funnel-bar"
                                             style={{ width: `${Math.max(pct, 8)}%`, background: step.color }} />
                                    </div>
                                    <div className="pipeline-funnel-label">
                                        <span style={{ fontWeight: 700, color: step.color }}>{fmtNum(step.value || 0)}</span>
                                        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{step.label}</span>
                                    </div>
                                    {i < 3 && <div className="pipeline-funnel-arrow">→</div>}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* ── TABS ── */}
                <div className="pipeline-tabs">
                    {[
                        { id: 'pipeline', icon: '📊', label: 'Vista Mensual' },
                        { id: 'lista', icon: '📋', label: 'Lista de Solicitudes' },
                        { id: 'agentes', icon: '👤', label: 'Top Agentes' },
                        { id: 'alertas', icon: '⚠️', label: `Alertas (${alertas?.total_atoradas || 0})` },
                    ].map(t => (
                        <button key={t.id} onClick={() => setTab(t.id)}
                            className={`pipeline-tab ${tab === t.id ? 'active' : ''}`}>
                            <span>{t.icon}</span> {t.label}
                        </button>
                    ))}
                </div>

                {/* ── TAB: PIPELINE MENSUAL ── */}
                {tab === 'pipeline' && (
                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
                        <div className="card">
                            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
                                Solicitudes por Mes
                            </h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {(s.mensual || []).map(m => {
                                    const maxMes = Math.max(...(s.mensual || []).map(x => x.total), 1);
                                    return (
                                        <div key={m.mes} className="pipeline-bar-row">
                                            <span className="pipeline-bar-month">{MESES_NOMBRE[m.mes]}</span>
                                            <div className="pipeline-bar-track">
                                                <div className="pipeline-bar-emit" style={{ width: `${(m.emitidas / maxMes) * 100}%` }} />
                                                <div className="pipeline-bar-rech" style={{ width: `${(m.rechazadas / maxMes) * 100}%` }} />
                                            </div>
                                            <span className="pipeline-bar-total">{m.total}</span>
                                        </div>
                                    );
                                })}
                            </div>
                            <div style={{ display: 'flex', gap: 20, marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <span style={{ width: 10, height: 10, borderRadius: 3, background: 'linear-gradient(90deg, #10b981, #34d399)' }} /> Emitidas
                                </span>
                                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <span style={{ width: 10, height: 10, borderRadius: 3, background: 'linear-gradient(90deg, #ef4444, #f87171)' }} /> Rechazadas
                                </span>
                            </div>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <div className="card">
                                <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
                                    Por Estado
                                </h3>
                                {Object.entries(ESTADO_CONFIG).map(([key, cfg]) => {
                                    const val = s[key.toLowerCase()] || 0;
                                    const pct = s.total > 0 ? ((val / s.total) * 100).toFixed(1) : 0;
                                    return (
                                        <div key={key} style={{ marginBottom: 12 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span style={{ color: cfg.color, fontSize: 13, fontWeight: 600 }}>
                                                    {cfg.icon} {cfg.label}
                                                </span>
                                                <span style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 700 }}>
                                                    {fmtNum(val)} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({pct}%)</span>
                                                </span>
                                            </div>
                                            <div className="progress-bar">
                                                <div className="progress-fill" style={{ width: `${pct}%`, background: cfg.color }} />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="card">
                                <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
                                    Por Ramo
                                </h3>
                                <div style={{ display: 'flex', gap: 12 }}>
                                    <div className="pipeline-ramo-chip" style={{ flex: 1 }}>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Vida</div>
                                        <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-blue)' }}>{fmtNum(s.por_ramo?.vida)}</div>
                                    </div>
                                    <div className="pipeline-ramo-chip" style={{ flex: 1 }}>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>GMM</div>
                                        <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-emerald)' }}>{fmtNum(s.por_ramo?.gmm)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── TAB: LISTA ── */}
                {tab === 'lista' && (
                    <div>
                        {/* Filtros */}
                        <div className="filters-bar" style={{ marginBottom: 16 }}>
                            <div className="filter-group">
                                <span className="filter-label">🔍</span>
                                <input type="search" placeholder="Buscar nosol, contratante, agente..."
                                    value={buscar} onChange={e => setBuscar(e.target.value)}
                                    style={{ minWidth: 280 }} />
                            </div>
                            <div className="filter-group">
                                <span className="filter-label">Estado:</span>
                                <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}>
                                    <option value="">Todos</option>
                                    {Object.entries(ESTADO_CONFIG).map(([k, v]) => (
                                        <option key={k} value={k}>{v.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="filter-group">
                                <span className="filter-label">Ramo:</span>
                                <select value={filtroRamo} onChange={e => setFiltroRamo(e.target.value)}>
                                    <option value="">Todos</option>
                                    <option value="VIDA">Vida</option>
                                    <option value="GMM">GMM</option>
                                </select>
                            </div>
                        </div>

                        {/* Tabla */}
                        <div className="card" style={{ padding: 0 }}>
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>NoSol</th>
                                            <th>Ramo</th>
                                            <th>Contratante</th>
                                            <th>Agente</th>
                                            <th>Estado</th>
                                            <th>Días</th>
                                            <th>Última Etapa</th>
                                            <th>Póliza</th>
                                            <th style={{ textAlign: 'center' }}>Detalle</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredSols.slice(0, 100).map(sol => {
                                            const cfg = ESTADO_CONFIG[sol.estado] || ESTADO_CONFIG.TRAMITE;
                                            return (
                                                <tr key={sol.id}>
                                                    <td style={{ fontWeight: 700, color: 'var(--accent-blue-light)' }}>{sol.nosol || sol.folio}</td>
                                                    <td>
                                                        <span style={{ background: sol.ramo_normalizado === 'VIDA' ? 'rgba(99,102,241,0.15)' : 'rgba(16,185,129,0.15)',
                                                                       color: sol.ramo_normalizado === 'VIDA' ? '#818cf8' : '#34d399',
                                                                       padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600 }}>
                                                            {sol.ramo_normalizado || sol.nomramo || '—'}
                                                        </span>
                                                    </td>
                                                    <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                        {sol.contratante_nombre || '—'}
                                                    </td>
                                                    <td style={{ fontSize: 12 }}>{sol.agente_nombre || sol.idagente || '—'}</td>
                                                    <td>
                                                        <span className="status-pill" style={{ background: cfg.bg, color: cfg.color }}>
                                                            <span style={{ width: 6, height: 6, borderRadius: '50%', background: cfg.color }} />
                                                            {cfg.label}
                                                        </span>
                                                    </td>
                                                    <td style={{ fontWeight: 600, color: (sol.dias_tramite || 0) > 15 ? 'var(--accent-rose)' : 'var(--text-secondary)' }}>
                                                        {sol.dias_tramite ?? '—'}
                                                    </td>
                                                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                                        {sol.ultima_etapa || '—'}
                                                    </td>
                                                    <td style={{ fontFamily: 'monospace', fontSize: 12, color: sol.poliza_numero ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                                                        {sol.poliza_numero || '—'}
                                                    </td>
                                                    <td style={{ textAlign: 'center' }}>
                                                        <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 12 }}
                                                            onClick={() => openTrazabilidad(sol.nosol || sol.id)}>
                                                            🔍
                                                        </button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                            <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--text-muted)' }}>
                                Mostrando {Math.min(filteredSols.length, 100)} de {filteredSols.length} solicitudes
                            </div>
                        </div>
                    </div>
                )}

                {/* ── TAB: TOP AGENTES ── */}
                {tab === 'agentes' && (
                    <div className="card" style={{ padding: 0 }}>
                        <div style={{ padding: '20px 24px 8px', borderBottom: '1px solid var(--border)' }}>
                            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                                Top 10 Agentes por Solicitudes
                            </h3>
                        </div>
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style={{ width: 40 }}>#</th>
                                        <th>Agente</th>
                                        <th style={{ textAlign: 'right' }}>Total</th>
                                        <th style={{ textAlign: 'right' }}>Emitidas</th>
                                        <th style={{ textAlign: 'right' }}>Tasa</th>
                                        <th style={{ width: 200 }}>Conversión</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(s.top_agentes || []).map((a, i) => (
                                        <tr key={a.idagente}>
                                            <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                                            <td>
                                                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{a.nombre_completo || `Agente ${a.idagente}`}</div>
                                                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.idagente}</span>
                                            </td>
                                            <td style={{ textAlign: 'right', fontWeight: 700, fontSize: 15 }}>{a.total}</td>
                                            <td style={{ textAlign: 'right', color: 'var(--accent-emerald)', fontWeight: 600 }}>{a.emitidas}</td>
                                            <td style={{ textAlign: 'right' }}>
                                                <span style={{ color: a.tasa >= 70 ? 'var(--accent-emerald)' : a.tasa >= 50 ? 'var(--accent-amber)' : 'var(--accent-rose)', fontWeight: 700 }}>
                                                    {a.tasa}%
                                                </span>
                                            </td>
                                            <td>
                                                <div className="progress-bar" style={{ height: 8 }}>
                                                    <div className="progress-fill" style={{
                                                        width: `${a.tasa}%`,
                                                        background: a.tasa >= 70 ? 'var(--grad-emerald)' : a.tasa >= 50 ? 'var(--grad-amber)' : 'var(--grad-rose)',
                                                    }} />
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* ── TAB: ALERTAS ── */}
                {tab === 'alertas' && (
                    <div>
                        <div className="card" style={{ background: 'rgba(244,63,94,0.06)', borderColor: 'rgba(244,63,94,0.2)', marginBottom: 16  }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <span style={{ fontSize: 28 }}>⚠️</span>
                                <div>
                                    <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent-rose)' }}>{alertas?.total_atoradas || 0}</div>
                                    <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Solicitudes sin movimiento por más de 15 días</div>
                                </div>
                            </div>
                        </div>
                        <div className="card" style={{ padding: 0 }}>
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>NoSol</th>
                                            <th>Ramo</th>
                                            <th>Contratante</th>
                                            <th>Agente</th>
                                            <th>Días</th>
                                            <th>Última Etapa</th>
                                            <th>Fecha</th>
                                            <th style={{ textAlign: 'center' }}>Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(alertas?.solicitudes || []).slice(0, 50).map(sol => (
                                            <tr key={sol.id} style={{ background: 'rgba(244,63,94,0.03)' }}>
                                                <td style={{ fontWeight: 700, color: 'var(--accent-rose)' }}>{sol.nosol}</td>
                                                <td>{sol.ramo_normalizado || sol.nomramo || '—'}</td>
                                                <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {sol.contratante_nombre || '—'}
                                                </td>
                                                <td style={{ fontSize: 12 }}>{sol.agente_nombre || sol.idagente || '—'}</td>
                                                <td style={{ fontWeight: 700, color: 'var(--accent-rose)' }}>{sol.dias_tramite}d</td>
                                                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{sol.ultima_etapa || '—'}</td>
                                                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{sol.fecha_ultima_etapa || '—'}</td>
                                                <td style={{ textAlign: 'center' }}>
                                                    <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 12 }}
                                                        onClick={() => openTrazabilidad(sol.nosol)}>
                                                        🔍 Ver
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                </div>
            </main>

            {/* ── MODAL: TRAZABILIDAD ── */}
            {selectedSol && (
                <div className="pipeline-modal-overlay" onClick={() => { setSelectedSol(null); setTrazabilidad(null); }}>
                    <div className="pipeline-modal" onClick={e => e.stopPropagation()}>
                        <div className="pipeline-modal-header">
                            <h2>🔗 Trazabilidad — {selectedSol}</h2>
                            <button onClick={() => { setSelectedSol(null); setTrazabilidad(null); }}
                                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: 20, cursor: 'pointer' }}>✕</button>
                        </div>

                        {loadingTraza ? (
                            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                                <div className="pipeline-loading-spinner" />
                                <p style={{ marginTop: 12 }}>Cargando trazabilidad...</p>
                            </div>
                        ) : trazabilidad ? (
                            <div className="pipeline-modal-body">
                                {/* Solicitud */}
                                <div className="pipeline-traza-section">
                                    <h4 className="pipeline-traza-title">📋 Solicitud</h4>
                                    <div className="pipeline-traza-grid">
                                        <TrazaItem label="NoSol" value={trazabilidad.solicitud?.nosol} />
                                        <TrazaItem label="Ramo" value={trazabilidad.solicitud?.ramo_normalizado || trazabilidad.solicitud?.nomramo} />
                                        <TrazaItem label="Estado" value={trazabilidad.solicitud?.estado}
                                            color={ESTADO_CONFIG[trazabilidad.solicitud?.estado]?.color} />
                                        <TrazaItem label="Contratante" value={trazabilidad.solicitud?.contratante_nombre} />
                                        <TrazaItem label="Agente" value={trazabilidad.solicitud?.agente_nombre || trazabilidad.solicitud?.idagente} />
                                        <TrazaItem label="Días Trámite" value={trazabilidad.solicitud?.dias_tramite != null ? `${trazabilidad.solicitud.dias_tramite}d` : '—'} />
                                        <TrazaItem label="Recepción" value={trazabilidad.solicitud?.fecrecepcion} />
                                        <TrazaItem label="Solicitantes" value={trazabilidad.solicitud?.numsolicitantes} />
                                    </div>
                                </div>

                                {/* Timeline Etapas */}
                                <div className="pipeline-traza-section">
                                    <h4 className="pipeline-traza-title">⏱️ Timeline de Etapas ({trazabilidad.etapas?.length || 0})</h4>
                                    <div className="pipeline-timeline">
                                        {(trazabilidad.etapas || []).map((e, i) => (
                                            <div key={e.id} className="pipeline-timeline-item">
                                                <div className="pipeline-timeline-dot" />
                                                <div className="pipeline-timeline-content">
                                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{e.etapa}</span>
                                                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{e.fecetapa}</span>
                                                    </div>
                                                    {e.subetapa && <div style={{ fontSize: 12, color: 'var(--accent-blue-light)' }}>{e.subetapa}</div>}
                                                    {e.observaciones && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{e.observaciones}</div>}
                                                </div>
                                            </div>
                                        ))}
                                        {(trazabilidad.etapas || []).length === 0 && (
                                            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Sin etapas registradas</p>
                                        )}
                                    </div>
                                </div>

                                {/* Póliza */}
                                <div className="pipeline-traza-section">
                                    <h4 className="pipeline-traza-title">📋 Póliza Vinculada</h4>
                                    {trazabilidad.poliza ? (
                                        <div className="pipeline-traza-grid">
                                            <TrazaItem label="Póliza" value={trazabilidad.poliza.poliza_estandar} />
                                            <TrazaItem label="Asegurado" value={trazabilidad.poliza.asegurado_nombre} />
                                            <TrazaItem label="Ramo" value={trazabilidad.poliza.ramo_nombre} />
                                            <TrazaItem label="Prima Neta" value={trazabilidad.poliza.prima_neta ? fmt(trazabilidad.poliza.prima_neta) : '—'} />
                                            <TrazaItem label="Status" value={trazabilidad.poliza.mystatus} />
                                            <TrazaItem label="Vigencia" value={`${trazabilidad.poliza.fecha_inicio || ''} → ${trazabilidad.poliza.fecha_fin || ''}`} />
                                        </div>
                                    ) : (
                                        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Sin póliza vinculada</p>
                                    )}
                                </div>

                                {/* Pagos */}
                                <div className="pipeline-traza-section">
                                    <h4 className="pipeline-traza-title">
                                        💰 Pagos ({trazabilidad.pagos?.length || 0})
                                        {trazabilidad.resumen_pagos && (
                                            <span style={{ fontWeight: 400, fontSize: 13, color: 'var(--accent-emerald)', marginLeft: 12 }}>
                                                Total: {fmt(trazabilidad.resumen_pagos.prima_pagada_total)}
                                            </span>
                                        )}
                                    </h4>
                                    {(trazabilidad.pagos || []).length > 0 ? (
                                        <div className="table-container">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        <th>Fecha</th>
                                                        <th>Póliza</th>
                                                        <th style={{ textAlign: 'right' }}>Prima Neta</th>
                                                        <th style={{ textAlign: 'right' }}>Comisión</th>
                                                        <th>Ramo</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {trazabilidad.pagos.map((p, i) => (
                                                        <tr key={i}>
                                                            <td>{p.fecha_aplicacion || '—'}</td>
                                                            <td style={{ fontFamily: 'monospace' }}>{p.poliza_numero || p.poliza_match || '—'}</td>
                                                            <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--accent-emerald)' }}>
                                                                {p.prima_neta ? fmt(p.prima_neta) : '—'}
                                                            </td>
                                                            <td style={{ textAlign: 'right' }}>{p.comision_total ? fmt(p.comision_total) : p.comision ? fmt(p.comision) : '—'}</td>
                                                            <td>{p.ramo || '—'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    ) : (
                                        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Sin pagos registrados</p>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <p style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>No se pudo cargar la trazabilidad.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function TrazaItem({ label, value, color }) {
    return (
        <div className="pipeline-traza-item">
            <span className="pipeline-traza-item-label">{label}</span>
            <span className="pipeline-traza-item-value" style={color ? { color } : undefined}>{value || '—'}</span>
        </div>
    );
}
