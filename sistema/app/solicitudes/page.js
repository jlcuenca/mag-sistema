'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, getSolicitudDocUrl } from '@/lib/api';

const ESTADOS = ['TRAMITE', 'EMITIDA', 'PAGADA', 'RECHAZADA', 'CANCELADA'];
const ESTADO_CONFIG = {
    TRAMITE: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '📝', label: 'En Trámite' },
    EMITIDA: { color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', icon: '📄', label: 'Emitida' },
    PAGADA: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '✅', label: 'Pagada' },
    RECHAZADA: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '❌', label: 'Rechazada' },
    CANCELADA: { color: '#6b7280', bg: 'rgba(107,114,128,0.12)', icon: '🚫', label: 'Cancelada' },
};

function fmt(n) {
    if (n == null) return '$0';
    if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}

const EMPTY_FORM = { agente_id: '', contratante_id: '', ramo: 'VIDA', plan: '', prima_estimada: '', notas: '' };

export default function Solicitudes() {
    const [data, setData] = useState({ solicitudes: [], pipeline: {} });
    const [loading, setLoading] = useState(true);
    const [filtroEstado, setFiltroEstado] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ ...EMPTY_FORM });
    const [saving, setSaving] = useState(false);
    const [viewMode, setViewMode] = useState('kanban'); // kanban | tabla
    const [docViewer, setDocViewer] = useState(null); // { folio, url }

    const fetchData = () => {
        setLoading(true);
        const p = filtroEstado ? `?estado=${filtroEstado}` : '';
        apiFetch(`/solicitudes${p}`)
            .then(d => { setData(d || { solicitudes: [], pipeline: {} }); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [filtroEstado]);

    const handleCreate = async () => {
        setSaving(true);
        const body = { ...form, prima_estimada: parseFloat(form.prima_estimada) || 0 };
        if (!body.agente_id) delete body.agente_id;
        if (!body.contratante_id) delete body.contratante_id;
        try {
            await apiFetch('/solicitudes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            setShowModal(false);
            setForm({ ...EMPTY_FORM });
            fetchData();
        } catch (e) { alert('Error al crear'); }
        setSaving(false);
    };

    const updateEstado = async (id, nuevoEstado) => {
        const body = { estado: nuevoEstado };
        if (nuevoEstado === 'PAGADA') body.fecha_pago = new Date().toISOString().split('T')[0];
        if (nuevoEstado === 'EMITIDA') body.fecha_emision = new Date().toISOString().split('T')[0];
        await apiFetch(`/solicitudes/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        fetchData();
    };

    const pipe = data.pipeline || {};
    const sols = data.solicitudes || [];

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Pipeline de Solicitudes</div>
                        <div className="header-subtitle">Tracking: Trámite → Emitida → Pagada</div>
                    </div>
                    <div className="header-right">
                        <div style={{ display: 'flex', gap: 4, background: 'var(--bg-card)', padding: 3, borderRadius: 10, border: '1px solid var(--border)' }}>
                            <button className={`btn ${viewMode === 'kanban' ? 'btn-primary' : 'btn-ghost'}`} style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => setViewMode('kanban')}>🗂️ Kanban</button>
                            <button className={`btn ${viewMode === 'tabla' ? 'btn-primary' : 'btn-ghost'}`} style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => setViewMode('tabla')}>📋 Tabla</button>
                        </div>
                        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Nueva Solicitud</button>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* Pipeline KPIs */}
                    <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-blue)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-blue)', fontSize: 28 }}>{pipe.total || 0}</div>
                            <div className="kpi-label">Total Solicitudes</div>
                        </div>
                        {ESTADOS.slice(0, 3).map(e => {
                            const cfg = ESTADO_CONFIG[e];
                            const count = pipe[e.toLowerCase()] || 0;
                            return (
                                <div key={e} className="kpi-card" style={{ borderTop: `3px solid ${cfg.color}`, cursor: 'pointer' }} onClick={() => setFiltroEstado(filtroEstado === e ? '' : e)}>
                                    <div style={{ fontSize: 20, marginBottom: 4 }}>{cfg.icon}</div>
                                    <div className="kpi-value" style={{ color: cfg.color, fontSize: 26 }}>{count}</div>
                                    <div className="kpi-label">{cfg.label}</div>
                                </div>
                            );
                        })}
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-emerald)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-emerald)', fontSize: 18 }}>{fmt(pipe.prima_estimada_total)}</div>
                            <div className="kpi-label">Prima Estimada</div>
                        </div>
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-cyan)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-cyan)', fontSize: 18 }}>{fmt(pipe.prima_pagada_total)}</div>
                            <div className="kpi-label">Prima Pagada</div>
                        </div>
                    </div>

                    {/* Kanban View */}
                    {viewMode === 'kanban' && (
                        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${ESTADOS.length}, 1fr)`, gap: 14 }}>
                            {ESTADOS.map(estado => {
                                const cfg = ESTADO_CONFIG[estado];
                                const cards = sols.filter(s => s.estado === estado);
                                return (
                                    <div key={estado} style={{ background: 'var(--bg-card)', borderRadius: 14, border: '1px solid var(--border)', overflow: 'hidden' }}>
                                        <div style={{ padding: '12px 16px', background: cfg.bg, borderBottom: `2px solid ${cfg.color}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span style={{ fontWeight: 700, fontSize: 13, color: cfg.color }}>{cfg.icon} {cfg.label}</span>
                                            <span className="badge" style={{ background: cfg.color, color: '#fff', fontSize: 11 }}>{cards.length}</span>
                                        </div>
                                        <div style={{ padding: 10, display: 'flex', flexDirection: 'column', gap: 8, minHeight: 120 }}>
                                            {cards.length === 0 ? (
                                                <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 12 }}>Sin solicitudes</div>
                                            ) : cards.map(s => (
                                                <div key={s.id} style={{ background: 'var(--bg-main)', borderRadius: 10, padding: 12, border: '1px solid var(--border)', transition: 'transform 0.15s', cursor: 'default' }}
                                                    onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
                                                    onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                                        <code style={{ fontSize: 10, color: cfg.color, background: cfg.bg, padding: '2px 6px', borderRadius: 4 }}>{s.folio}</code>
                                                        <span className="badge" style={{ fontSize: 9 }}>{s.ramo}</span>
                                                    </div>
                                                    <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--text-primary)' }}>
                                                        {s.contratante_nombre || s.plan || '—'}
                                                    </div>
                                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                                                        {s.agente_nombre || 'Sin agente'} · {fmt(s.prima_estimada)}
                                                    </div>
                                                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 8 }}>
                                                        📅 {s.fecha_solicitud || '—'}
                                                    </div>
                                                    {/* Quick actions */}
                                                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
                                                        <button
                                                            className="btn btn-ghost"
                                                            title={`Ver PDF solicitud ${s.folio}`}
                                                            onClick={() => setDocViewer({ folio: s.folio, url: getSolicitudDocUrl(s.folio), contratante: s.contratante_nombre })}
                                                            style={{ padding: '3px 8px', fontSize: 10, color: '#60a5fa' }}
                                                        >
                                                            📄 Ver Doc
                                                        </button>
                                                        {estado === 'TRAMITE' && (
                                                            <>
                                                                <button className="btn btn-ghost" style={{ padding: '3px 8px', fontSize: 10, color: '#3b82f6' }} onClick={() => updateEstado(s.id, 'EMITIDA')}>📄 Emitir</button>
                                                                <button className="btn btn-ghost" style={{ padding: '3px 8px', fontSize: 10, color: '#ef4444' }} onClick={() => updateEstado(s.id, 'RECHAZADA')}>❌ Rechazar</button>
                                                            </>
                                                        )}
                                                        {estado === 'EMITIDA' && (
                                                            <>
                                                                <button className="btn btn-ghost" style={{ padding: '3px 8px', fontSize: 10, color: '#10b981' }} onClick={() => updateEstado(s.id, 'PAGADA')}>✅ Pagada</button>
                                                                <button className="btn btn-ghost" style={{ padding: '3px 8px', fontSize: 10, color: '#6b7280' }} onClick={() => updateEstado(s.id, 'CANCELADA')}>🚫 Cancelar</button>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Table View */}
                    {viewMode === 'tabla' && (
                        <div className="card">
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Folio</th>
                                            <th style={{ textAlign: 'center', width: 50 }}>Doc</th>
                                            <th>Estado</th>
                                            <th>Ramo</th>
                                            <th>Plan</th>
                                            <th>Contratante</th>
                                            <th>Agente</th>
                                            <th style={{ textAlign: 'right' }}>Prima Est.</th>
                                            <th>Fecha Sol.</th>
                                            <th>Fecha Emisión</th>
                                            <th>Fecha Pago</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? Array(5).fill(0).map((_, i) => (
                                            <tr key={i}>{Array(10).fill(0).map((_, j) => <td key={j}><div className="loading-skeleton" style={{ height: 14, width: '70%' }} /></td>)}</tr>
                                        )) : sols.length === 0 ? (
                                            <tr><td colSpan={10} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                                                <div style={{ fontSize: 40, marginBottom: 10 }}>📝</div>
                                                Sin solicitudes. Crea una nueva para comenzar.
                                            </td></tr>
                                        ) : sols.map(s => {
                                            const cfg = ESTADO_CONFIG[s.estado] || ESTADO_CONFIG.TRAMITE;
                                            return (
                                                <tr key={s.id}>
                                                    <td><code style={{ fontSize: 11 }}>{s.folio}</code></td>
                                                    <td style={{ textAlign: 'center' }}>
                                                        <button
                                                            className="btn btn-ghost"
                                                            title={`Ver PDF solicitud ${s.folio}`}
                                                            onClick={() => setDocViewer({ folio: s.folio, url: getSolicitudDocUrl(s.folio), contratante: s.contratante_nombre })}
                                                            style={{ padding: '3px 6px', fontSize: 14, lineHeight: 1, borderRadius: 6, minWidth: 30 }}
                                                        >
                                                            📄
                                                        </button>
                                                    </td>
                                                    <td><span className="badge" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}30` }}>{cfg.icon} {cfg.label}</span></td>
                                                    <td><span className="badge badge-info">{s.ramo}</span></td>
                                                    <td>{s.plan || '—'}</td>
                                                    <td>{s.contratante_nombre || '—'}</td>
                                                    <td style={{ fontSize: 12 }}>{s.agente_nombre || '—'}</td>
                                                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(s.prima_estimada)}</td>
                                                    <td style={{ fontSize: 12 }}>{s.fecha_solicitud || '—'}</td>
                                                    <td style={{ fontSize: 12 }}>{s.fecha_emision || '—'}</td>
                                                    <td style={{ fontSize: 12 }}>{s.fecha_pago || '—'}</td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>

                {/* Create Modal */}
                {showModal && (
                    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
                        onClick={() => setShowModal(false)}>
                        <div className="card" style={{ width: 480 }} onClick={e => e.stopPropagation()}>
                            <h3 style={{ marginBottom: 20 }}>📝 Nueva Solicitud</h3>
                            <div style={{ display: 'grid', gap: 14 }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                    <div>
                                        <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Ramo</label>
                                        <select value={form.ramo} onChange={e => setForm({ ...form, ramo: e.target.value })}
                                            style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}>
                                            <option>VIDA</option>
                                            <option>GMM</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Prima Estimada</label>
                                        <input type="number" value={form.prima_estimada} onChange={e => setForm({ ...form, prima_estimada: e.target.value })} placeholder="25000"
                                            style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
                                    </div>
                                </div>
                                <div>
                                    <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Plan / Producto</label>
                                    <input value={form.plan} onChange={e => setForm({ ...form, plan: e.target.value })} placeholder="VIDA Y AHORRO, FLEX PLUS..."
                                        style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
                                </div>
                                <div>
                                    <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Notas</label>
                                    <textarea value={form.notas} onChange={e => setForm({ ...form, notas: e.target.value })} placeholder="Observaciones adicionales..." rows={3}
                                        style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', resize: 'vertical' }} />
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
                                <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancelar</button>
                                <button className="btn btn-primary" disabled={saving} onClick={handleCreate}>
                                    {saving ? 'Creando...' : 'Crear Solicitud'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ═══ PDF Viewer Modal ═══ */}
                {docViewer && (
                    <div
                        style={{
                            position: 'fixed', inset: 0, zIndex: 1000,
                            background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            animation: 'fadeIn 0.2s ease',
                        }}
                        onClick={() => setDocViewer(null)}
                    >
                        <div
                            style={{
                                width: '85vw', maxWidth: 1000, height: '90vh',
                                background: 'var(--bg-card)', borderRadius: 16,
                                border: '1px solid var(--border)',
                                boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
                                display: 'flex', flexDirection: 'column',
                                overflow: 'hidden',
                                animation: 'slideUp 0.25s ease',
                            }}
                            onClick={e => e.stopPropagation()}
                        >
                            {/* Header */}
                            <div style={{
                                padding: '16px 24px', display: 'flex', justifyContent: 'space-between',
                                alignItems: 'center', borderBottom: '1px solid var(--border)',
                                background: 'linear-gradient(135deg, rgba(245,158,11,0.08), rgba(59,130,246,0.05))',
                            }}>
                                <div>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                                        📝 Documento de Solicitud
                                        <code style={{ fontSize: 12, background: 'rgba(245,158,11,0.15)', color: '#fbbf24', padding: '2px 8px', borderRadius: 4 }}>
                                            {docViewer.folio}
                                        </code>
                                    </div>
                                    {docViewer.contratante && (
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                                            Contratante: {docViewer.contratante}
                                        </div>
                                    )}
                                </div>
                                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                    <a
                                        href={docViewer.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn btn-ghost"
                                        style={{ padding: '6px 14px', fontSize: 12, textDecoration: 'none', color: '#60a5fa' }}
                                    >
                                        🔗 Abrir en nueva pestaña
                                    </a>
                                    <a
                                        href={docViewer.url}
                                        download
                                        className="btn btn-ghost"
                                        style={{ padding: '6px 14px', fontSize: 12, textDecoration: 'none', color: '#34d399' }}
                                    >
                                        ⬇ Descargar
                                    </a>
                                    <button
                                        className="btn btn-ghost"
                                        onClick={() => setDocViewer(null)}
                                        style={{ padding: '6px 10px', fontSize: 16, lineHeight: 1 }}
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>

                            {/* PDF Embed */}
                            <div style={{ flex: 1, background: '#1a1a2e' }}>
                                <iframe
                                    src={docViewer.url}
                                    style={{ width: '100%', height: '100%', border: 'none' }}
                                    title={`Solicitud ${docViewer.folio}`}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
