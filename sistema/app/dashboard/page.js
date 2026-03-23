'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, MESES } from '@/lib/api';
import {
    BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

function fmt(n) {
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n?.toFixed(0) || 0}`;
}

function pct(val, meta) {
    if (!meta) return 0;
    return Math.min(100, Math.round((val / meta) * 100));
}

function fmtNum(n) {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(0)}K`;
    return `${n?.toFixed?.(0) ?? n ?? 0}`;
}

/* ── Small KPI Card ─────────────────────────────────────────── */
function KpiCard({ label, value, sub, icon, color, meta, highlight }) {
    const p = meta > 0 ? pct(typeof value === 'string' ? 0 : value, meta) : null;
    return (
        <div className={`kpi-card ${color}`} style={highlight ? { border: '1px solid var(--accent-amber)' } : {}}>
            <span className="kpi-icon">{icon}</span>
            <div className="kpi-label">{label}</div>
            <div className="kpi-value" style={{ fontSize: 24 }}>{value}</div>
            <div className="kpi-sub">{sub}</div>
            {p !== null && (
                <>
                    <div className="progress-bar" style={{ marginTop: 8 }}>
                        <div className={`progress-fill progress-${color}`} style={{ width: `${p}%` }} />
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
                        {p}% cumplimiento
                    </div>
                </>
            )}
        </div>
    );
}

/* ── Año Anterior side panel ─────────────────────────────────── */
function AntPanel({ items }) {
    return (
        <div className="card" style={{ padding: 16, background: 'var(--bg-secondary)', minWidth: 170 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-amber)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                Año anterior
            </div>
            {items.map((it, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '5px 0', borderBottom: i < items.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{it.label}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{it.value}</span>
                </div>
            ))}
        </div>
    );
}

/* ── Top 5 ranking table ─────────────────────────────────────── */
function Top5Table({ title, data, tipo }) {
    const isGMM = tipo === 'gmm';
    return (
        <div className="card">
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
                {title}
            </div>
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Agente</th>
                            <th>Clave</th>
                            <th>Pólizas</th>
                            <th>{isGMM ? 'Asegurados' : 'Equivalencias'}</th>
                            <th>Prima Nueva</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((a, i) => (
                            <tr key={i}>
                                <td>
                                    <span style={{
                                        width: 22, height: 22, borderRadius: '50%',
                                        background: i < 3 ? 'var(--grad-blue)' : 'rgba(255,255,255,0.08)',
                                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: 11, fontWeight: 700, color: 'white'
                                    }}>{i + 1}</span>
                                </td>
                                <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <div className="avatar" style={{ width: 28, height: 28, fontSize: 11 }}>
                                            {(a.nombre_completo || '?').charAt(0)}
                                        </div>
                                        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
                                            {a.nombre_completo}
                                        </span>
                                    </div>
                                </td>
                                <td><code style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 5px', borderRadius: 4, fontSize: 10 }}>{a.codigo_agente}</code></td>
                                <td><span className="badge badge-blue">{a.polizas_nuevas}</span></td>
                                <td style={{ fontWeight: 700, color: isGMM ? 'var(--accent-emerald)' : 'var(--accent-indigo)' }}>
                                    {isGMM ? fmtNum(a.asegurados || 0) : fmtNum(a.equivalencias || 0)}
                                </td>
                                <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{fmt(a.prima_nueva || 0)}</td>
                            </tr>
                        ))}
                        {data.length === 0 && (
                            <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 20 }}>Sin datos</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [anio, setAnio] = useState(2025);
    const [loading, setLoading] = useState(true);
    const [ramoFilter, setRamoFilter] = useState('todos'); // todos | vida | gmm | autos

    useEffect(() => {
        setLoading(true);
        apiFetch(`/dashboard?anio=${anio}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [anio]);

    const k = data?.kpis || {};
    const mensual = (data?.produccion_mensual || []).map(m => ({
        ...m,
        mes: MESES[m.periodo?.slice(5)] || m.periodo,
        prima_vida: Math.round(m.prima_vida || 0),
        prima_gmm: Math.round(m.prima_gmm || 0),
        prima_autos: Math.round(m.prima_autos || 0),
    }));
    const topGMM = data?.top_gmm || [];
    const topVIDA = data?.top_vida || [];

    /* ── KPI cards for VIDA row ─────────────────────────────── */
    const vidaCards = [
        { label: 'Pólizas Nuevas Vida', value: k.polizas_nuevas_vida || 0, meta: k.meta_vida, icon: '🛡️', color: 'indigo', sub: `Meta: ${k.meta_vida || 0}` },
        { label: 'Pólizas Equivalentes/Vida', value: k.equivalencias_vida || 0, meta: null, icon: '📋', color: 'purple', sub: 'Equivalencias emitidas' },
        { label: 'Prima Nueva Vida', value: fmt(k.prima_nueva_vida || 0), meta: null, icon: '💰', color: 'indigo', sub: `Meta: ${fmt(k.meta_prima_vida || 0)}` },
        { label: 'Prima Subsec. Vida', value: fmt(k.prima_subsecuente_vida || 0), meta: null, icon: '💵', color: 'amber', sub: 'Renovaciones', highlight: true },
        { label: 'Prima Total Vida', value: fmt(k.prima_total_nueva_vida || 0), meta: null, icon: '💎', color: 'cyan', sub: 'total 1er año' },
    ];

    /* ── KPI cards for GMM row ──────────────────────────────── */
    const gmmCards = [
        { label: 'Pólizas Nuevas GMM', value: k.polizas_nuevas_gmm || 0, meta: k.meta_gmm, icon: '🏥', color: 'emerald', sub: `Meta: ${k.meta_gmm || 0}` },
        { label: 'Asegurados Nuevos GMM', value: k.asegurados_nuevos_gmm || 0, meta: null, icon: '👥', color: 'cyan', sub: 'Primer año' },
        { label: 'Prima Nueva GMM', value: fmt(k.prima_nueva_gmm || 0), meta: null, icon: '💵', color: 'emerald', sub: `Meta: ${fmt(k.meta_prima_gmm || 0)}` },
        { label: 'Prima Subsec. GMM', value: fmt(k.prima_subsecuente_gmm || 0), meta: null, icon: '💵', color: 'amber', sub: 'Renovaciones' },
        { label: 'Prima Total GMM', value: fmt((k.prima_nueva_gmm || 0) + (k.prima_subsecuente_gmm || 0)), meta: null, icon: '💎', color: 'cyan', sub: 'Nueva + Renovaciones' },
    ];

    /* ── KPI cards for AUTOS row ─────────────────────────────── */
    const autosCards = [
        { label: 'Pólizas Nuevas Autos', value: k.polizas_nuevas_autos || 0, meta: null, icon: '🚗', color: 'blue', sub: 'Primer año' },
        { label: 'Prima Nueva Autos', value: fmt(k.prima_nueva_autos || 0), meta: null, icon: '💰', color: 'blue', sub: 'Primer año' },
        { label: 'Prima Subsec. Autos', value: fmt(k.prima_subsecuente_autos || 0), meta: null, icon: '💵', color: 'amber', sub: 'Renovaciones' },
        { label: 'Prima Total Autos', value: fmt((k.prima_nueva_autos || 0) + (k.prima_subsecuente_autos || 0)), meta: null, icon: '💎', color: 'cyan', sub: 'Nueva + Renovaciones' },
    ];

    /* ── Año Anterior Data ──────────────────────────────────── */
    const vidaAnt = [
        { label: 'Pólizas', value: k.polizas_vida_ant || 0 },
        { label: 'Equivalencias', value: k.equivalencias_vida_ant || 0 },
        { label: 'Prima Nueva', value: fmt(k.prima_nueva_vida_ant || 0) },
        { label: 'Prima Total Nueva', value: fmt(k.prima_total_nueva_vida_ant || 0) },
    ];
    const gmmAnt = [
        { label: 'Pólizas', value: k.polizas_gmm_ant || 0 },
        { label: 'Asegurados', value: k.asegurados_gmm_ant || 0 },
        { label: 'Prima Nueva', value: fmt(k.prima_nueva_gmm_ant || 0) },
        { label: 'Prima Subsec.', value: fmt(k.prima_subsecuente_gmm_ant || 0) },
    ];
    const autosAnt = [
        { label: 'Pólizas', value: k.polizas_autos_ant || 0 },
        { label: 'Prima Nueva', value: fmt(k.prima_nueva_autos_ant || 0) },
        { label: 'Prima Subsec.', value: fmt(k.prima_subsecuente_autos_ant || 0) },
    ];

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Dashboard de Producción</div>
                        <div className="header-subtitle">
                            Resumen ejecutivo en tiempo real · <strong style={{ color: 'var(--accent-amber)' }}>RANKING POR ASEGURADOS/EQUIV O PRIMA</strong> · <strong style={{ color: 'var(--accent-cyan)' }}>COMPARATIVO MISMO PERIODO AÑO ANTERIOR</strong>
                        </div>
                    </div>
                    <div className="header-right">
                        <select value={anio} onChange={e => setAnio(+e.target.value)} style={{ padding: '7px 12px' }}>
                            {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
                        </select>
                        <span className="badge badge-emerald">🟢 En línea</span>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {loading ? (
                        <div className="kpi-grid">
                            {Array(10).fill(0).map((_, i) => (
                                <div key={i} className="kpi-card" style={{ height: 120 }}>
                                    <div className="loading-skeleton" style={{ height: 12, width: '60%', marginBottom: 16 }} />
                                    <div className="loading-skeleton" style={{ height: 28, width: '40%', marginBottom: 10 }} />
                                    <div className="loading-skeleton" style={{ height: 6 }} />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <>
                            {/* ═══════ VIDA ROW ═══════ */}
                            <div style={{ display: 'flex', gap: 16, marginBottom: 20, alignItems: 'stretch' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${vidaCards.length}, 1fr)`, gap: 14, flex: 1 }}>
                                    {vidaCards.map((kpi, i) => (
                                        <KpiCard key={i} {...kpi} />
                                    ))}
                                </div>
                                <AntPanel items={vidaAnt} />
                            </div>

                            {/* ═══════ GMM ROW ═══════ */}
                            <div style={{ display: 'flex', gap: 16, marginBottom: 28, alignItems: 'stretch' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${gmmCards.length}, 1fr)`, gap: 14, flex: 1 }}>
                                    {gmmCards.map((kpi, i) => (
                                        <KpiCard key={i} {...kpi} />
                                    ))}
                                </div>
                                <AntPanel items={gmmAnt} />
                            </div>

                            {/* ═══════ AUTOS ROW ═══════ */}
                            <div style={{ display: 'flex', gap: 16, marginBottom: 28, alignItems: 'stretch' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${autosCards.length}, 1fr)`, gap: 14, flex: 1 }}>
                                    {autosCards.map((kpi, i) => (
                                        <KpiCard key={i} {...kpi} />
                                    ))}
                                </div>
                                <AntPanel items={autosAnt} />
                            </div>

                            {/* ═══════ TOP 5 RANKINGS ═══════ */}
                            <div className="charts-grid" style={{ marginBottom: 28 }}>
                                <Top5Table title={`🏥 Top 5 GMM — Agentes por Asegurados ${anio}`} data={topGMM} tipo="gmm" />
                                <Top5Table title={`🛡️ Top 5 VIDA — Agentes por Equivalencias ${anio}`} data={topVIDA} tipo="vida" />
                            </div>

                            {/* ═══════ CHARTS: GMM Mensual + VIDA Mensual (MISMO PERIODO) ═══════ */}
                            <div className="charts-grid">
                                {/* GMM mensual — comparativo interanual */}
                                <div className="card">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Producción Mensual {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Pólizas nuevas por ramo</div>
                                        </div>
                                        <span className="badge badge-emerald">■ GMM</span>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={(() => {
                                                const MESES_ALL = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
                                                const actMap = {};
                                                mensual.forEach(m => { actMap[m.mes] = m.polizas_gmm || 0; });
                                                const antData = (data?.produccion_mensual_ant || []);
                                                const antMap = {};
                                                antData.forEach(m => {
                                                    const mesKey = MESES[m.periodo?.slice(5)] || m.periodo;
                                                    antMap[mesKey] = m.polizas_gmm || 0;
                                                });
                                                return MESES_ALL.map(mes => ({
                                                    mes,
                                                    [`${anio}`]: actMap[mes] || 0,
                                                    [`${anio - 1}`]: antMap[mes] || 0,
                                                }));
                                            })()} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                                <Bar dataKey={`${anio}`} name={`${anio}`} fill="#10b981" radius={[4, 4, 0, 0]} />
                                                <Bar dataKey={`${anio - 1}`} name={`${anio - 1}`} fill="rgba(16,185,129,0.3)" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div style={{ textAlign: 'center', marginTop: 12, padding: '6px 16px', background: 'rgba(16,185,129,0.12)', borderRadius: 8 }}>
                                        <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-emerald)', letterSpacing: 1 }}>
                                            {anio - 1} – {anio} MISMO PERIODO
                                        </span>
                                    </div>
                                </div>

                                {/* VIDA mensual — comparativo interanual */}
                                <div className="card">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Producción Mensual {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Pólizas nuevas por ramo</div>
                                        </div>
                                        <span className="badge badge-blue">■ Vida</span>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={(() => {
                                                const MESES_ALL = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
                                                const actMap = {};
                                                mensual.forEach(m => { actMap[m.mes] = m.polizas_vida || 0; });
                                                const antData = (data?.produccion_mensual_ant || []);
                                                const antMap = {};
                                                antData.forEach(m => {
                                                    const mesKey = MESES[m.periodo?.slice(5)] || m.periodo;
                                                    antMap[mesKey] = m.polizas_vida || 0;
                                                });
                                                return MESES_ALL.map(mes => ({
                                                    mes,
                                                    [`${anio}`]: actMap[mes] || 0,
                                                    [`${anio - 1}`]: antMap[mes] || 0,
                                                }));
                                            })()} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                                <Bar dataKey={`${anio}`} name={`${anio}`} fill="#6366f1" radius={[4, 4, 0, 0]} />
                                                <Bar dataKey={`${anio - 1}`} name={`${anio - 1}`} fill="rgba(99,102,241,0.3)" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div style={{ textAlign: 'center', marginTop: 12, padding: '6px 16px', background: 'rgba(99,102,241,0.12)', borderRadius: 8 }}>
                                        <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-indigo)', letterSpacing: 1 }}>
                                            {anio - 1} – {anio} MISMO PERIODO
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* ═══════ TOP AGENTES POR PRIMA NUEVA (con filtro VIDA/GMM) ═══════ */}
                            <div className="card" style={{ marginBottom: 28 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6, flexWrap: 'wrap', gap: 12 }}>
                                    <div>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                                            Top Agentes por Prima Nueva {anio}
                                        </div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Ranking por producción acumulada</div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ fontSize: 11, color: 'var(--accent-rose)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>POR RAMO</span>
                                    </div>
                                </div>

                                {/* ── Filtro bar ── */}
                                <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
                                    <div style={{ display: 'flex', gap: 4, background: 'var(--bg-secondary)', borderRadius: 8, padding: 3 }}>
                                        {[
                                            { key: 'todos', label: 'Todos', icon: '📊' },
                                            { key: 'vida', label: 'Vida', icon: '🛡️' },
                                            { key: 'gmm', label: 'GMM', icon: '🏥' },
                                            { key: 'autos', label: 'Autos', icon: '🚗' },
                                        ].map(f => (
                                            <button key={f.key}
                                                onClick={() => setRamoFilter(f.key)}
                                                style={{
                                                    padding: '6px 14px', fontSize: 12, fontWeight: 600, borderRadius: 6,
                                                    border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5,
                                                    background: ramoFilter === f.key ? 'var(--grad-blue)' : 'transparent',
                                                    color: ramoFilter === f.key ? 'white' : 'var(--text-muted)',
                                                    transition: 'all 0.2s',
                                                }}
                                            >
                                                {f.icon} {f.label}
                                            </button>
                                        ))}
                                    </div>
                                    <div style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                                        FILTROS POR PERIODO, AL MES, AL AÑO ETC O POR RANGO
                                    </div>
                                </div>

                                {/* ── Sección AVANCE VS PRESUPUESTO ── */}
                                {ramoFilter !== 'todos' && (
                                    <div style={{ display: 'flex', gap: 16, marginBottom: 16, padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: 10 }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>AVANCE VS PRESUPUESTO</div>
                                            <div className="progress-bar" style={{ height: 8 }}>
                                                <div className={`progress-fill progress-${ramoFilter === 'vida' ? 'indigo' : ramoFilter === 'gmm' ? 'emerald' : 'blue'}`}
                                                    style={{ width: `${ramoFilter === 'vida' ? pct(k.polizas_nuevas_vida, k.meta_vida) : ramoFilter === 'gmm' ? pct(k.polizas_nuevas_gmm, k.meta_gmm) : pct(k.polizas_nuevas_autos, k.meta_autos)}%` }} />
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
                                                {ramoFilter === 'vida'
                                                    ? `${k.polizas_nuevas_vida} / ${k.meta_vida} pólizas (${pct(k.polizas_nuevas_vida, k.meta_vida)}%)`
                                                    : ramoFilter === 'gmm'
                                                    ? `${k.polizas_nuevas_gmm} / ${k.meta_gmm} pólizas (${pct(k.polizas_nuevas_gmm, k.meta_gmm)}%)`
                                                    : `${k.polizas_nuevas_autos || 0} pólizas nuevas autos`
                                                }
                                            </div>
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>PRIMA VS META</div>
                                            <div className="progress-bar" style={{ height: 8 }}>
                                                <div className={`progress-fill progress-${ramoFilter === 'vida' ? 'indigo' : ramoFilter === 'gmm' ? 'emerald' : 'blue'}`}
                                                    style={{ width: `${ramoFilter === 'vida' ? pct(k.prima_nueva_vida, k.meta_prima_vida) : ramoFilter === 'gmm' ? pct(k.prima_nueva_gmm, k.meta_prima_gmm) : pct(k.prima_nueva_autos, k.meta_prima_autos)}%` }} />
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
                                                {ramoFilter === 'vida'
                                                    ? `${fmt(k.prima_nueva_vida)} / ${fmt(k.meta_prima_vida)} (${pct(k.prima_nueva_vida, k.meta_prima_vida)}%)`
                                                    : ramoFilter === 'gmm'
                                                    ? `${fmt(k.prima_nueva_gmm)} / ${fmt(k.meta_prima_gmm)} (${pct(k.prima_nueva_gmm, k.meta_prima_gmm)}%)`
                                                    : `${fmt(k.prima_nueva_autos || 0)} prima nueva autos`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div className="table-container">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>#</th>
                                                <th>Agente</th>
                                                <th>Pólizas Nuevas</th>
                                                {(ramoFilter === 'todos' || ramoFilter === 'vida') && <th>Equivalentes</th>}
                                                {(ramoFilter === 'todos' || ramoFilter === 'gmm') && <th>Asegurados</th>}
                                                <th>Prima Venta Nueva</th>
                                                <th>Prima Total</th>
                                                <th>Participación</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(data?.top_agentes || []).map((a, i) => {
                                                const totalPrima = (data?.top_agentes || []).reduce((s, ag) => s + (ag.prima_total || 0), 0);
                                                const participacion = totalPrima > 0 ? ((a.prima_total || 0) / totalPrima * 100).toFixed(1) : 0;
                                                return (
                                                    <tr key={i}>
                                                        <td>
                                                            <span style={{ width: 24, height: 24, borderRadius: '50%', background: i < 3 ? 'var(--grad-blue)' : 'rgba(255,255,255,0.08)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: 'white' }}>
                                                                {i + 1}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                                <div className="avatar">{(a.nombre_completo || '?').charAt(0)}</div>
                                                                <div>
                                                                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{a.nombre_completo}</div>
                                                                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{a.codigo_agente} · {a.oficina}</div>
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <span className="badge badge-blue">{a.polizas_nuevas || 0}</span>
                                                        </td>
                                                        {(ramoFilter === 'todos' || ramoFilter === 'vida') && (
                                                            <td style={{ fontWeight: 700, color: 'var(--accent-indigo)' }}>
                                                                {fmtNum(a.equivalencias || 0)}
                                                            </td>
                                                        )}
                                                        {(ramoFilter === 'todos' || ramoFilter === 'gmm') && (
                                                            <td style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                                                                {fmtNum(a.asegurados || 0)}
                                                            </td>
                                                        )}
                                                        <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{fmt(a.prima_nueva || 0)}</td>
                                                        <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{fmt(a.prima_total || 0)}</td>
                                                        <td>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                                <div className="progress-bar" style={{ width: 80, marginTop: 0 }}>
                                                                    <div className="progress-fill progress-blue" style={{ width: `${participacion}%`, height: '100%' }} />
                                                                </div>
                                                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{participacion}%</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
