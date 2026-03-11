'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';

const MESES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const ETAPA_CONFIG = {
    POLIZA_ENVIADA: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '✅', label: 'Emitida' },
    RECHAZO_EMISION: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '❌', label: 'Rechazo Emisión' },
    RECHAZO_EXPIRACION: { color: '#f97316', bg: 'rgba(249,115,22,0.12)', icon: '⏰', label: 'Expirada' },
    RECHAZO_SELECCION: { color: '#a855f7', bg: 'rgba(168,85,247,0.12)', icon: '🚫', label: 'Selección' },
    RECHAZO_AUT_INFO_AD: { color: '#ec4899', bg: 'rgba(236,72,153,0.12)', icon: '📋', label: 'Aut/Info' },
    CANCELADO: { color: '#6b7280', bg: 'rgba(107,114,128,0.12)', icon: '🚫', label: 'Cancelada' },
};

const fmt = (n) => {
    if (n == null) return '0';
    return new Intl.NumberFormat('es-MX').format(n);
};

export default function IndicadoresSolicitudes() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [anio, setAnio] = useState(2025);
    const [ramo, setRamo] = useState('');
    const [tab, setTab] = useState('pipeline'); // pipeline, agentes, rechazos

    useEffect(() => {
        setLoading(true);
        const params = new URLSearchParams({ anio });
        if (ramo) params.set('ramo', ramo);
        apiFetch(`/indicadores-solicitudes?${params}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [anio, ramo]);

    if (loading) return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0e1a' }}>
            <Sidebar />
            <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: '#94a3b8', fontSize: 18 }}>⏳ Cargando indicadores...</div>
            </main>
        </div>
    );

    if (!data) return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0e1a' }}>
            <Sidebar />
            <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: '#ef4444', fontSize: 18 }}>❌ Error al cargar datos. Importa el archivo VW_CONCENTRADO_ETAPAS primero.</div>
            </main>
        </div>
    );

    const k = data.kpis;
    const maxBarMes = Math.max(...(data.por_mes || []).map(m => m.total), 1);

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0e1a' }}>
            <Sidebar />
            <main style={{ flex: 1, padding: '24px 32px', overflowY: 'auto' }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
                    <div>
                        <h1 style={{ color: '#f1f5f9', fontSize: 24, fontWeight: 700, margin: 0 }}>
                            Indicadores de Solicitudes
                        </h1>
                        <p style={{ color: '#64748b', fontSize: 13, margin: '4px 0 0' }}>
                            Pipeline de trámites · Emisiones · Rechazos · Tiempos
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                        <select value={anio} onChange={e => setAnio(Number(e.target.value))}
                            style={{ background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 8, padding: '8px 14px', fontSize: 14 }}>
                            {(data.anios_disponibles || []).map(a => <option key={a} value={a}>{a}</option>)}
                        </select>
                        <select value={ramo} onChange={e => setRamo(e.target.value)}
                            style={{ background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 8, padding: '8px 14px', fontSize: 14 }}>
                            <option value="">Todos los ramos</option>
                            <option value="SALUD">Salud (GMM)</option>
                            <option value="VIDA">Vida</option>
                        </select>
                    </div>
                </div>

                {/* KPIS principales */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 16, marginBottom: 24 }}>
                    <KpiCard icon="📋" value={fmt(k.total_solicitudes)} label="Total Solicitudes" color="#3b82f6" />
                    <KpiCard icon="✅" value={fmt(k.emitidas)} label="Pólizas Emitidas" color="#10b981" sub={`${k.tasa_emision}%`} />
                    <KpiCard icon="❌" value={fmt(k.total_rechazos)} label="Total Rechazos" color="#ef4444" sub={`${k.tasa_rechazo}%`} />
                    <KpiCard icon="⏱️" value={`${k.promedio_dias_emision}d`} label="Prom. Días Emisión" color="#f59e0b" />
                    <KpiCard icon="🆕" value={fmt(k.nuevos)} label="Negocio Nuevo" color="#8b5cf6" />
                    <KpiCard icon="👥" value={fmt(k.total_solicitantes)} label="Solicitantes" color="#06b6d4" />
                </div>

                {/* Semáforo de etapas */}
                <div style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', borderRadius: 16, padding: '20px 24px', marginBottom: 24, border: '1px solid #334155' }}>
                    <h3 style={{ color: '#94a3b8', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, margin: '0 0 16px' }}>
                        Distribución del Pipeline
                    </h3>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                        <EtapaChip etapa="POLIZA_ENVIADA" count={k.emitidas} total={k.total_solicitudes} />
                        <EtapaChip etapa="RECHAZO_EMISION" count={k.rechazos_emision} total={k.total_solicitudes} />
                        <EtapaChip etapa="RECHAZO_EXPIRACION" count={k.rechazos_expiracion} total={k.total_solicitudes} />
                        <EtapaChip etapa="RECHAZO_SELECCION" count={k.rechazos_seleccion} total={k.total_solicitudes} />
                        <EtapaChip etapa="CANCELADO" count={k.canceladas} total={k.total_solicitudes} />
                    </div>
                    {/* Progress bar */}
                    <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', marginTop: 16 }}>
                        <div style={{ width: `${k.tasa_emision}%`, background: 'linear-gradient(90deg, #10b981, #34d399)', transition: 'width 0.5s' }} />
                        <div style={{ width: `${k.total_solicitudes > 0 ? k.rechazos_emision / k.total_solicitudes * 100 : 0}%`, background: '#ef4444', transition: 'width 0.5s' }} />
                        <div style={{ width: `${k.total_solicitudes > 0 ? k.rechazos_expiracion / k.total_solicitudes * 100 : 0}%`, background: '#f97316', transition: 'width 0.5s' }} />
                        <div style={{ width: `${k.total_solicitudes > 0 ? k.rechazos_seleccion / k.total_solicitudes * 100 : 0}%`, background: '#a855f7', transition: 'width 0.5s' }} />
                        <div style={{ flex: 1, background: '#334155' }} />
                    </div>
                    <div style={{ display: 'flex', gap: 20, marginTop: 8, fontSize: 11, color: '#94a3b8' }}>
                        <span><span style={{ color: '#10b981' }}>●</span> Emitidas {k.tasa_emision}%</span>
                        <span><span style={{ color: '#ef4444' }}>●</span> Rech. Emisión</span>
                        <span><span style={{ color: '#f97316' }}>●</span> Expiradas</span>
                        <span><span style={{ color: '#a855f7' }}>●</span> Selección</span>
                        <span><span style={{ color: '#334155' }}>●</span> Otros</span>
                    </div>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
                    {[
                        { id: 'pipeline', icon: '📊', label: 'Pipeline Mensual' },
                        { id: 'agentes', icon: '👤', label: 'Top Agentes' },
                        { id: 'rechazos', icon: '📋', label: 'Rechazos Recientes' },
                    ].map(t => (
                        <button key={t.id} onClick={() => setTab(t.id)}
                            style={{
                                background: tab === t.id ? 'linear-gradient(135deg, #3b82f6, #6366f1)' : '#1e293b',
                                color: tab === t.id ? '#fff' : '#94a3b8',
                                border: tab === t.id ? 'none' : '1px solid #334155',
                                borderRadius: 10, padding: '10px 20px', fontSize: 13, fontWeight: 600,
                                cursor: 'pointer', transition: 'all 0.2s',
                            }}>
                            {t.icon} {t.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div style={{ display: 'grid', gridTemplateColumns: tab === 'agentes' ? '1fr' : '2fr 1fr', gap: 20 }}>

                    {/* Pipeline Mensual */}
                    {tab === 'pipeline' && (
                        <>
                            <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155' }}>
                                <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 20px' }}>
                                    Solicitudes por Mes — {anio}
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {(data.por_mes || []).map(m => (
                                        <div key={m.mes} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <span style={{ color: '#94a3b8', fontSize: 13, width: 36, textAlign: 'right' }}>{MESES[m.mes]}</span>
                                            <div style={{ flex: 1, display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden', background: '#0f172a' }}>
                                                <div style={{ width: `${m.emitidas / maxBarMes * 100}%`, background: 'linear-gradient(90deg, #10b981, #34d399)', transition: 'width 0.4s' }}
                                                    title={`Emitidas: ${m.emitidas}`} />
                                                <div style={{ width: `${m.rechazadas / maxBarMes * 100}%`, background: 'linear-gradient(90deg, #ef4444, #f87171)', transition: 'width 0.4s' }}
                                                    title={`Rechazadas: ${m.rechazadas}`} />
                                                <div style={{ width: `${m.tramite / maxBarMes * 100}%`, background: 'linear-gradient(90deg, #f59e0b, #fbbf24)', transition: 'width 0.4s' }}
                                                    title={`Trámite: ${m.tramite}`} />
                                            </div>
                                            <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, width: 40, textAlign: 'right' }}>{m.total}</span>
                                        </div>
                                    ))}
                                </div>
                                <div style={{ display: 'flex', gap: 20, marginTop: 16, fontSize: 11, color: '#94a3b8' }}>
                                    <span>🟢 Emitidas</span>
                                    <span>🔴 Rechazadas</span>
                                    <span>🟡 Trámite</span>
                                </div>
                            </div>

                            {/* Sidebar: Por Ramo */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155' }}>
                                    <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
                                        Por Ramo
                                    </h3>
                                    {(data.por_ramo || []).map(r => (
                                        <div key={r.ramo} style={{ marginBottom: 16 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>
                                                    {r.ramo === 'SALUD' ? '🏥' : '💎'} {r.ramo}
                                                </span>
                                                <span style={{ color: '#10b981', fontSize: 13, fontWeight: 700 }}>{r.tasa_emision}%</span>
                                            </div>
                                            <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>
                                                <span>Total: {fmt(r.total)}</span>
                                                <span style={{ color: '#10b981' }}>✅ {fmt(r.emitidas)}</span>
                                                <span style={{ color: '#ef4444' }}>❌ {fmt(r.rechazadas)}</span>
                                            </div>
                                            <div style={{ height: 6, borderRadius: 3, background: '#0f172a', overflow: 'hidden' }}>
                                                <div style={{ height: '100%', width: `${r.tasa_emision}%`, background: r.ramo === 'SALUD' ? 'linear-gradient(90deg, #06b6d4, #22d3ee)' : 'linear-gradient(90deg, #8b5cf6, #a78bfa)', borderRadius: 3 }} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                {/* Métricas extra */}
                                <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155' }}>
                                    <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
                                        Métricas de Tiempo
                                    </h3>
                                    <Metric icon="⏱️" label="Promedio general" value={`${k.promedio_dias_tramite} días`} />
                                    <Metric icon="✅" label="Emisión promedio" value={`${k.promedio_dias_emision} días`} color="#10b981" />
                                    <Metric icon="🔄" label="Reingresos" value={fmt(k.reingresos)} color="#f97316" />
                                    <Metric icon="🆕" label="Negocio nuevo" value={`${k.total_solicitudes > 0 ? ((k.nuevos / k.total_solicitudes) * 100).toFixed(1) : 0}%`} color="#8b5cf6" />
                                </div>
                            </div>
                        </>
                    )}

                    {/* Top Agentes */}
                    {tab === 'agentes' && (
                        <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155' }}>
                            <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
                                Top 15 Agentes por Solicitudes — {anio}
                            </h3>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid #334155' }}>
                                        {['#', 'Agente', 'Total', 'Emitidas', 'Rechazadas', 'Tasa Emisión'].map(h => (
                                            <th key={h} style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', padding: '10px 12px', textAlign: h === 'Agente' ? 'left' : 'right', letterSpacing: 0.5 }}>{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {(data.top_agentes || []).map((a, i) => (
                                        <tr key={a.agente_id} style={{ borderBottom: '1px solid rgba(51,65,85,0.5)', transition: 'background 0.2s' }}
                                            onMouseEnter={e => e.currentTarget.style.background = 'rgba(59,130,246,0.05)'}
                                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                                            <td style={{ color: '#64748b', fontSize: 13, padding: '12px', textAlign: 'right' }}>{i + 1}</td>
                                            <td style={{ color: '#e2e8f0', fontSize: 13, padding: '12px', fontWeight: 600 }}>
                                                {a.nombre}
                                                <span style={{ color: '#64748b', fontSize: 11, marginLeft: 8 }}>ID: {a.agente_id}</span>
                                            </td>
                                            <td style={{ color: '#e2e8f0', fontSize: 14, padding: '12px', textAlign: 'right', fontWeight: 700 }}>{a.total}</td>
                                            <td style={{ color: '#10b981', fontSize: 14, padding: '12px', textAlign: 'right', fontWeight: 600 }}>{a.emitidas}</td>
                                            <td style={{ color: '#ef4444', fontSize: 14, padding: '12px', textAlign: 'right', fontWeight: 600 }}>{a.rechazadas}</td>
                                            <td style={{ padding: '12px', textAlign: 'right' }}>
                                                <span style={{
                                                    background: a.tasa_emision >= 80 ? 'rgba(16,185,129,0.15)' : a.tasa_emision >= 50 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                                                    color: a.tasa_emision >= 80 ? '#10b981' : a.tasa_emision >= 50 ? '#f59e0b' : '#ef4444',
                                                    padding: '4px 10px', borderRadius: 6, fontSize: 13, fontWeight: 700,
                                                }}>{a.tasa_emision}%</span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Rechazos Recientes */}
                    {tab === 'rechazos' && (
                        <>
                            <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155', gridColumn: 'span 2' }}>
                                <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
                                    Últimos Rechazos — Detalle
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {(data.rechazos_recientes || []).map((r, i) => {
                                        const cfg = ETAPA_CONFIG[r.etapa] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', icon: '❓', label: r.etapa };
                                        return (
                                            <div key={i} style={{ background: '#0f172a', borderRadius: 12, padding: '14px 18px', border: `1px solid ${cfg.color}22` }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                        <span style={{ background: cfg.bg, color: cfg.color, padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700 }}>
                                                            {cfg.icon} {cfg.label}
                                                        </span>
                                                        <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 14 }}>#{r.nosol}</span>
                                                        <span style={{ color: '#64748b', fontSize: 12 }}>{r.ramo}</span>
                                                    </div>
                                                    <div style={{ display: 'flex', gap: 10, fontSize: 12, color: '#64748b' }}>
                                                        <span>📅 {r.fecha_recepcion}</span>
                                                        {r.dias != null && <span>⏱️ {r.dias}d</span>}
                                                        <span>👤 {r.agente}</span>
                                                    </div>
                                                </div>
                                                <div style={{ color: '#94a3b8', fontSize: 12 }}>
                                                    <span style={{ fontWeight: 600, color: '#cbd5e1' }}>{r.contratante}</span>
                                                    {r.observaciones && (
                                                        <p style={{ margin: '6px 0 0', lineHeight: 1.5, color: '#78879b' }}>{r.observaciones}</p>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}

function KpiCard({ icon, value, label, color, sub }) {
    return (
        <div style={{
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            borderRadius: 14, padding: '18px 16px', border: '1px solid #334155',
            display: 'flex', flexDirection: 'column', gap: 4,
            transition: 'transform 0.2s, box-shadow 0.2s',
        }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = `0 8px 30px ${color}15`; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}
        >
            <div style={{ fontSize: 20, marginBottom: 2 }}>{icon}</div>
            <div style={{ color, fontSize: 26, fontWeight: 800, lineHeight: 1.1 }}>
                {value}
                {sub && <span style={{ fontSize: 13, fontWeight: 600, marginLeft: 6, opacity: 0.8 }}>{sub}</span>}
            </div>
            <div style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
        </div>
    );
}

function EtapaChip({ etapa, count, total }) {
    const cfg = ETAPA_CONFIG[etapa] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', icon: '?', label: etapa };
    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
    return (
        <div style={{
            background: cfg.bg, border: `1px solid ${cfg.color}33`, borderRadius: 10,
            padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 150px',
        }}>
            <span style={{ fontSize: 22 }}>{cfg.icon}</span>
            <div>
                <div style={{ color: cfg.color, fontSize: 20, fontWeight: 800 }}>{fmt(count)}</div>
                <div style={{ color: '#94a3b8', fontSize: 11 }}>{cfg.label} · {pct}%</div>
            </div>
        </div>
    );
}

function Metric({ icon, label, value, color = '#e2e8f0' }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #334155' }}>
            <span style={{ color: '#94a3b8', fontSize: 13 }}>{icon} {label}</span>
            <span style={{ color, fontSize: 15, fontWeight: 700 }}>{value}</span>
        </div>
    );
}
