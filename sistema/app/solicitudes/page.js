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
    const [segmento, setSegmento] = useState('');
    const [gestion, setGestion] = useState('');
    const [lider, setLider] = useState('');
    const [tab, setTab] = useState('pipeline'); // pipeline, looker, agentes, rechazos

    useEffect(() => {
        setLoading(true);
        const params = new URLSearchParams({ anio });
        if (ramo) params.set('ramo', ramo);
        if (segmento) params.set('segmento', segmento);
        if (gestion) params.set('gestion', gestion);
        if (lider) params.set('lider', lider);

        apiFetch(`/indicadores-solicitudes?${params}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [anio, ramo, segmento, gestion, lider]);

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
                <div style={{ color: '#ef4444', fontSize: 18 }}>❌ Error al cargar datos.</div>
            </main>
        </div>
    );

    const k = data.kpis;
    const maxBarMes = Math.max(...(data.por_mes || []).map(m => m.total), 1);
    const disponibilidad = data.disponibles || {};

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
                </div>

                {/* Filtros Looker-style */}
                <div style={{ background: '#1e293b', borderRadius: 12, padding: '16px 20px', marginBottom: 24, border: '1px solid #334155', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr) auto', gap: 12, alignItems: 'end' }}>
                    <FilterSelect label="Año" value={anio} onChange={setAnio} options={data.anios_disponibles} />
                    <FilterSelect label="Ramo" value={ramo} onChange={setRamo} options={['SALUD', 'VIDA']} isRamo />
                    <FilterSelect label="Segmento" value={segmento} onChange={setSegmento} options={disponibilidad.segmentos} />
                    <FilterSelect label="Gestión Comercial" value={gestion} onChange={setGestion} options={disponibilidad.gestiones} />
                    <FilterSelect label="Promotor / Líder" value={lider} onChange={setLider} options={disponibilidad.lideres} />
                    <button onClick={() => { setAnio(2025); setRamo(''); setSegmento(''); setGestion(''); setLider(''); }} 
                        style={{ padding: '8px 16px', background: 'transparent', color: '#94a3b8', border: '1px solid #334155', borderRadius: 8, cursor: 'pointer', fontSize: 13, height: 38 }}>
                        Limpiar
                    </button>
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

                {/* Tabs */}
                <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid #334155' }}>
                    {[
                        { id: 'pipeline', icon: '📊', label: 'Pipeline Mensual' },
                        { id: 'looker', icon: '🔍', label: 'Vista Detallada (Looker)' },
                        { id: 'agentes', icon: '👤', label: 'Top Agentes' },
                        { id: 'rechazos', icon: '📋', label: 'Rechazos Recientes' },
                    ].map(t => (
                        <button key={t.id} onClick={() => setTab(t.id)}
                            style={{
                                borderBottom: tab === t.id ? '2px solid #3b82f6' : '2px solid transparent',
                                background: tab === t.id ? 'rgba(59,130,246,0.1)' : 'transparent',
                                color: tab === t.id ? '#3b82f6' : '#94a3b8',
                                padding: '12px 24px', fontSize: 13, fontWeight: 600,
                                cursor: 'pointer', transition: 'all 0.2s', borderTop: 'none', borderLeft: 'none', borderRight: 'none'
                            }}>
                            {t.icon} {t.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div style={{ display: 'grid', gridTemplateColumns: (tab === 'agentes' || tab === 'looker') ? '1fr' : '2fr 1fr', gap: 20 }}>

                    {/* VISTA LOOKER (PIVOT TABLES) */}
                    {tab === 'looker' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 24, paddingBottom: 40 }}>
                            <PivotHeatmap title="Solicitudes por Ramo / Mes" data={data.pivot_ramo} />
                            <PivotHeatmap title="Solicitudes por Etapa / Mes" data={data.pivot_etapa} />
                        </div>
                    )}

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
                                                <div style={{ width: `${m.emitidas / maxBarMes * 100}%`, background: 'linear-gradient(90deg, #10b981, #34d399)' }} />
                                                <div style={{ width: `${m.rechazadas / maxBarMes * 100}%`, background: 'linear-gradient(90deg, #ef4444, #f87171)' }} />
                                                <div style={{ width: `${m.tramite / maxBarMes * 100}%`, background: 'linear-gradient(90deg, #f59e0b, #fbbf24)' }} />
                                            </div>
                                            <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, width: 40, textAlign: 'right' }}>{m.total}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155' }}>
                                    <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 16px' }}>
                                        Distribución por Ramo
                                    </h3>
                                    {(data.por_ramo || []).map(r => (
                                        <div key={r.ramo} style={{ marginBottom: 16 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>{r.ramo}</span>
                                                <span style={{ color: '#10b981', fontSize: 13, fontWeight: 700 }}>{r.tasa_emision}%</span>
                                            </div>
                                            <div style={{ height: 6, borderRadius: 3, background: '#0f172a', overflow: 'hidden' }}>
                                                <div style={{ height: '100%', width: `${r.tasa_emision}%`, background: '#3b82f6' }} />
                                            </div>
                                        </div>
                                    ))}
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
                                            <th key={h} style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', padding: '10px 12px', textAlign: h === 'Agente' ? 'left' : 'right' }}>{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {(data.top_agentes || []).map((a, i) => (
                                        <tr key={a.agente_id} style={{ borderBottom: '1px solid rgba(51,65,85,0.5)' }}>
                                            <td style={{ color: '#64748b', fontSize: 13, padding: '12px', textAlign: 'right' }}>{i + 1}</td>
                                            <td style={{ color: '#e2e8f0', fontSize: 13, padding: '12px', fontWeight: 600 }}>{a.nombre} <span style={{ color: '#64748b', fontSize: 11 }}>{a.agente_id}</span></td>
                                            <td style={{ color: '#e2e8f0', fontSize: 14, padding: '12px', textAlign: 'right', fontWeight: 700 }}>{a.total}</td>
                                            <td style={{ color: '#10b981', fontSize: 14, padding: '12px', textAlign: 'right' }}>{a.emitidas}</td>
                                            <td style={{ color: '#ef4444', fontSize: 14, padding: '12px', textAlign: 'right' }}>{a.rechazadas}</td>
                                            <td style={{ padding: '12px', textAlign: 'right' }}>{a.tasa_emision}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Rechazos Recientes */}
                    {tab === 'rechazos' && (
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
                                                    <span style={{ background: cfg.bg, color: cfg.color, padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700 }}>{cfg.icon} {cfg.label}</span>
                                                    <span style={{ color: '#e2e8f0', fontWeight: 700 }}>#{r.nosol}</span>
                                                    <span style={{ color: '#64748b', fontSize: 12 }}>{r.ramo}</span>
                                                </div>
                                                <div style={{ display: 'flex', gap: 10, fontSize: 12, color: '#64748b' }}>
                                                    <span>📅 {r.fecha_recepcion}</span>
                                                    <span>👤 {r.agente}</span>
                                                </div>
                                            </div>
                                            <p style={{ margin: 0, color: '#94a3b8', fontSize: 12 }}>{r.observaciones}</p>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

function KpiCard({ icon, value, label, color, sub }) {
    return (
        <div style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', borderRadius: 14, padding: '18px 16px', border: '1px solid #334155' }}>
            <div style={{ fontSize: 20, marginBottom: 2 }}>{icon}</div>
            <div style={{ color, fontSize: 26, fontWeight: 800 }}>{value} {sub && <span style={{ fontSize: 13, opacity: 0.8 }}>{sub}</span>}</div>
            <div style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase' }}>{label}</div>
        </div>
    );
}

function FilterSelect({ label, value, onChange, options = [], isRamo }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', fontWeight: 600 }}>{label}</label>
            <select value={value} onChange={e => onChange(e.target.value)}
                style={{ background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 8, padding: '8px 12px', fontSize: 13, outline: 'none' }}>
                <option value="">{isRamo ? 'Todos' : `Seleccionar ${label}...`}</option>
                {options.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                ))}
            </select>
        </div>
    );
}

function PivotHeatmap({ title, data = [] }) {
    const maxVal = Math.max(...data.flatMap(d => Object.values(d.meses)), 1);
    
    const getBg = (val) => {
        if (!val) return 'transparent';
        const opacity = Math.min(0.1 + (val / maxVal) * 0.8, 0.9);
        return `rgba(59, 130, 246, ${opacity})`;
    };

    return (
        <div style={{ background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155', overflowX: 'auto' }}>
            <h3 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700, margin: '0 0 20px' }}>{title}</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                    <tr style={{ borderBottom: '1px solid #334155' }}>
                        <th style={{ color: '#64748b', padding: '8px 12px', textAlign: 'left' }}>Categoría</th>
                        {MESES.slice(1).map(m => <th key={m} style={{ color: '#64748b', padding: '8px 4px', width: 60 }}>{m}</th>)}
                        <th style={{ color: '#f1f5f9', padding: '8px 12px', textAlign: 'right' }}>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid rgba(51,65,85,0.3)' }}>
                            <td style={{ color: '#e2e8f0', padding: '10px 12px', fontWeight: 600 }}>{row.nombre}</td>
                            {Object.entries(row.meses).map(([m, val]) => (
                                <td key={m} style={{ 
                                    padding: '10px 4px', 
                                    textAlign: 'center', 
                                    background: getBg(val), 
                                    color: val > (maxVal/2) ? '#fff' : '#e2e8f0',
                                    borderRadius: 4,
                                    margin: 1
                                }}>
                                    {val || ''}
                                </td>
                            ))}
                            <td style={{ color: '#3b82f6', padding: '10px 12px', textAlign: 'right', fontWeight: 700 }}>{row.total}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
