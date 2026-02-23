'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';

function fmt(n) {
    if (!n) return '$0';
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}

export default function Agentes() {
    const [agentes, setAgentes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filtro, setFiltro] = useState('ACTIVO');

    useEffect(() => {
        setLoading(true);
        const params = filtro !== 'TODOS' ? `?situacion=${filtro}` : '';
        apiFetch(`/agentes${params}`)
            .then(d => { setAgentes(d.data || []); setLoading(false); })
            .catch(() => setLoading(false));
    }, [filtro]);

    const activos = agentes.filter(a => a.situacion === 'ACTIVO').length;
    const cancelados = agentes.filter(a => a.situacion === 'CANCELADO').length;

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Directorio de Agentes</div>
                        <div className="header-subtitle">Fuerza de ventas MAG</div>
                    </div>
                    <div className="header-right">
                        <span className="badge badge-emerald">✅ {activos} Activos</span>
                        {cancelados > 0 && <span className="badge badge-rose">⛔ {cancelados} Cancelados</span>}
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* Filtro de situación */}
                    <div className="filters-bar" style={{ marginBottom: 24 }}>
                        {['ACTIVO', 'CANCELADO', 'TODOS'].map(s => (
                            <button
                                key={s}
                                className={`btn ${filtro === s ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setFiltro(s)}
                            >
                                {s === 'ACTIVO' ? '✅ Activos' : s === 'CANCELADO' ? '⛔ Cancelados' : '📋 Todos'}
                            </button>
                        ))}
                    </div>

                    {/* Grid de agentes */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
                        {loading ? (
                            Array(6).fill(0).map((_, i) => (
                                <div key={i} className="card" style={{ height: 180 }}>
                                    <div className="loading-skeleton" style={{ height: 14, width: '60%', marginBottom: 12 }} />
                                    <div className="loading-skeleton" style={{ height: 10, width: '40%', marginBottom: 20 }} />
                                    <div className="loading-skeleton" style={{ height: 10, width: '80%', marginBottom: 8 }} />
                                    <div className="loading-skeleton" style={{ height: 10, width: '60%' }} />
                                </div>
                            ))
                        ) : agentes.length === 0 ? (
                            <div className="empty-state" >
                                <div className="empty-state-icon">👥</div>
                                <div className="empty-state-title">Sin agentes</div>
                                <div className="empty-state-desc">No hay agentes con este filtro</div>
                            </div>
                        ) : agentes.map((a, i) => (
                            <div key={i} className="card" style={{ position: 'relative', overflow: 'hidden' }}>
                                {/* Top accent */}
                                <div style={{
                                    position: 'absolute', top: 0, left: 0, right: 0, height: 3,
                                    background: a.situacion === 'ACTIVO' ? 'linear-gradient(90deg, #3b82f6, #10b981)' : 'linear-gradient(90deg, #f43f5e, #f97316)'
                                }} />

                                {/* Header del card */}
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 16 }}>
                                    <div style={{
                                        width: 44, height: 44, borderRadius: 12,
                                        background: a.situacion === 'ACTIVO' ? 'linear-gradient(135deg, #3b82f6, #6366f1)' : 'linear-gradient(135deg, #64748b, #475569)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: 18, fontWeight: 800, color: 'white', flexShrink: 0
                                    }}>
                                        {(a.nombre_completo || '?').charAt(0)}
                                    </div>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                                            {a.nombre_completo}
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                                            <code style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa', padding: '1px 6px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>
                                                {a.codigo_agente}
                                            </code>
                                            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.rol}</span>
                                        </div>
                                    </div>
                                    <span className={a.situacion === 'ACTIVO' ? 'badge badge-emerald' : 'badge badge-rose'} style={{ flexShrink: 0 }}>
                                        {a.situacion === 'ACTIVO' ? '✅' : '⛔'} {a.situacion}
                                    </span>
                                </div>

                                {/* Info */}
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
                                    {[
                                        { label: 'Territorio', val: a.territorio },
                                        { label: 'Oficina', val: a.oficina },
                                        { label: 'Gerencia', val: a.gerencia },
                                        { label: 'CC', val: a.centro_costos },
                                    ].map(f => (
                                        <div key={f.label}>
                                            <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{f.label}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>{f.val || '—'}</div>
                                        </div>
                                    ))}
                                </div>

                                <div style={{ height: 1, background: 'var(--border)', margin: '12px 0' }} />

                                {/* KPIs del agente */}
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)' }}>{a.total_polizas || 0}</div>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>Total</div>
                                    </div>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: 18, fontWeight: 800, color: '#60a5fa' }}>{a.polizas_nuevas_2025 || 0}</div>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>Nuevas 2025</div>
                                    </div>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: 18, fontWeight: 800, color: '#34d399' }}>{fmt(a.prima_nueva_2025 || 0)}</div>
                                        <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>Prima 2025</div>
                                    </div>
                                </div>

                                {a.fecha_alta && (
                                    <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                                        Alta: {a.fecha_alta}
                                        {a.fecha_cancelacion && <span style={{ color: 'var(--accent-rose)', marginLeft: 12 }}>• Baja: {a.fecha_cancelacion}</span>}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
}
