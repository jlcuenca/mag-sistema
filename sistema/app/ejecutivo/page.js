'use client';
import { useState, useEffect, useMemo } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, API_URL } from '@/lib/api';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS_SEG = { ALFA: '#6366f1', BETA: '#10b981', OMEGA: '#f59e0b', 'SIN SEGMENTO': '#64748b' };
const TABS = ['directiva', 'operativa'];

function fmt(n) {
    if (n == null) return '$0';
    if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}
function fmtFull(n) {
    if (n == null) return '$0';
    return `$${n.toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}
function varClass(v) {
    if (v > 0) return 'kpi-trend up';
    if (v < 0) return 'kpi-trend down';
    return 'kpi-trend';
}
function varIcon(v) { return v > 0 ? '▲' : v < 0 ? '▼' : '●'; }

export default function Ejecutivo() {
    const [data, setData] = useState(null);
    const [anio, setAnio] = useState(2025);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('directiva');
    const [segFiltro, setSegFiltro] = useState('');
    const [topN, setTopN] = useState(0);
    const [busqueda, setBusqueda] = useState('');
    const [sortOp, setSortOp] = useState('prima'); // 'aseg' | 'prima'

    useEffect(() => {
        setLoading(true);
        const params = new URLSearchParams({ anio });
        if (segFiltro) params.set('segmento', segFiltro);
        if (topN > 0) params.set('top_n', topN);
        apiFetch(`/dashboard/ejecutivo?${params}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [anio, segFiltro, topN]);

    const cg = data?.comparativo_gmm || {};
    const cv = data?.comparativo_vida || {};
    const ca = data?.comparativo_autos || {};
    const segs = data?.segmentos || [];
    const agentes = useMemo(() => {
        if (!data?.agentes_operativo) return [];
        let list = data.agentes_operativo;
        if (busqueda) {
            const q = busqueda.toLowerCase();
            list = list.filter(a =>
                (a.nombre || '').toLowerCase().includes(q) ||
                (a.clave || '').toLowerCase().includes(q)
            );
        }
        // Sort
        if (sortOp === 'aseg') {
            list = [...list].sort((a, b) => ((b.polizas_gmm || 0) + (b.polizas_vida || 0)) - ((a.polizas_gmm || 0) + (a.polizas_vida || 0)));
        } else {
            list = [...list].sort((a, b) => (b.prima_pagada_total || 0) - (a.prima_pagada_total || 0));
        }
        return list;
    }, [data, busqueda, sortOp]);

    // Export to CSV/Excel
    function exportExcel() {
        if (!agentes.length) return;
        const headers = ['#', 'Agente', 'Clave', 'Segmento', 'Gestión', 'Pol Vida', 'Equiv', 'Prima Vida', 'Pol GMM', 'Aseg', 'Prima GMM', 'Total', 'Crec Vida', 'Crec GMM'];
        const rows = agentes.map((a, i) => [
            i + 1, a.nombre, a.clave, a.segmento_agrupado, a.oficina,
            a.polizas_vida, a.equivalencias_vida || 0, a.prima_pagada_vida,
            a.polizas_gmm, a.asegurados_gmm || a.polizas_gmm, a.prima_pagada_gmm,
            a.prima_pagada_total,
            `${(a.vida_crecimiento || 0).toFixed(1)}%`,
            `${(a.gmm_crecimiento || 0).toFixed(1)}%`,
        ]);
        const csv = [headers.join(','), ...rows.map(r => r.map(v => `"${v}"`).join(','))].join('\n');
        const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `operativo_${anio}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    }

    // Descargar detalle de pólizas (raw data para cruce)
    function downloadPolizasDetalle(ramoFiltro) {
        const params = new URLSearchParams({ anio });
        if (ramoFiltro) params.set('ramo', ramoFiltro.toLowerCase());
        if (segFiltro) params.set('segmento', segFiltro);
        if (busqueda) params.set('agente_codigo', busqueda); // Si hay búsqueda por agente, filtrar por ese agente
        
        const url = `${API_URL}/exportar/polizas-excel?${params.toString()}`;
        window.open(url, '_blank');
    }

    // —— Comparativo Table Row (con VS PRESUPUESTO) ——
    function CompRow({ label, ant, act, variacion, isMoney = false, meta }) {
        const renderVal = isMoney ? fmt : v => v?.toLocaleString('es-MX') || '0';
        const avance = meta > 0 ? Math.min(100, Math.round((act / meta) * 100)) : null;
        return (
            <tr>
                <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{label}</td>
                <td style={{ textAlign: 'right' }}>{renderVal(ant)}</td>
                <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--text-primary)' }}>{renderVal(act)}</td>
                <td style={{ textAlign: 'right' }}>
                    <span className={varClass(variacion)}>
                        {varIcon(variacion)} {variacion > 0 ? '+' : ''}{variacion?.toFixed(2)}%
                    </span>
                </td>
                <td style={{ textAlign: 'right', minWidth: 100 }}>
                    {avance !== null ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end' }}>
                            <div className="progress-bar" style={{ width: 60, marginTop: 0, height: 6 }}>
                                <div className="progress-fill progress-emerald" style={{ width: `${avance}%`, height: '100%' }} />
                            </div>
                            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{avance}%</span>
                        </div>
                    ) : (
                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>—</span>
                    )}
                </td>
            </tr>
        );
    }

    // Render comparativo panel for one ramo
    function ComparativoPanel({ title, icon, comp, color, showEquiv, showAseg }) {
        return (
            <div className="card" style={{ borderTop: `3px solid ${color}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                    <span style={{ fontSize: 24 }}>{icon}</span>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{title}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{data?.anio_anterior} vs {data?.anio_actual}</div>
                    </div>
                    <button 
                        onClick={() => downloadPolizasDetalle(title)}
                        className="btn btn-ghost"
                        title={`Bajar detalle de pólizas ${title} (Excel)`}
                        style={{ fontSize: 11, padding: '4px 8px', border: '1px solid var(--border)' }}
                    >
                        📥 Bajar Excel
                    </button>
                </div>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Indicador</th>
                                <th style={{ textAlign: 'right' }}>{data?.anio_anterior}</th>
                                <th style={{ textAlign: 'right' }}>{data?.anio_actual}</th>
                                <th style={{ textAlign: 'right' }}>Variación</th>
                                <th style={{ textAlign: 'right', color: 'var(--accent-amber)' }}>VS PRESUPUESTO</th>
                            </tr>
                        </thead>
                        <tbody>
                            <CompRow label="N° Pólizas Nuevas" ant={comp.polizas_anterior} act={comp.polizas_actual} variacion={comp.polizas_variacion} />
                            {showEquiv && (
                                <CompRow label="Equivalentes" ant={comp.equivalentes_anterior} act={comp.equivalentes_actual} variacion={comp.equivalentes_variacion} />
                            )}
                            {showAseg && (
                                <CompRow label="Asegurados" ant={comp.asegurados_anterior} act={comp.asegurados_actual} variacion={comp.asegurados_variacion} />
                            )}
                            <CompRow label="Prima Venta Nueva" ant={comp.prima_nueva_anterior} act={comp.prima_nueva_actual} variacion={comp.prima_nueva_variacion} isMoney />
                            <CompRow label="Prima Subsecuente" ant={comp.prima_subsecuente_anterior} act={comp.prima_subsecuente_actual} variacion={comp.prima_subsecuente_variacion} isMoney />
                            <CompRow label="TOTAL" ant={comp.prima_total_anterior} act={comp.prima_total_actual} variacion={comp.prima_total_variacion} isMoney />
                        </tbody>
                    </table>
                </div>
            </div>
        );
    }

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Vista Ejecutiva</div>
                        <div className="header-subtitle">Comparativo interanual · Vida · GMM · Autos · Segmentos · Operativo</div>
                    </div>
                    <div className="header-right">
                        <select value={anio} onChange={e => setAnio(+e.target.value)} style={{ padding: '7px 12px' }}>
                            {[2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
                        </select>
                        {data?.filtros_disponibles?.segmentos?.length > 0 && (
                            <select value={segFiltro} onChange={e => setSegFiltro(e.target.value)} style={{ padding: '7px 12px' }}>
                                <option value="">Todos segmentos</option>
                                {data.filtros_disponibles.segmentos.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        )}
                        <select value={topN} onChange={e => setTopN(+e.target.value)} style={{ padding: '7px 12px' }}>
                            <option value={0}>Todos agentes</option>
                            <option value={10}>Top 10</option>
                            <option value={20}>Top 20</option>
                        </select>
                        <button 
                            onClick={() => downloadPolizasDetalle('')}
                            className="btn btn-primary"
                            style={{ padding: '7px 14px', fontSize: 13, background: 'var(--grad-blue)', border: 'none' }}
                        >
                            📥 Todo (Excel)
                        </button>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* Tab switcher + filter text */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
                        <div style={{ display: 'flex', gap: 4, background: 'var(--bg-card)', padding: 4, borderRadius: 12, width: 'fit-content', border: '1px solid var(--border)' }}>
                            {TABS.map(t => (
                                <button key={t} onClick={() => setTab(t)}
                                    className={`btn ${tab === t ? 'btn-primary' : 'btn-ghost'}`}
                                    style={{ textTransform: 'capitalize', padding: '8px 20px' }}>
                                    {t === 'directiva' ? '🏛️ Vista Directiva' : '📋 Vista Operativa'}
                                </button>
                            ))}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--accent-amber)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>
                            FILTROS POR: Q1,Q2,Q3,Q4, MES X, ACUMULADO MISMO PERIODO
                        </div>
                    </div>

                    {loading ? (
                        <div className="kpi-grid">
                            {Array(6).fill(0).map((_, i) => (
                                <div key={i} className="kpi-card" style={{ height: 140 }}>
                                    <div className="loading-skeleton" style={{ height: 14, width: '50%', marginBottom: 16 }} />
                                    <div className="loading-skeleton" style={{ height: 32, width: '60%', marginBottom: 12 }} />
                                    <div className="loading-skeleton" style={{ height: 8, width: '80%' }} />
                                </div>
                            ))}
                        </div>
                    ) : tab === 'directiva' ? (
                        <>
                            {/* ── KPI Summary Row (4 cards: GMM-Aseg, GMM-Prima, Vida-Equiv, Vida-Prima) ── */}
                            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                                {/* ASEGURADOS (GMM) */}
                                <div className="kpi-card emerald">
                                    <span className="kpi-icon">🏥</span>
                                    <div className="kpi-label" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>ASEGURADOS</div>
                                    <div className="kpi-value">{cg.asegurados_actual || cg.polizas_actual}</div>
                                    <span className={varClass(cg.polizas_variacion)}>
                                        {varIcon(cg.polizas_variacion)} {cg.polizas_variacion > 0 ? '+' : ''}{cg.polizas_variacion?.toFixed(1)}%
                                    </span>
                                </div>
                                {/* PRIMA TOTAL VENTA NUEVA (GMM) */}
                                <div className="kpi-card emerald">
                                    <span className="kpi-icon">💵</span>
                                    <div className="kpi-label" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>PRIMA TOTAL VENTA NUEVA</div>
                                    <div className="kpi-value">{fmt(cg.prima_nueva_actual || cg.prima_total_actual)}</div>
                                    <span className={varClass(cg.prima_nueva_variacion || cg.prima_total_variacion)}>
                                        {varIcon(cg.prima_nueva_variacion || cg.prima_total_variacion)} {(cg.prima_nueva_variacion || cg.prima_total_variacion) > 0 ? '+' : ''}{(cg.prima_nueva_variacion || cg.prima_total_variacion)?.toFixed(1)}%
                                    </span>
                                </div>
                                {/* EQUIVALENCIAS (VIDA) */}
                                <div className="kpi-card indigo">
                                    <span className="kpi-icon">🛡️</span>
                                    <div className="kpi-label" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>EQUIVALENCIAS</div>
                                    <div className="kpi-value">{cv.equivalentes_actual || cv.polizas_actual}</div>
                                    <span className={varClass(cv.equivalentes_variacion || cv.polizas_variacion)}>
                                        {varIcon(cv.equivalentes_variacion || cv.polizas_variacion)} {(cv.equivalentes_variacion || cv.polizas_variacion) > 0 ? '+' : ''}{(cv.equivalentes_variacion || cv.polizas_variacion)?.toFixed(1)}%
                                    </span>
                                </div>
                                {/* PRIMA TOTAL VENTA NUEVA (VIDA) */}
                                <div className="kpi-card indigo">
                                    <span className="kpi-icon">💰</span>
                                    <div className="kpi-label" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1 }}>PRIMA TOTAL VENTA NUEVA</div>
                                    <div className="kpi-value">{fmt(cv.prima_nueva_actual || cv.prima_total_actual)}</div>
                                    <span className={varClass(cv.prima_nueva_variacion || cv.prima_total_variacion)}>
                                        {varIcon(cv.prima_nueva_variacion || cv.prima_total_variacion)} {(cv.prima_nueva_variacion || cv.prima_total_variacion) > 0 ? '+' : ''}{(cv.prima_nueva_variacion || cv.prima_total_variacion)?.toFixed(1)}%
                                    </span>
                                </div>
                            </div>

                            {/* ── Comparativo tables (GMM & VIDA side by side) ── */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20, marginBottom: 28 }}>
                                <ComparativoPanel title="GMM" icon="🏥" comp={cg} color="#10b981" showEquiv={false} showAseg />
                                <ComparativoPanel title="VIDA" icon="🛡️" comp={cv} color="#6366f1" showEquiv showAseg={false} />
                            </div>

                            {/* ── Segmentos: GMM por Segmento + VIDA por Segmento + Distribución ── */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, marginBottom: 28 }}>
                                {/* GMM por Segmento */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Producción GMM por Segmento</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ALFA · BETA · OMEGA — {anio}</div>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={(() => {
                                                const totalGmm = segs.reduce((s, x) => s + (x.prima_gmm || 0), 0);
                                                return segs.map(s => ({
                                                    ...s,
                                                    prima_gmm_val: s.prima_gmm || 0,
                                                    pct_dist: totalGmm > 0 ? `${((s.prima_gmm || 0) / totalGmm * 100).toFixed(0)}%` : '0%',
                                                }));
                                            })()} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="segmento" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                                <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip formatter={v => fmtFull(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Bar dataKey="prima_gmm" name="Prima GMM" fill="#10b981" radius={[4, 4, 0, 0]}
                                                    label={{ position: 'top', fill: '#10b981', fontSize: 10, formatter: (v) => { const total = segs.reduce((s, x) => s + (x.prima_gmm || 0), 0); return total > 0 ? `${((v / total) * 100).toFixed(0)}%` : ''; } }} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div style={{ textAlign: 'center', marginTop: 8, fontSize: 10, color: 'var(--text-muted)' }}>
                                        % DE DISTRIBUCIÓN · % DE INCREMENTO VS AÑO PASADO
                                    </div>
                                </div>

                                {/* VIDA por Segmento */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Producción VIDA por Segmento</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ALFA · BETA · OMEGA — {anio}</div>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={segs} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="segmento" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                                <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip formatter={v => fmtFull(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Bar dataKey="prima_vida" name="Prima Vida" fill="#6366f1" radius={[4, 4, 0, 0]}
                                                    label={{ position: 'top', fill: '#6366f1', fontSize: 10, formatter: (v) => { const total = segs.reduce((s, x) => s + (x.prima_vida || 0), 0); return total > 0 ? `${((v / total) * 100).toFixed(0)}%` : ''; } }} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div style={{ textAlign: 'center', marginTop: 8, fontSize: 10, color: 'var(--text-muted)' }}>
                                        % DE DISTRIBUCIÓN · % DE INCREMENTO VS AÑO PASADO
                                    </div>
                                </div>

                                {/* Distribución por Segmento (pie chart) */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Distribución por Segmento</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Proporción de prima total</div>
                                    </div>
                                    <div style={{ height: 220, display: 'flex', gap: 16, alignItems: 'center' }}>
                                        <ResponsiveContainer width="55%" height="100%">
                                            <PieChart>
                                                <Pie data={segs} dataKey="prima_total" cx="50%" cy="50%" outerRadius={80} innerRadius={40}
                                                    label={({ segmento, percent }) => `${segmento} ${(percent * 100).toFixed(0)}%`}
                                                    labelLine={false}>
                                                    {segs.map((s, i) => <Cell key={i} fill={COLORS_SEG[s.segmento] || '#64748b'} />)}
                                                </Pie>
                                                <Tooltip formatter={v => fmtFull(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                            </PieChart>
                                        </ResponsiveContainer>
                                        <div style={{ flex: 1 }}>
                                            {segs.map((s, i) => (
                                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                                                    <div style={{ width: 12, height: 12, borderRadius: 4, background: COLORS_SEG[s.segmento] || '#64748b', flexShrink: 0 }} />
                                                    <div>
                                                        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{s.segmento}</div>
                                                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.num_agentes} agentes · {s.polizas_vida + s.polizas_gmm + s.polizas_autos} pólizas</div>
                                                        <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{fmtFull(s.prima_total)}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* ── Producción Mensual Comparativa ── */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 28 }}>
                                {/* Vida */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Prima Vida — {data?.anio_anterior} vs {data?.anio_actual}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Producción mensual comparativa</div>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={data?.mensual_vida || []} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip formatter={v => fmtFull(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                                <Line type="monotone" dataKey="prima_anterior" name={`${data?.anio_anterior}`} stroke="#64748b" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: '#64748b', r: 3 }} />
                                                <Line type="monotone" dataKey="prima_actual" name={`${data?.anio_actual}`} stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 4 }} activeDot={{ r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                                {/* GMM */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Prima GMM — {data?.anio_anterior} vs {data?.anio_actual}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Producción mensual comparativa</div>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={data?.mensual_gmm || []} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip formatter={v => fmtFull(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                                <Line type="monotone" dataKey="prima_anterior" name={`${data?.anio_anterior}`} stroke="#64748b" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: '#64748b', r: 3 }} />
                                                <Line type="monotone" dataKey="prima_actual" name={`${data?.anio_actual}`} stroke="#10b981" strokeWidth={2.5} dot={{ fill: '#10b981', r: 4 }} activeDot={{ r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                                {/* Autos */}
                                <div className="card">
                                    <div style={{ marginBottom: 20 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Prima Autos — {data?.anio_anterior} vs {data?.anio_actual}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Producción mensual comparativa</div>
                                    </div>
                                    <div className="chart-container">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={data?.mensual_autos || []} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                <Tooltip formatter={v => fmtFull(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                                <Line type="monotone" dataKey="prima_anterior" name={`${data?.anio_anterior}`} stroke="#64748b" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: '#64748b', r: 3 }} />
                                                <Line type="monotone" dataKey="prima_actual" name={`${data?.anio_actual}`} stroke="#3b82f6" strokeWidth={2.5} dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 6 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        /* ── VISTA OPERATIVA ── */
                        <>
                            {/* Filter bar + Export + Sort */}
                            <div className="filters-bar" style={{ marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
                                <div className="filter-group">
                                    <span className="filter-label">🔎 Buscar:</span>
                                    <input type="search" placeholder="Nombre o clave de agente..."
                                        value={busqueda} onChange={e => setBusqueda(e.target.value)}
                                        style={{ width: 240 }} />
                                </div>

                                {/* Sort toggle */}
                                <div style={{ display: 'flex', gap: 4, background: 'var(--bg-secondary)', borderRadius: 8, padding: 3 }}>
                                    {[
                                        { key: 'prima', label: '💰 Por Prima' },
                                        { key: 'aseg', label: '👥 Por Aseg/Equiv' },
                                    ].map(s => (
                                        <button key={s.key}
                                            onClick={() => setSortOp(s.key)}
                                            style={{
                                                padding: '5px 12px', fontSize: 11, fontWeight: 600, borderRadius: 6,
                                                border: 'none', cursor: 'pointer',
                                                background: sortOp === s.key ? 'var(--grad-blue)' : 'transparent',
                                                color: sortOp === s.key ? 'white' : 'var(--text-muted)',
                                                transition: 'all 0.2s',
                                            }}>
                                            {s.label}
                                        </button>
                                    ))}
                                </div>

                                {/* Export */}
                                <button onClick={exportExcel}
                                    style={{
                                        padding: '6px 14px', fontSize: 11, fontWeight: 600, borderRadius: 8,
                                        border: '1px solid var(--accent-emerald)', background: 'rgba(16,185,129,0.1)',
                                        color: 'var(--accent-emerald)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5,
                                    }}>
                                    📥 Exportar Excel
                                </button>

                                <div style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
                                    {agentes.length} agentes · Prima total: {fmtFull(agentes.reduce((s, a) => s + a.prima_pagada_total, 0))}
                                </div>
                            </div>

                            {/* Filter labels */}
                            <div style={{ display: 'flex', gap: 6, marginBottom: 16, fontSize: 11, color: 'var(--accent-amber)', fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>
                                FILTROS: RAMO, PERIODO, SEGMENTO, LIDER
                            </div>

                            <div className="card" style={{ overflow: 'hidden' }}>
                                <div className="table-container" style={{ maxHeight: 'calc(100vh - 320px)', overflow: 'auto' }}>
                                    <table style={{ fontSize: 12 }}>
                                        <thead>
                                            {/* Year group headers */}
                                            <tr>
                                                <th colSpan={4} style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 3 }}></th>
                                                <th colSpan={4} style={{ position: 'sticky', top: 0, background: 'rgba(99,102,241,0.12)', zIndex: 3, textAlign: 'center', fontSize: 13, fontWeight: 800, color: 'var(--accent-indigo)', letterSpacing: 1 }}>
                                                    {data?.anio_actual || anio}
                                                </th>
                                                <th colSpan={4} style={{ position: 'sticky', top: 0, background: 'rgba(16,185,129,0.12)', zIndex: 3, textAlign: 'center', fontSize: 13, fontWeight: 800, color: 'var(--accent-emerald)', letterSpacing: 1 }}>
                                                    {data?.anio_anterior || anio - 1}
                                                </th>
                                                <th colSpan={2} style={{ position: 'sticky', top: 0, background: 'rgba(245,158,11,0.12)', zIndex: 3, textAlign: 'center', fontSize: 11, fontWeight: 700, color: 'var(--accent-amber)' }}>
                                                    VS PRESUPUESTO
                                                </th>
                                            </tr>
                                            <tr>
                                                <th style={{ position: 'sticky', top: 28, background: 'var(--bg-card)', zIndex: 2 }}>#</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'var(--bg-card)', zIndex: 2, minWidth: 180 }}>Agente</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'var(--bg-card)', zIndex: 2 }}>Seg</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'var(--bg-card)', zIndex: 2 }}>Gestión</th>
                                                {/* Año actual columns */}
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(99,102,241,0.15)', zIndex: 2, textAlign: 'right' }}>Pol Vida</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(99,102,241,0.15)', zIndex: 2, textAlign: 'right' }}>Equiv</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(99,102,241,0.15)', zIndex: 2, textAlign: 'right' }}>Prima Vida</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(16,185,129,0.15)', zIndex: 2, textAlign: 'right' }}>Pol GMM</th>
                                                {/* Año anterior columns */}
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(16,185,129,0.08)', zIndex: 2, textAlign: 'right' }}>Aseg</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(16,185,129,0.08)', zIndex: 2, textAlign: 'right' }}>Prima GMM</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(245,158,11,0.08)', zIndex: 2, textAlign: 'right', fontWeight: 700 }}>Total</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'var(--bg-card)', zIndex: 2, textAlign: 'right' }}>Crec Vida</th>
                                                {/* VS Presupuesto */}
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(245,158,11,0.08)', zIndex: 2, textAlign: 'right' }}>Vida</th>
                                                <th style={{ position: 'sticky', top: 28, background: 'rgba(245,158,11,0.08)', zIndex: 2, textAlign: 'right' }}>GMM</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {agentes.map((a, i) => (
                                                <tr key={a.clave || i}>
                                                    <td>
                                                        <span style={{
                                                            width: 22, height: 22, borderRadius: '50%',
                                                            background: i < 3 ? 'var(--grad-blue)' : i < 10 ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.06)',
                                                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                            fontSize: 10, fontWeight: 700, color: 'white',
                                                        }}>{i + 1}</span>
                                                    </td>
                                                    <td>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                            <div className="avatar" style={{ width: 28, height: 28, fontSize: 10 }}>{(a.nombre || '?')[0]}</div>
                                                            <div>
                                                                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                                                                    {a.nombre?.length > 22 ? a.nombre.slice(0, 22) + '…' : a.nombre}
                                                                </div>
                                                                <code style={{ background: 'rgba(59,130,246,0.1)', padding: '1px 5px', borderRadius: 3, fontSize: 10 }}>{a.clave}</code>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <span className={`badge badge-${a.segmento_agrupado === 'ALFA' ? 'purple' : a.segmento_agrupado === 'BETA' ? 'emerald' : 'amber'}`}>
                                                            {a.segmento_agrupado || '-'}
                                                        </span>
                                                    </td>
                                                    <td style={{ fontSize: 10, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{a.oficina}</td>
                                                    {/* Año actual */}
                                                    <td style={{ textAlign: 'right', background: 'rgba(99,102,241,0.04)' }}>{a.polizas_vida}</td>
                                                    <td style={{ textAlign: 'right', background: 'rgba(99,102,241,0.04)' }}>{a.equivalencias_vida || 0}</td>
                                                    <td style={{ textAlign: 'right', fontWeight: 600, background: 'rgba(99,102,241,0.04)' }}>{fmt(a.prima_pagada_vida)}</td>
                                                    <td style={{ textAlign: 'right', background: 'rgba(16,185,129,0.04)' }}>{a.polizas_gmm}</td>
                                                    {/* Año anterior / Aseg */}
                                                    <td style={{ textAlign: 'right', background: 'rgba(16,185,129,0.02)' }}>{a.asegurados_gmm || a.polizas_gmm}</td>
                                                    <td style={{ textAlign: 'right', fontWeight: 600, background: 'rgba(16,185,129,0.02)' }}>{fmt(a.prima_pagada_gmm)}</td>
                                                    {/* Total */}
                                                    <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--text-primary)', background: 'rgba(245,158,11,0.04)' }}>{fmt(a.prima_pagada_total)}</td>
                                                    {/* Crec Vida */}
                                                    <td style={{ textAlign: 'right' }}>
                                                        <span className={varClass(a.vida_crecimiento)} style={{ fontSize: 11 }}>
                                                            {a.vida_crecimiento > 0 ? '+' : ''}{a.vida_crecimiento?.toFixed(1)}%
                                                        </span>
                                                    </td>
                                                    {/* VS Presupuesto Vida */}
                                                    <td style={{ textAlign: 'right' }}>
                                                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>—</span>
                                                    </td>
                                                    {/* VS Presupuesto GMM */}
                                                    <td style={{ textAlign: 'right' }}>
                                                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>—</span>
                                                    </td>
                                                </tr>
                                            ))}
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
