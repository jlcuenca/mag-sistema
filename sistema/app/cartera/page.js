'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';

function diasParaVencer(fechaFin) {
    if (!fechaFin) return null;
    const hoy = new Date('2026-02-23');
    const fin = new Date(fechaFin);
    return Math.round((fin - hoy) / (1000 * 60 * 60 * 24));
}

function AlertaBadge({ dias }) {
    if (dias === null) return null;
    if (dias < 0) return <span className="badge badge-rose">⚠️ Vencida</span>;
    if (dias <= 30) return <span className="badge badge-rose">🔴 {dias}d</span>;
    if (dias <= 60) return <span className="badge badge-amber">🟡 {dias}d</span>;
    if (dias <= 90) return <span className="badge badge-blue">🔵 {dias}d</span>;
    return null;
}

export default function Cartera() {
    const [polizas, setPolizas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [horizonte, setHorizonte] = useState(90);

    useEffect(() => {
        setLoading(true);
        apiFetch('/polizas?limit=200&anio=2025')
            .then(d => {
                setPolizas(d.data || []);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    const proximasAVencer = polizas
        .filter(p => {
            const d = diasParaVencer(p.fecha_fin);
            return d !== null && d >= 0 && d <= horizonte;
        })
        .sort((a, b) => diasParaVencer(a.fecha_fin) - diasParaVencer(b.fecha_fin));

    const vencidas = polizas.filter(p => {
        const d = diasParaVencer(p.fecha_fin);
        return d !== null && d < 0;
    });

    const enRiesgo = polizas.filter(p => p.status_recibo === 'CANC/X F.PAGO');

    const stats = [
        { label: 'Pólizas vigentes', value: polizas.filter(p => p.status_recibo === 'PAGADA').length, icon: '✅', color: '#34d399' },
        { label: 'Vencen en 30 días', value: polizas.filter(p => { const d = diasParaVencer(p.fecha_fin); return d !== null && d >= 0 && d <= 30; }).length, icon: '🔴', color: '#f87171' },
        { label: 'Vencen en 60 días', value: polizas.filter(p => { const d = diasParaVencer(p.fecha_fin); return d !== null && d >= 31 && d <= 60; }).length, icon: '🟡', color: '#fbbf24' },
        { label: 'En riesgo (F.Pago)', value: enRiesgo.length, icon: '⚠️', color: '#fb923c' },
    ];

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Cartera</div>
                        <div className="header-subtitle">Seguimiento de vencimientos y riesgo</div>
                    </div>
                    <div className="header-right">
                        <select value={horizonte} onChange={e => setHorizonte(+e.target.value)}>
                            <option value={30}>30 días</option>
                            <option value={60}>60 días</option>
                            <option value={90}>90 días</option>
                        </select>
                        <span className="badge badge-amber">📅 Próximos {horizonte} días</span>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* KPIs */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
                        {stats.map((s, i) => (
                            <div key={i} className="kpi-card">
                                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: s.color }} />
                                <span className="kpi-icon">{s.icon}</span>
                                <div className="kpi-label">{s.label}</div>
                                <div className="kpi-value" style={{ color: s.color }}>{loading ? '—' : s.value}</div>
                            </div>
                        ))}
                    </div>

                    {/* Pólizas próximas a vencer */}
                    <div className="card" style={{ marginBottom: 24, padding: 0, overflow: 'hidden' }}>
                        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Próximas a vencer</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Pólizas que vencen en los próximos {horizonte} días</div>
                            </div>
                            <span className="badge badge-amber">📅 {proximasAVencer.length} pólizas</span>
                        </div>
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Póliza</th>
                                        <th>Asegurado</th>
                                        <th>Agente</th>
                                        <th>Ramo</th>
                                        <th>Gama</th>
                                        <th>F. Inicio</th>
                                        <th>F. Vencimiento</th>
                                        <th>Prima Neta</th>
                                        <th>Días</th>
                                        <th>Alerta</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        Array(5).fill(0).map((_, i) => (
                                            <tr key={i}>{Array(10).fill(0).map((_, j) => <td key={j}><div className="loading-skeleton" style={{ height: 12, width: '80%' }} /></td>)}</tr>
                                        ))
                                    ) : proximasAVencer.length === 0 ? (
                                        <tr>
                                            <td colSpan={10}>
                                                <div className="empty-state">
                                                    <div className="empty-state-icon">✅</div>
                                                    <div className="empty-state-title">Sin vencimientos próximos</div>
                                                    <div className="empty-state-desc">No hay pólizas que venzan en {horizonte} días</div>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : proximasAVencer.map((p, i) => {
                                        const dias = diasParaVencer(p.fecha_fin);
                                        return (
                                            <tr key={i} style={{ background: dias <= 30 ? 'rgba(244,63,94,0.03)' : dias <= 60 ? 'rgba(245,158,11,0.03)' : 'transparent' }}>
                                                <td><code style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>{p.poliza_original}</code></td>
                                                <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{p.asegurado_nombre}</td>
                                                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{p.agente_nombre?.split(',')[0]}</td>
                                                <td>
                                                    <span style={{ fontSize: 11, fontWeight: 600, color: p.ramo_codigo === 11 ? '#818cf8' : '#34d399' }}>
                                                        {p.ramo_codigo === 11 ? 'Vida' : 'GMM'}
                                                    </span>
                                                </td>
                                                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{p.gama || '—'}</td>
                                                <td style={{ fontSize: 12 }}>{p.fecha_inicio}</td>
                                                <td style={{ fontSize: 12, fontWeight: 500, color: dias <= 30 ? 'var(--accent-rose)' : 'var(--text-primary)' }}>{p.fecha_fin}</td>
                                                <td style={{ fontWeight: 700 }}>${(p.prima_neta || 0).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
                                                <td style={{ fontWeight: 700, color: dias <= 30 ? 'var(--accent-rose)' : dias <= 60 ? 'var(--accent-amber)' : 'var(--text-muted)' }}>{dias}d</td>
                                                <td><AlertaBadge dias={dias} /></td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* En riesgo por falta de pago */}
                    {enRiesgo.length > 0 && (
                        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent-rose)' }}>⚠️ En riesgo — Canceladas por Falta de Pago</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Requieren gestión urgente de cobranza</div>
                                </div>
                                <span className="badge badge-rose">{enRiesgo.length} pólizas</span>
                            </div>
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Póliza</th>
                                            <th>Asegurado</th>
                                            <th>Agente</th>
                                            <th>Ramo</th>
                                            <th>F. Inicio</th>
                                            <th>Prima Neta</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {enRiesgo.map((p, i) => (
                                            <tr key={i} style={{ background: 'rgba(244,63,94,0.03)' }}>
                                                <td><code style={{ background: 'rgba(244,63,94,0.1)', color: '#fda4af', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>{p.poliza_original}</code></td>
                                                <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{p.asegurado_nombre}</td>
                                                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{p.agente_nombre?.split(',')[0]}</td>
                                                <td><span style={{ fontSize: 11, fontWeight: 600, color: p.ramo_codigo === 11 ? '#818cf8' : '#34d399' }}>{p.ramo_codigo === 11 ? 'Vida' : 'GMM'}</span></td>
                                                <td style={{ fontSize: 12 }}>{p.fecha_inicio}</td>
                                                <td style={{ fontWeight: 700 }}>${(p.prima_neta || 0).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
                                                <td><span className="status-pill status-cancelada">Cancelada F.Pago</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
