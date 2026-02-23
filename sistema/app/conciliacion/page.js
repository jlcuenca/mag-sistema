'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const STATUS_COLORS = {
    COINCIDE: '#10b981',
    DIFERENCIA: '#f59e0b',
    SOLO_AXA: '#f43f5e',
    SOLO_INTERNO: '#3b82f6',
};

export default function Conciliacion() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [periodo, setPeriodo] = useState('2025-07');

    useEffect(() => {
        setLoading(true);
        apiFetch(`/conciliacion?periodo=${periodo}`)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [periodo]);

    const resumen = data?.resumen || {};
    const conciliacion = data?.conciliacion || [];
    const periodos = data?.periodos || [];

    const pieData = [
        { name: 'Coincide', value: resumen.coincide || 0, color: STATUS_COLORS.COINCIDE },
        { name: 'Diferencia', value: resumen.diferencia || 0, color: STATUS_COLORS.DIFERENCIA },
        { name: 'Solo AXA', value: resumen.solo_axa || 0, color: STATUS_COLORS.SOLO_AXA },
        { name: 'Solo Interno', value: resumen.solo_interno || 0, color: STATUS_COLORS.SOLO_INTERNO },
    ].filter(d => d.value > 0);

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Conciliación AXA</div>
                        <div className="header-subtitle">Cruce automático base interna vs. indicadores AXA</div>
                    </div>
                    <div className="header-right">
                        <select value={periodo} onChange={e => setPeriodo(e.target.value)}>
                            {periodos.length > 0 ? periodos.map(p => (
                                <option key={p} value={p}>{p}</option>
                            )) : <option value="2025-07">2025-07</option>}
                        </select>
                        <span className={`badge ${(resumen.pctCoincidencia || 0) >= 80 ? 'badge-emerald' : 'badge-amber'}`}>
                            {resumen.pctCoincidencia || 0}% coincidencia
                        </span>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {loading ? (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 24 }}>
                            {Array(4).fill(0).map((_, i) => (
                                <div key={i} className="kpi-card" style={{ height: 100 }}>
                                    <div className="loading-skeleton" style={{ height: 12, width: '70%', marginBottom: 12 }} />
                                    <div className="loading-skeleton" style={{ height: 28, width: '40%' }} />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <>
                            {/* Alerta informativa */}
                            <div className="alert alert-info" style={{ marginBottom: 20 }}>
                                ℹ️ Los indicadores AXA se reciben a <strong>mes vencido</strong>. El cruce se realiza normalizando el número de póliza antes de comparar.
                            </div>

                            {/* Resumen en KPI cards */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 28 }}>
                                {[
                                    { label: 'Total AXA', value: resumen.total || 0, color: '#60a5fa', icon: '📊' },
                                    { label: 'Coinciden', value: resumen.coincide || 0, color: '#34d399', icon: '✅' },
                                    { label: 'Con Diferencia', value: resumen.diferencia || 0, color: '#fbbf24', icon: '⚠️' },
                                    { label: 'Solo en AXA', value: resumen.soloAxa || 0, color: '#f87171', icon: '❌' },
                                ].map((k, i) => (
                                    <div key={i} className="kpi-card" style={{ [`--c`]: k.color }}>
                                        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: k.color, borderRadius: '16px 16px 0 0' }} />
                                        <span className="kpi-icon">{k.icon}</span>
                                        <div className="kpi-label">{k.label}</div>
                                        <div className="kpi-value" style={{ color: k.color, fontSize: 32 }}>{k.value}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Gráfica + Tabla */}
                            <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20, marginBottom: 24 }}>
                                {/* Pie chart */}
                                <div className="card">
                                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>Distribución</div>
                                    <div style={{ height: 180 }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={75} innerRadius={40}>
                                                    {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                                                </Pie>
                                                <Tooltip contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div style={{ marginTop: 12 }}>
                                        {pieData.map((d, i) => (
                                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                                <div style={{ width: 10, height: 10, borderRadius: 3, background: d.color, flexShrink: 0 }} />
                                                <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>{d.name}</span>
                                                <span style={{ fontSize: 13, fontWeight: 700, color: d.color }}>{d.value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Detalle de pólizas */}
                                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                                    <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
                                        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Detalle de Pólizas — Periodo {periodo}</div>
                                    </div>
                                    <div className="table-container">
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>Póliza AXA</th>
                                                    <th>Agente</th>
                                                    <th>Ramo</th>
                                                    <th>Prima AXA</th>
                                                    <th>Clasif. AXA</th>
                                                    <th>Clasif. Interna</th>
                                                    <th>Status</th>
                                                    <th>Diferencia</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {conciliacion.length === 0 ? (
                                                    <tr>
                                                        <td colSpan={8}>
                                                            <div className="empty-state">
                                                                <div className="empty-state-icon">🔍</div>
                                                                <div className="empty-state-title">Sin datos de conciliación</div>
                                                                <div className="empty-state-desc">No hay indicadores AXA para el periodo seleccionado</div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ) : conciliacion.map((c, i) => (
                                                    <tr key={i}>
                                                        <td>
                                                            <code style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>
                                                                {c.poliza}
                                                            </code>
                                                        </td>
                                                        <td style={{ fontSize: 12 }}>
                                                            <div style={{ color: 'var(--text-primary)' }}>{c.agente_nombre || '—'}</div>
                                                            <div style={{ color: 'var(--text-muted)' }}>{c.agente_codigo}</div>
                                                        </td>
                                                        <td>
                                                            <span style={{ fontSize: 11, fontWeight: 600, color: c.ramo === 'VIDA' ? '#818cf8' : '#34d399' }}>
                                                                {c.ramo}
                                                            </span>
                                                        </td>
                                                        <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                                                            ${(c.prima_primer_anio || 0).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                                        </td>
                                                        <td>
                                                            <span style={{ fontSize: 11, fontWeight: 600, color: c.es_nueva_axa ? '#34d399' : '#f87171' }}>
                                                                {c.es_nueva_axa ? '✅ Nueva' : '❌ No Nueva'}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            {c.poliza_interna ? (
                                                                <span style={{ fontSize: 11, fontWeight: 600, color: c.poliza_interna.tipo_poliza === 'NUEVA' ? '#34d399' : '#fbbf24' }}>
                                                                    {c.poliza_interna.tipo_poliza}
                                                                </span>
                                                            ) : <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>No encontrada</span>}
                                                        </td>
                                                        <td>
                                                            <span className={
                                                                c.status === 'COINCIDE' ? 'conc-status-coincide' :
                                                                    c.status === 'DIFERENCIA' ? 'conc-status-diferencia' :
                                                                        c.status === 'SOLO_AXA' ? 'conc-status-solo-axa' :
                                                                            'conc-status-solo-interno'
                                                            }>
                                                                {c.status === 'COINCIDE' ? '✅ Coincide' :
                                                                    c.status === 'DIFERENCIA' ? '⚠️ Diferencia' :
                                                                        c.status === 'SOLO_AXA' ? '❌ Solo AXA' : '🔵 Solo Interno'}
                                                            </span>
                                                        </td>
                                                        <td style={{ fontSize: 11, color: 'var(--text-muted)', maxWidth: 200 }}>
                                                            {c.tipo_diferencia || '—'}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
