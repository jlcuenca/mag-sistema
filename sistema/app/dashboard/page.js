'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, MESES } from '@/lib/api';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#f43f5e', '#06b6d4'];

function fmt(n) {
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n?.toFixed(0) || 0}`;
}

function pct(val, meta) {
    if (!meta) return 0;
    return Math.min(100, Math.round((val / meta) * 100));
}

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [anio, setAnio] = useState(2025);
    const [loading, setLoading] = useState(true);

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
    }));
    const gamas = data?.distribucion_gama || [];
    const topAgentes = data?.top_agentes || [];

    const kpiCards = [
        { label: 'Polizas Nuevas Vida', value: k.polizas_nuevas_vida || 0, meta: k.meta_vida, icon: '🏥', color: 'blue', sub: `Meta: ${k.meta_vida || 0}` },
        { label: 'Prima Nueva Vida', value: fmt(k.prima_nueva_vida || 0), meta: null, icon: '💰', color: 'indigo', sub: `Meta: ${fmt(k.meta_prima_vida || 0)}` },
        { label: 'Polizas Nuevas GMM', value: k.polizas_nuevas_gmm || 0, meta: k.meta_gmm, icon: '🏥', color: 'emerald', sub: `Meta: ${k.meta_gmm || 0}` },
        { label: 'Asegurados Nuevos GMM', value: k.asegurados_nuevos_gmm || 0, meta: null, icon: '👥', color: 'cyan', sub: 'Primer año' },
        { label: 'Prima Nueva GMM', value: fmt(k.prima_nueva_gmm || 0), meta: null, icon: '💵', color: 'purple', sub: `Meta: ${fmt(k.meta_prima_gmm || 0)}` },
        { label: 'Prima Subsec. Vida', value: fmt(k.prima_subsecuente_vida || 0), meta: null, icon: '🔄', color: 'amber', sub: 'Renovaciones' },
        { label: 'Prima Subsec. GMM', value: fmt(k.prima_subsecuente_gmm || 0), meta: null, icon: '🔁', color: 'orange', sub: 'Renovaciones' },
        { label: 'Canceladas', value: k.polizas_canceladas || 0, meta: null, icon: '⚠️', color: 'rose', sub: 'Total polizas' },
    ];

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Dashboard de Producción</div>
                        <div className="header-subtitle">Resumen ejecutivo en tiempo real</div>
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
                            {Array(8).fill(0).map((_, i) => (
                                <div key={i} className="kpi-card" style={{ height: 120 }}>
                                    <div className="loading-skeleton" style={{ height: 12, width: '60%', marginBottom: 16 }} />
                                    <div className="loading-skeleton" style={{ height: 28, width: '40%', marginBottom: 10 }} />
                                    <div className="loading-skeleton" style={{ height: 6 }} />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <>
                            {/* KPI Grid */}
                            <div className="kpi-grid">
                                {kpiCards.map((kpi, i) => (
                                    <div key={i} className={`kpi-card ${kpi.color}`}>
                                        <span className="kpi-icon">{kpi.icon}</span>
                                        <div className="kpi-label">{kpi.label}</div>
                                        <div className="kpi-value">{kpi.value}</div>
                                        <div className="kpi-sub">{kpi.sub}</div>
                                        {kpi.meta > 0 && (
                                            <>
                                                <div className="progress-bar" style={{ marginTop: 10 }}>
                                                    <div
                                                        className={`progress-fill progress-${kpi.color}`}
                                                        style={{ width: `${pct(typeof kpi.value === 'string' ? 0 : kpi.value, kpi.meta)}%` }}
                                                    />
                                                </div>
                                                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                                                    {pct(typeof kpi.value === 'string' ? 0 : kpi.value, kpi.meta)}% cumplimiento
                                                </div>
                                            </>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Gráficas principales */}
                            <div className="charts-grid-wide">
                                {/* Producción mensual */}
                                <div className="card">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Producción Mensual {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Pólizas nuevas por ramo</div>
                                        </div>
                                        <span className="badge badge-blue">📊 Barras</span>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={mensual} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                                <Bar dataKey="polizas_vida" name="Vida" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                                <Bar dataKey="polizas_gmm" name="GMM" fill="#10b981" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Distribución por gama */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>GMM por Gama</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Distribución de pólizas</div>
                                    </div>
                                    <div style={{ height: 220, display: 'flex', gap: 16, alignItems: 'center' }}>
                                        <ResponsiveContainer width="60%" height="100%">
                                            <PieChart>
                                                <Pie data={gamas} dataKey="total" cx="50%" cy="50%" outerRadius={80} innerRadius={40}>
                                                    {gamas.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                                </Pie>
                                                <Tooltip contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                            </PieChart>
                                        </ResponsiveContainer>
                                        <div style={{ flex: 1 }}>
                                            {gamas.map((g, i) => (
                                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                                                    <div style={{ width: 10, height: 10, borderRadius: 3, background: COLORS[i % COLORS.length], flexShrink: 0 }} />
                                                    <div>
                                                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{g.gama}</div>
                                                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{g.total} pólizas</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Primas mensuales */}
                            <div className="card" style={{ marginBottom: 28 }}>
                                <div style={{ marginBottom: 20 }}>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Prima Nueva por Mes — {anio}</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Comparativo Vida vs GMM en MXN</div>
                                </div>
                                <div className="chart-container">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={mensual} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                            <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}K`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <Tooltip formatter={v => fmt(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                            <Legend wrapperStyle={{ fontSize: 12 }} />
                                            <Line type="monotone" dataKey="prima_vida" name="Prima Vida" stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 4 }} activeDot={{ r: 6 }} />
                                            <Line type="monotone" dataKey="prima_gmm" name="Prima GMM" stroke="#10b981" strokeWidth={2.5} dot={{ fill: '#10b981', r: 4 }} activeDot={{ r: 6 }} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Top Agentes */}
                            <div className="card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                                    <div>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Top Agentes por Prima Nueva {anio}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Ranking por producción acumulada</div>
                                    </div>
                                </div>
                                <div className="table-container">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>#</th>
                                                <th>Agente</th>
                                                <th>Código</th>
                                                <th>Oficina</th>
                                                <th>Pólizas Nuevas</th>
                                                <th>Prima Total</th>
                                                <th>Participación</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {topAgentes.map((a, i) => {
                                                const totalPrima = topAgentes.reduce((s, ag) => s + (ag.prima_total || 0), 0);
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
                                                                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                                                                    {a.nombre_completo}
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td><code style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 11 }}>{a.codigo_agente}</code></td>
                                                        <td>{a.oficina}</td>
                                                        <td>
                                                            <span className="badge badge-blue">{a.polizas_nuevas || 0}</span>
                                                        </td>
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
