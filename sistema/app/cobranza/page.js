'use client';
import { useState, useEffect, useMemo } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const PRIO_CONFIG = {
    critico: { color: '#ef4444', bg: 'rgba(239,68,68,0.15)', icon: '🔴', label: 'Crítico' },
    urgente: { color: '#f97316', bg: 'rgba(249,115,22,0.15)', icon: '🟠', label: 'Urgente' },
    atencion: { color: '#eab308', bg: 'rgba(234,179,8,0.15)', icon: '🟡', label: 'Atención' },
    al_dia: { color: '#22c55e', bg: 'rgba(34,197,94,0.15)', icon: '🟢', label: 'Al día' },
    pagado: { color: '#3b82f6', bg: 'rgba(59,130,246,0.15)', icon: '✅', label: 'Pagado' },
};
const TABS = ['deudores', 'renovaciones', 'canceladas', 'seguimiento'];

function fmt(n) {
    if (n == null) return '$0';
    if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}
function fmtF(n) {
    if (n == null) return '$0';
    return `$${n.toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export default function Cobranza() {
    const [data, setData] = useState(null);
    const [anio, setAnio] = useState(2025);
    const [ramo, setRamo] = useState('');
    const [prioFiltro, setPrioFiltro] = useState('');
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('deudores');
    const [busqueda, setBusqueda] = useState('');

    useEffect(() => {
        setLoading(true);
        const p = new URLSearchParams({ anio });
        if (ramo) p.set('ramo', ramo);
        if (prioFiltro) p.set('prioridad', prioFiltro);
        apiFetch(`/cobranza?${p}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [anio, ramo, prioFiltro]);

    const res = data?.resumen || {};
    const deudores = useMemo(() => {
        if (!data?.deudores) return [];
        if (!busqueda) return data.deudores;
        const q = busqueda.toLowerCase();
        return data.deudores.filter(d =>
            (d.poliza || '').toLowerCase().includes(q) ||
            (d.contratante || '').toLowerCase().includes(q) ||
            (d.agente_nombre || '').toLowerCase().includes(q) ||
            (d.agente_clave || '').toLowerCase().includes(q)
        );
    }, [data, busqueda]);

    const renovaciones = data?.renovaciones || [];
    const canceladas = data?.canceladas || [];
    const alertas = data?.alertas || [];
    const seguimiento = data?.seguimiento_mensual || [];
    const donutData = Object.entries(PRIO_CONFIG)
        .map(([k, v]) => ({ name: v.label, value: res[k === 'al_dia' ? 'al_dia' : k === 'atencion' ? 'atencion' : k === 'urgente' ? 'urgentes' : k === 'critico' ? 'criticas' : 'pagadas'] || 0, fill: v.color }))
        .filter(d => d.value > 0);

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Cobranza y Deudor por Prima</div>
                        <div className="header-subtitle">Semáforo de prioridad · Renovaciones · Canceladas</div>
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
                        <select value={prioFiltro} onChange={e => setPrioFiltro(e.target.value)} style={{ padding: '7px 12px' }}>
                            <option value="">Todas prioridades</option>
                            {Object.entries(PRIO_CONFIG).map(([k, v]) => (
                                <option key={k} value={k}>{v.icon} {v.label}</option>
                            ))}
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
                            {/* ── ALERTAS ── */}
                            {alertas.length > 0 && (
                                <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
                                    {alertas.map((a, i) => (
                                        <div key={i} className={`alert alert-${a.tipo === 'vencido' ? 'error' : a.tipo === 'por_cancelar' ? 'warning' : a.tipo === 'renovacion' ? 'info' : 'warning'}`}
                                            style={{ flex: '1 1 280px' }}>
                                            <span style={{ fontSize: 20 }}>{a.icono}</span>
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: 13 }}>{a.titulo}</div>
                                                <div style={{ fontSize: 12, opacity: 0.85 }}>{a.descripcion}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* ── KPI CARDS ── */}
                            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                                {Object.entries(PRIO_CONFIG).map(([key, cfg]) => {
                                    const count = key === 'critico' ? res.criticas : key === 'urgente' ? res.urgentes :
                                        key === 'atencion' ? res.atencion : key === 'al_dia' ? res.al_dia : res.pagadas;
                                    return (
                                        <div key={key} className="kpi-card" style={{ borderTop: `3px solid ${cfg.color}`, cursor: 'pointer' }}
                                            onClick={() => setPrioFiltro(prioFiltro === key ? '' : key)}>
                                            <div style={{ fontSize: 24, marginBottom: 8 }}>{cfg.icon}</div>
                                            <div className="kpi-value" style={{ color: cfg.color }}>{count || 0}</div>
                                            <div className="kpi-label">{cfg.label}</div>
                                        </div>
                                    );
                                })}
                                <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-cyan)' }}>
                                    <div style={{ fontSize: 24, marginBottom: 8 }}>💰</div>
                                    <div className="kpi-value" style={{ fontSize: 22 }}>{res.pct_cobranza?.toFixed(1)}%</div>
                                    <div className="kpi-label">% Cobranza</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                        Cobrado: {fmt(res.prima_cobrada)} / {fmt(res.prima_cobrada + res.prima_por_cobrar)}
                                    </div>
                                </div>
                            </div>

                            {/* ── TABS ── */}
                            <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--bg-card)', padding: 4, borderRadius: 12, width: 'fit-content', border: '1px solid var(--border)' }}>
                                {TABS.map(t => (
                                    <button key={t} onClick={() => setTab(t)}
                                        className={`btn ${tab === t ? 'btn-primary' : 'btn-ghost'}`}
                                        style={{ textTransform: 'capitalize', padding: '8px 18px' }}>
                                        {t === 'deudores' ? '🔴 Deudores' : t === 'renovaciones' ? '🔄 Renovaciones' :
                                            t === 'canceladas' ? '⚠️ Canceladas' : '📊 Seguimiento'}
                                    </button>
                                ))}
                            </div>

                            {/* ── TAB CONTENT ── */}
                            {tab === 'deudores' && (
                                <>
                                    <div className="filters-bar" style={{ marginBottom: 16 }}>
                                        <div className="filter-group">
                                            <span className="filter-label">🔎</span>
                                            <input type="search" placeholder="Póliza, contratante o agente..."
                                                value={busqueda} onChange={e => setBusqueda(e.target.value)}
                                                style={{ width: 280 }} />
                                        </div>
                                        <div style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
                                            {deudores.length} pólizas · Prima pendiente: {fmtF(deudores.reduce((s, d) => s + d.prima_pendiente, 0))}
                                        </div>
                                    </div>

                                    <div className="card" style={{ overflow: 'hidden' }}>
                                        <div className="table-container" style={{ maxHeight: 'calc(100vh - 380px)', overflow: 'auto' }}>
                                            <table style={{ fontSize: 12 }}>
                                                <thead>
                                                    <tr>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>Prioridad</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>Póliza</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2, minWidth: 150 }}>Contratante</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>Agente</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>Ramo</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2, textAlign: 'right' }}>Prima Neta</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2, textAlign: 'right' }}>Cobrado</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2, textAlign: 'right' }}>Pendiente</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2, textAlign: 'center' }}>Recibo</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2, textAlign: 'right' }}>Días Venc.</th>
                                                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {deudores.map((d, i) => {
                                                        const pc = PRIO_CONFIG[d.prioridad] || PRIO_CONFIG.al_dia;
                                                        return (
                                                            <tr key={i}>
                                                                <td>
                                                                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: pc.bg, color: pc.color }}>
                                                                        {pc.icon} {pc.label}
                                                                    </span>
                                                                </td>
                                                                <td><code style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 11 }}>{d.poliza}</code></td>
                                                                <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                    {d.contratante || d.asegurado || '-'}
                                                                </td>
                                                                <td>
                                                                    <div style={{ fontSize: 11 }}>{d.agente_nombre?.length > 20 ? d.agente_nombre.slice(0, 20) + '…' : d.agente_nombre}</div>
                                                                    <code style={{ fontSize: 10, color: 'var(--text-muted)' }}>{d.agente_clave}</code>
                                                                </td>
                                                                <td style={{ fontSize: 11 }}>{d.ramo || '-'}</td>
                                                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(d.prima_neta)}</td>
                                                                <td style={{ textAlign: 'right', color: 'var(--accent-emerald)' }}>{fmt(d.prima_acumulada)}</td>
                                                                <td style={{ textAlign: 'right', fontWeight: 700, color: d.prima_pendiente > 0 ? pc.color : 'var(--text-muted)' }}>{fmt(d.prima_pendiente)}</td>
                                                                <td style={{ textAlign: 'center' }}>
                                                                    <span className="badge badge-blue" style={{ fontSize: 10 }}>{d.recibo_actual}</span>
                                                                </td>
                                                                <td style={{ textAlign: 'right', fontWeight: d.dias_vencimiento > 0 ? 700 : 400, color: d.dias_vencimiento > 30 ? '#ef4444' : d.dias_vencimiento > 15 ? '#f97316' : d.dias_vencimiento > 0 ? '#eab308' : 'var(--text-muted)' }}>
                                                                    {d.dias_vencimiento > 0 ? `${d.dias_vencimiento}d` : '-'}
                                                                </td>
                                                                <td>
                                                                    <span className={`status-pill ${d.mystatus?.includes('PAGADA') ? 'status-pagada' : d.mystatus?.includes('CANCELADA') || d.mystatus?.includes('CANC') ? 'status-cancelada' : 'status-subsecuente'}`}>
                                                                        {d.mystatus || d.status || '-'}
                                                                    </span>
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

                            {tab === 'renovaciones' && (
                                <div className="card">
                                    <div style={{ marginBottom: 16 }}>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Renovaciones Pendientes</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{renovaciones.length} pólizas en ventana de renovación (±90 días)</div>
                                    </div>
                                    {renovaciones.length === 0 ? (
                                        <div className="empty-state">
                                            <div className="empty-state-icon">🔄</div>
                                            <div className="empty-state-title">Sin renovaciones pendientes</div>
                                            <div className="empty-state-desc">No hay pólizas próximas a renovar en el período seleccionado</div>
                                        </div>
                                    ) : (
                                        <div className="table-container">
                                            <table style={{ fontSize: 12 }}>
                                                <thead>
                                                    <tr>
                                                        <th>Estado</th>
                                                        <th>Póliza</th>
                                                        <th>Contratante</th>
                                                        <th>Agente</th>
                                                        <th>Ramo</th>
                                                        <th style={{ textAlign: 'right' }}>Prima</th>
                                                        <th>Vencimiento</th>
                                                        <th style={{ textAlign: 'right' }}>Días</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {renovaciones.map((r, i) => (
                                                        <tr key={i}>
                                                            <td>
                                                                <span style={{
                                                                    padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                                                                    background: r.estado_renovacion === 'renovada' ? 'rgba(59,130,246,0.15)' : r.estado_renovacion === 'vencida' ? 'rgba(239,68,68,0.15)' : 'rgba(234,179,8,0.15)',
                                                                    color: r.estado_renovacion === 'renovada' ? '#3b82f6' : r.estado_renovacion === 'vencida' ? '#ef4444' : '#eab308',
                                                                }}>
                                                                    {r.estado_renovacion === 'renovada' ? '✅ Renovada' : r.estado_renovacion === 'vencida' ? '❌ Vencida' : '⏳ Por vencer'}
                                                                </span>
                                                            </td>
                                                            <td><code style={{ fontSize: 11 }}>{r.poliza}</code></td>
                                                            <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.contratante || '-'}</td>
                                                            <td style={{ fontSize: 11 }}>{r.agente_nombre || '-'}</td>
                                                            <td>{r.ramo || '-'}</td>
                                                            <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.prima_neta)}</td>
                                                            <td style={{ fontSize: 11 }}>{r.fecha_fin || '-'}</td>
                                                            <td style={{ textAlign: 'right', fontWeight: 700, color: r.dias_para_renovar < 0 ? '#ef4444' : r.dias_para_renovar <= 30 ? '#eab308' : 'var(--text-muted)' }}>
                                                                {r.dias_para_renovar}d
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}

                            {tab === 'canceladas' && (
                                <div className="card">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Pólizas Canceladas — {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{canceladas.length} pólizas · Prima perdida: {fmtF(canceladas.reduce((s, c) => s + c.prima_perdida, 0))}</div>
                                        </div>
                                    </div>
                                    {canceladas.length === 0 ? (
                                        <div className="empty-state">
                                            <div className="empty-state-icon">✅</div>
                                            <div className="empty-state-title">Sin cancelaciones</div>
                                        </div>
                                    ) : (
                                        <div className="table-container">
                                            <table style={{ fontSize: 12 }}>
                                                <thead>
                                                    <tr>
                                                        <th>Póliza</th>
                                                        <th>Contratante</th>
                                                        <th>Agente</th>
                                                        <th>Ramo</th>
                                                        <th style={{ textAlign: 'right' }}>Prima Neta</th>
                                                        <th style={{ textAlign: 'right' }}>Cobrado</th>
                                                        <th style={{ textAlign: 'right' }}>Prima Perdida</th>
                                                        <th>Motivo</th>
                                                        <th>Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {canceladas.map((c, i) => (
                                                        <tr key={i}>
                                                            <td><code style={{ fontSize: 11 }}>{c.poliza}</code></td>
                                                            <td style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.contratante || '-'}</td>
                                                            <td style={{ fontSize: 11 }}>{c.agente_nombre || '-'}</td>
                                                            <td>{c.ramo || '-'}</td>
                                                            <td style={{ textAlign: 'right' }}>{fmt(c.prima_neta)}</td>
                                                            <td style={{ textAlign: 'right', color: 'var(--accent-emerald)' }}>{fmt(c.prima_acumulada)}</td>
                                                            <td style={{ textAlign: 'right', fontWeight: 700, color: '#ef4444' }}>{fmt(c.prima_perdida)}</td>
                                                            <td style={{ fontSize: 11, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.motivo || '-'}</td>
                                                            <td><span className="status-pill status-cancelada">{c.mystatus || '-'}</span></td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}

                            {tab === 'seguimiento' && (
                                <div className="charts-grid">
                                    <div className="card">
                                        <div style={{ marginBottom: 20 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Seguimiento de Cobranza — {anio}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Meta vs Cobrado por mes</div>
                                        </div>
                                        <div className="chart-container">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={seguimiento} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis tickFormatter={v => fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => fmtF(v)} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                                    <Bar dataKey="meta" name="Meta (Prima)" fill="rgba(99,102,241,0.3)" radius={[4, 4, 0, 0]} />
                                                    <Bar dataKey="cobrado" name="Cobrado" fill="#10b981" radius={[4, 4, 0, 0]} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    <div className="card">
                                        <div style={{ marginBottom: 20 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>% Cobranza por Mes</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Porcentaje de prima cobrada</div>
                                        </div>
                                        <div className="chart-container">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart data={seguimiento} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                                    <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                                                        tickFormatter={v => v.substring(0, 3)} />
                                                    <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} labelStyle={{ color: '#f1f5f9' }} />
                                                    <Line type="monotone" dataKey="pct" name="% Cobranza" stroke="#3b82f6" strokeWidth={2.5}
                                                        dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 6 }} />
                                                    {/* Reference line at 80% target */}
                                                    <Line type="monotone" dataKey={() => 80} name="Meta 80%" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    {/* Distribución de prioridades */}
                                    <div className="card" style={{ gridColumn: 'span 2' }}>
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Distribución de Cartera</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{res.total_polizas} pólizas totales</div>
                                        </div>
                                        <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                                            <ResponsiveContainer width="40%" height={200}>
                                                <PieChart>
                                                    <Pie data={donutData} dataKey="value" cx="50%" cy="50%" outerRadius={80} innerRadius={45}
                                                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                                                        {donutData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                                                    </Pie>
                                                    <Tooltip contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                                                </PieChart>
                                            </ResponsiveContainer>
                                            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                                                {Object.entries(PRIO_CONFIG).map(([key, cfg]) => {
                                                    const count = key === 'critico' ? res.criticas : key === 'urgente' ? res.urgentes :
                                                        key === 'atencion' ? res.atencion : key === 'al_dia' ? res.al_dia : res.pagadas;
                                                    return (
                                                        <div key={key} style={{ background: cfg.bg, padding: '12px 16px', borderRadius: 12, textAlign: 'center' }}>
                                                            <div style={{ fontSize: 20 }}>{cfg.icon}</div>
                                                            <div style={{ fontSize: 22, fontWeight: 800, color: cfg.color }}>{count || 0}</div>
                                                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{cfg.label}</div>
                                                        </div>
                                                    );
                                                })}
                                                <div style={{ background: 'rgba(6,182,212,0.15)', padding: '12px 16px', borderRadius: 12, textAlign: 'center' }}>
                                                    <div style={{ fontSize: 20 }}>💰</div>
                                                    <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--accent-cyan)' }}>{fmt(res.prima_por_cobrar)}</div>
                                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Por Cobrar</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
