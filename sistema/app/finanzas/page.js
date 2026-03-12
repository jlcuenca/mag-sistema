'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';
import {
    BarChart, Bar, LineChart, Line, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    ReferenceLine, ComposedChart,
} from 'recharts';

const TABS = ['ingresos', 'presupuesto', 'tendencia', 'proyeccion'];

function fmt(n) {
    if (n == null) return '$0';
    if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}
function fmtF(n) {
    return `$${(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

const TEND_COLORS = { arriba: '#10b981', abajo: '#ef4444', estable: '#eab308' };
const TEND_ICONS = { arriba: '📈', abajo: '📉', estable: '➡️' };

export default function Finanzas() {
    const [data, setData] = useState(null);
    const [anio, setAnio] = useState(2025);
    const [ramo, setRamo] = useState('');
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('ingresos');

    useEffect(() => {
        setLoading(true);
        const p = new URLSearchParams({ anio });
        if (ramo) p.set('ramo', ramo);
        apiFetch(`/finanzas?${p}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [anio, ramo]);

    const res = data?.resumen || {};
    const ie = data?.ingresos_egresos || [];
    const pres = data?.presupuesto || [];
    const tend = data?.tendencia || [];
    const proy = data?.proyeccion || {};

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Dashboard Financiero</div>
                        <div className="header-subtitle">Ingresos vs Egresos · Proyecciones · Presupuesto IDEAL</div>
                    </div>
                    <div className="header-right">
                        <select value={anio} onChange={e => setAnio(+e.target.value)} style={{ padding: '7px 12px' }}>
                            {[2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
                        </select>
                        <select value={ramo} onChange={e => setRamo(e.target.value)} style={{ padding: '7px 12px' }}>
                            <option value="">Todos ramos</option>
                            <option value="vida">Vida</option>
                            <option value="gmm">GMM</option>
                        </select>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {loading ? (
                        <div className="kpi-grid">
                            {Array(6).fill(0).map((_, i) => (
                                <div key={i} className="kpi-card" style={{ height: 120 }}>
                                    <div className="loading-skeleton" style={{ height: 14, width: '50%', marginBottom: 14 }} />
                                    <div className="loading-skeleton" style={{ height: 28, width: '40%' }} />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <>
                            {/* ═══ INDICADORES ESTRELLA ═══ */}
                            <div className="card" style={{ marginBottom: 20, borderTop: '3px solid var(--accent-amber)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--accent-amber)', textTransform: 'uppercase', letterSpacing: 1 }}>⭐ Indicadores Estrella</div>
                                </div>
                                <div className="table-container">
                                    <table style={{ fontSize: 12 }}>
                                        <tbody>
                                            <tr><td style={{ fontWeight: 600 }}>Recluta productiva</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-emerald)' }}>{data?.indicadores_estrella?.recluta_productiva ?? 11}</td></tr>
                                            <tr><td style={{ fontWeight: 600 }}>Pólizas de Vida 1er. Año equivalentes</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-indigo)' }}>{data?.indicadores_estrella?.polizas_equivalentes ?? '341.8'}</td></tr>
                                            <tr><td style={{ fontWeight: 600 }}>Número de agentes ALFA adicionales</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-blue)' }}>{data?.indicadores_estrella?.agentes_alfa ?? 13}</td></tr>
                                            <tr><td style={{ fontWeight: 600 }}>Porcentaje de plantilla ALFA</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-cyan)' }}>{data?.indicadores_estrella?.pct_plantilla_alfa ?? '7.03%'}</td></tr>
                                            <tr><td style={{ fontWeight: 600 }}>Asegurados nuevos GMI</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-emerald)' }}>{data?.indicadores_estrella?.asegurados_nuevos_gmi ?? '1,026'}</td></tr>
                                            <tr><td style={{ fontWeight: 600 }}>Crecimiento en cartera individual</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-rose)' }}>{data?.indicadores_estrella?.crecimiento_cartera ?? '8.01%'}</td></tr>
                                            <tr><td style={{ fontWeight: 600 }}>Agentes ganadores bonus BIC</td><td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-amber)' }}>{data?.indicadores_estrella?.ganadores_bic ?? 55}</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* ── KPI CARDS (renombrados según SUGERIDA) ── */}
                            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                                <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-emerald)' }}>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>💰</div>
                                    <div className="kpi-value" style={{ color: 'var(--accent-emerald)', fontSize: 20 }}>{fmt(res.prima_cobrada_total)}</div>
                                    <div className="kpi-label">Prima Cobrada</div>
                                    <div style={{ fontSize: 9, color: 'var(--accent-amber)', marginTop: 4, textTransform: 'uppercase', fontWeight: 700, letterSpacing: 1 }}>RECLUTA PRODUCTIVA</div>
                                </div>
                                <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-rose)' }}>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>💸</div>
                                    <div className="kpi-value" style={{ color: 'var(--accent-rose)', fontSize: 20 }}>{fmt(res.comision_total)}</div>
                                    <div className="kpi-label">Comisiones</div>
                                    <div style={{ fontSize: 9, color: 'var(--accent-cyan)', marginTop: 4, textTransform: 'uppercase', fontWeight: 700 }}>PÓLIZAS EQUIVALENTES</div>
                                </div>
                                <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-blue)' }}>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>📊</div>
                                    <div className="kpi-value" style={{ color: 'var(--accent-blue)', fontSize: 20 }}>{fmt(res.margen_total)}</div>
                                    <div className="kpi-label">Margen ({res.pct_margen}%)</div>
                                    <div style={{ fontSize: 9, color: 'var(--accent-cyan)', marginTop: 4, textTransform: 'uppercase', fontWeight: 700 }}>ASEGURADOS NUEVOS</div>
                                </div>
                                <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-cyan)' }}>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>🎯</div>
                                    <div className="kpi-value" style={{ color: 'var(--accent-cyan)', fontSize: 20 }}>{res.pct_cumplimiento}%</div>
                                    <div className="kpi-label">Cumplimiento Meta</div>
                                    <div style={{ fontSize: 9, color: 'var(--accent-amber)', marginTop: 4, textTransform: 'uppercase', fontWeight: 700 }}>AGENTES ALFA Y % VS PLANTILLA</div>
                                </div>
                                <div className="kpi-card" style={{ borderTop: `3px solid ${TEND_COLORS[proy.tendencia]}` }}>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>{TEND_ICONS[proy.tendencia]}</div>
                                    <div className="kpi-value" style={{ color: TEND_COLORS[proy.tendencia], fontSize: 20 }}>{fmt(proy.proyeccion_anual)}</div>
                                    <div className="kpi-label">Proyección Cierre</div>
                                    <div style={{ fontSize: 9, color: 'var(--accent-rose)', marginTop: 4, textTransform: 'uppercase', fontWeight: 700 }}>*CRECIMIENTO DE CARTERA LP</div>
                                </div>
                                <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-amber)' }}>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>📅</div>
                                    <div className="kpi-value" style={{ fontSize: 16, color: res.variacion_interanual >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                                        {res.variacion_interanual >= 0 ? '+' : ''}{res.variacion_interanual}%
                                    </div>
                                    <div className="kpi-label">vs {anio - 1}</div>
                                    <div style={{ fontSize: 9, color: 'var(--accent-amber)', marginTop: 4, textTransform: 'uppercase', fontWeight: 700 }}>GANADORES DE BIC</div>
                                </div>
                            </div>

                            {/* ── TABS ── */}
                            <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--bg-card)', padding: 4, borderRadius: 12, width: 'fit-content', border: '1px solid var(--border)' }}>
                                {TABS.map(t => (
                                    <button key={t} onClick={() => setTab(t)}
                                        className={`btn ${tab === t ? 'btn-primary' : 'btn-ghost'}`}
                                        style={{ textTransform: 'capitalize', padding: '8px 18px' }}>
                                        {t === 'ingresos' ? '💰 Ingresos vs Egresos' : t === 'presupuesto' ? '🎯 Presupuesto IDEAL' :
                                            t === 'tendencia' ? '📈 Tendencia' : '🔮 Proyección'}
                                    </button>
                                ))}
                            </div>

                            {/* ── TAB: INGRESOS VS EGRESOS (4.1) ── */}
                            {tab === 'ingresos' && (
                                <div className="charts-grid">
                                    <div className="card" style={{ gridColumn: 'span 2' }}>
                                        <div style={{ marginBottom: 20 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Ingresos vs Egresos — {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Prima cobrada vs comisiones pagadas</div>
                                        </div>
                                        <div className="chart-container" style={{ height: 320 }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ComposedChart data={ie} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                                    <Bar dataKey="prima_cobrada" name="Ingreso (Prima)" fill="#10b981" radius={[4, 4, 0, 0]} />
                                                    <Bar dataKey="comision_pagada" name="Egreso (Comisión)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                                                    <Line type="monotone" dataKey="margen" name="Margen" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3 }} />
                                                </ComposedChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    <div className="card">
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>% Margen por Mes</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Eficiencia operativa mensual</div>
                                        </div>
                                        <div className="chart-container">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={ie} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <ReferenceLine y={90} stroke="#22c55e" strokeDasharray="5 5" label={{ value: '90%', fill: '#22c55e', fontSize: 10 }} />
                                                    <Area type="monotone" dataKey="pct_margen" name="% Margen" stroke="#6366f1" fill="rgba(99,102,241,0.2)" strokeWidth={2} />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    <div className="card">
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Composición de Prima</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Nueva vs Subsecuente vs Cancelaciones</div>
                                        </div>
                                        <div className="chart-container">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={ie} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <Legend wrapperStyle={{ fontSize: 11 }} />
                                                    <Bar dataKey="prima_nueva" name="Nueva" stackId="a" fill="#3b82f6" />
                                                    <Bar dataKey="prima_subsecuente" name="Subsecuente" stackId="a" fill="#06b6d4" />
                                                    <Bar dataKey="cancelaciones" name="Cancelaciones" fill="rgba(239,68,68,0.4)" />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* ── TAB: PRESUPUESTO IDEAL (4.3) ── */}
                            {tab === 'presupuesto' && (
                                <div className="charts-grid">
                                    <div className="card" style={{ gridColumn: 'span 2' }}>
                                        <div style={{ marginBottom: 20 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                                                Presupuesto IDEAL {anio} — Acumulado
                                            </div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Meta mensual vs Real con acumulados</div>
                                        </div>
                                        <div className="chart-container" style={{ height: 320 }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ComposedChart data={pres} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis yAxisId="left" tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <YAxis yAxisId="right" orientation="right" tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                                    <Bar yAxisId="left" dataKey="meta" name="Meta Mensual" fill="rgba(99,102,241,0.3)" radius={[4, 4, 0, 0]} />
                                                    <Bar yAxisId="left" dataKey="real" name="Real Mensual" fill="#10b981" radius={[4, 4, 0, 0]} />
                                                    <Line yAxisId="right" type="monotone" dataKey="acumulado_meta" name="Acum. Meta" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                                                    <Line yAxisId="right" type="monotone" dataKey="acumulado_real" name="Acum. Real" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3, fill: '#3b82f6' }} />
                                                </ComposedChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    <div className="card">
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Variación vs Meta</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Desviación % mensual</div>
                                        </div>
                                        <div className="chart-container">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={pres} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis tickFormatter={v => `${v}%`} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
                                                    <Bar dataKey="variacion" name="Variación %" radius={[4, 4, 0, 0]}>
                                                        {pres.map((entry, i) => (
                                                            <rect key={i} fill={entry.variacion >= 0 ? '#10b981' : '#ef4444'} />
                                                        ))}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    {/* Monthly table */}
                                    <div className="card">
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Detalle Mensual</div>
                                        </div>
                                        <div className="table-container" style={{ maxHeight: 260, overflow: 'auto' }}>
                                            <table style={{ fontSize: 12 }}>
                                                <thead>
                                                    <tr>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)' }}>Mes</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', textAlign: 'right' }}>Meta</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', textAlign: 'right' }}>Real</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', textAlign: 'right' }}>Var%</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {pres.map((p, i) => (
                                                        <tr key={i}>
                                                            <td>{p.mes}</td>
                                                            <td style={{ textAlign: 'right' }}>{fmt(p.meta)}</td>
                                                            <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(p.real)}</td>
                                                            <td style={{ textAlign: 'right', fontWeight: 700, color: p.variacion >= 0 ? '#10b981' : '#ef4444' }}>
                                                                {p.variacion >= 0 ? '+' : ''}{p.variacion}%
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* ── TAB: TENDENCIA INTERANUAL (4.4) ── */}
                            {tab === 'tendencia' && (
                                <div className="charts-grid">
                                    <div className="card" style={{ gridColumn: 'span 2' }}>
                                        <div style={{ marginBottom: 20 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                                                Tendencia: {anio - 1} vs {anio} vs Meta
                                            </div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Prima mensual comparativa</div>
                                        </div>
                                        <div className="chart-container" style={{ height: 320 }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart data={tend} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                                    <Line type="monotone" dataKey="anio_anterior" name={`${anio - 1}`} stroke="#94a3b8" strokeWidth={2}
                                                        strokeDasharray="5 5" dot={{ r: 3, fill: '#94a3b8' }} />
                                                    <Line type="monotone" dataKey="anio_actual" name={`${anio}`} stroke="#3b82f6" strokeWidth={2.5}
                                                        dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} />
                                                    <Line type="monotone" dataKey="meta" name="Meta IDEAL" stroke="#f59e0b" strokeWidth={1.5}
                                                        strokeDasharray="8 4" dot={false} />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    <div className="card" style={{ gridColumn: 'span 2' }}>
                                        <div style={{ marginBottom: 20 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                                                Acumulado: {anio - 1} vs {anio}
                                            </div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Progreso de prima acumulada con banda de meta</div>
                                        </div>
                                        <div className="chart-container" style={{ height: 320 }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={tend} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                                    <Area type="monotone" dataKey="acum_meta" name="Meta Acumulada" stroke="#f59e0b" fill="rgba(245,158,11,0.08)" strokeWidth={1.5} strokeDasharray="5 5" />
                                                    <Area type="monotone" dataKey="acum_anterior" name={`Acum ${anio - 1}`} stroke="#94a3b8" fill="rgba(148,163,184,0.1)" strokeWidth={2} />
                                                    <Area type="monotone" dataKey="acum_actual" name={`Acum ${anio}`} stroke="#3b82f6" fill="rgba(59,130,246,0.15)" strokeWidth={2.5} />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* ── TAB: PROYECCIÓN (4.2) ── */}
                            {tab === 'proyeccion' && (
                                <div className="charts-grid">
                                    <div className="card" style={{ gridColumn: 'span 2' }}>
                                        <div style={{ marginBottom: 24 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Proyección de Cierre {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Basada en tendencia de {proy.meses_transcurridos} meses de datos</div>
                                        </div>

                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
                                            <div style={{ background: 'rgba(16,185,129,0.1)', padding: '20px', borderRadius: 14, textAlign: 'center' }}>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Prima Acumulada</div>
                                                <div style={{ fontSize: 22, fontWeight: 800, color: '#10b981' }}>{fmt(proy.prima_acumulada)}</div>
                                                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{proy.meses_transcurridos} meses</div>
                                            </div>
                                            <div style={{ background: 'rgba(59,130,246,0.1)', padding: '20px', borderRadius: 14, textAlign: 'center' }}>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Promedio Mensual</div>
                                                <div style={{ fontSize: 22, fontWeight: 800, color: '#3b82f6' }}>{fmt(proy.promedio_mensual)}</div>
                                            </div>
                                            <div style={{ background: `${TEND_COLORS[proy.tendencia]}1a`, padding: '20px', borderRadius: 14, textAlign: 'center' }}>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Proyección Anual</div>
                                                <div style={{ fontSize: 22, fontWeight: 800, color: TEND_COLORS[proy.tendencia] }}>{fmt(proy.proyeccion_anual)}</div>
                                                <div style={{ fontSize: 11, marginTop: 4 }}>
                                                    <span style={{ color: TEND_COLORS[proy.tendencia] }}>{TEND_ICONS[proy.tendencia]} {proy.tendencia.toUpperCase()}</span>
                                                </div>
                                            </div>
                                            <div style={{ background: 'rgba(245,158,11,0.1)', padding: '20px', borderRadius: 14, textAlign: 'center' }}>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Meta Anual</div>
                                                <div style={{ fontSize: 22, fontWeight: 800, color: '#f59e0b' }}>{fmt(proy.meta_anual)}</div>
                                                <div style={{ fontSize: 11, marginTop: 4, fontWeight: 700, color: proy.variacion_vs_meta >= 0 ? '#10b981' : '#ef4444' }}>
                                                    {proy.variacion_vs_meta >= 0 ? '▲' : '▼'} {proy.variacion_vs_meta}%
                                                </div>
                                            </div>
                                        </div>

                                        {/* Confidence bar */}
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Confianza del modelo (R²)</span>
                                                <span style={{ fontSize: 12, fontWeight: 700, color: proy.confianza > 0.7 ? '#10b981' : proy.confianza > 0.4 ? '#eab308' : '#ef4444' }}>
                                                    {(proy.confianza * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                            <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 6, height: 8, overflow: 'hidden' }}>
                                                <div style={{
                                                    width: `${proy.confianza * 100}%`,
                                                    height: '100%',
                                                    borderRadius: 6,
                                                    background: proy.confianza > 0.7 ? 'linear-gradient(90deg, #10b981, #22d3ee)' : proy.confianza > 0.4 ? 'linear-gradient(90deg, #eab308, #f59e0b)' : 'linear-gradient(90deg, #ef4444, #f97316)',
                                                    transition: 'width 0.8s ease',
                                                }} />
                                            </div>
                                        </div>

                                        {/* Projection visualization */}
                                        <div className="chart-container" style={{ height: 280 }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ComposedChart data={pres} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                                    <Bar dataKey="real" name="Real" fill="#10b981" radius={[4, 4, 0, 0]} />
                                                    <Line type="monotone" dataKey="acumulado_real" name="Acum. Real" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3 }} />
                                                    <Line type="monotone" dataKey="acumulado_meta" name="Acum. Meta" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
                                                    <ReferenceLine y={proy.meta_anual} stroke="#f59e0b" strokeDasharray="8 4"
                                                        label={{ value: `Meta: ${fmt(proy.meta_anual)}`, fill: '#f59e0b', fontSize: 10, position: 'right' }} />
                                                </ComposedChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* ═══ TABLA DE METAS POR RAMO ═══ */}
                            <div className="card" style={{ marginTop: 28, borderTop: '3px solid var(--accent-blue)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                    <div>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Metas por Ramo — {anio}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Meta prorrateada para ser Año TOP y Año ATL</div>
                                    </div>
                                </div>
                                <div className="table-container">
                                    <table style={{ fontSize: 12 }}>
                                        <thead>
                                            <tr>
                                                <th rowSpan={2} style={{ background: 'var(--bg-card)', zIndex: 2 }}></th>
                                                <th colSpan={2} style={{ textAlign: 'center', background: 'rgba(99,102,241,0.12)', color: 'var(--accent-indigo)' }}>VIDA</th>
                                                <th colSpan={2} style={{ textAlign: 'center', background: 'rgba(16,185,129,0.12)', color: 'var(--accent-emerald)' }}>SALUD</th>
                                                <th colSpan={2} style={{ textAlign: 'center', background: 'rgba(59,130,246,0.12)', color: 'var(--accent-blue)' }}>AUTOS</th>
                                                <th colSpan={2} style={{ textAlign: 'center', background: 'rgba(245,158,11,0.12)', color: 'var(--accent-amber)' }}>DAÑOS</th>
                                                <th colSpan={2} style={{ textAlign: 'center', background: 'rgba(239,68,68,0.12)', color: 'var(--accent-rose)' }}>PRIMAS TOTALES</th>
                                            </tr>
                                            <tr>
                                                <th style={{ textAlign: 'right', background: 'rgba(99,102,241,0.06)' }}>Pólizas</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(99,102,241,0.06)' }}>Prima Pagada</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(16,185,129,0.06)' }}>Aseg Nuevos</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(16,185,129,0.06)' }}>Prima Pagada</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(59,130,246,0.06)' }}>Crecimiento</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(59,130,246,0.06)' }}>Prima Pagada</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(245,158,11,0.06)' }}>Crecimiento</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(245,158,11,0.06)' }}>Prima Pagada</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(239,68,68,0.06)' }}>Crecimiento</th>
                                                <th style={{ textAlign: 'right', background: 'rgba(239,68,68,0.06)' }}>Prima Pagada</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>Meta Año TOP</td>
                                                <td style={{ textAlign: 'right' }}>48</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(2000000)}</td>
                                                <td style={{ textAlign: 'right' }}>100.0</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(830000)}</td>
                                                <td style={{ textAlign: 'right' }}>10%</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(5000000)}</td>
                                                <td style={{ textAlign: 'right' }}>5%</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(10000000)}</td>
                                                <td style={{ textAlign: 'right' }}>5%</td>
                                                <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-emerald)' }}>{fmt(21000000)}</td>
                                            </tr>
                                            <tr>
                                                <td style={{ fontWeight: 700, color: 'var(--accent-blue)' }}>Meta Año ATL</td>
                                                <td style={{ textAlign: 'right' }}>24</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(500000)}</td>
                                                <td style={{ textAlign: 'right' }}>50.0</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(415000)}</td>
                                                <td style={{ textAlign: 'right' }}>15%</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(1500000)}</td>
                                                <td style={{ textAlign: 'right' }}>5%</td>
                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(5000000)}</td>
                                                <td style={{ textAlign: 'right' }}>15%</td>
                                                <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--accent-blue)' }}>{fmt(10500000)}</td>
                                            </tr>
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
