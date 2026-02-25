'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';

const GRUPO_CONFIG = {
    umbrales: { icon: '📏', label: 'Umbrales', color: '#f59e0b' },
    tipos_cambio: { icon: '💱', label: 'Tipos de Cambio', color: '#3b82f6' },
    catalogos: { icon: '📋', label: 'Catálogos', color: '#10b981' },
    general: { icon: '⚙️', label: 'General', color: '#8b5cf6' },
};

export default function Configuracion() {
    const [data, setData] = useState({ configuraciones: [], grupos: [] });
    const [loading, setLoading] = useState(true);
    const [grupoFilter, setGrupoFilter] = useState('');
    const [editando, setEditando] = useState(null);     // clave being edited
    const [editValor, setEditValor] = useState('');
    const [saving, setSaving] = useState(false);

    const fetchData = () => {
        setLoading(true);
        const p = grupoFilter ? `?grupo=${grupoFilter}` : '';
        apiFetch(`/configuracion${p}`)
            .then(d => { setData(d || { configuraciones: [], grupos: [] }); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [grupoFilter]);

    const handleSave = async (clave) => {
        setSaving(true);
        try {
            await apiFetch(`/configuracion/${clave}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ valor: editValor }),
            });
            setEditando(null);
            fetchData();
        } catch (e) { alert('Error al guardar'); }
        setSaving(false);
    };

    const startEdit = (c) => {
        setEditando(c.clave);
        setEditValor(c.valor || '');
    };

    const configs = data.configuraciones || [];
    const grupos = data.grupos || [];

    // Group configs by grupo
    const grouped = {};
    configs.forEach(c => {
        const g = c.grupo || 'otros';
        if (!grouped[g]) grouped[g] = [];
        grouped[g].push(c);
    });

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Configuración del Sistema</div>
                        <div className="header-subtitle">Gestión de umbrales, tipos de cambio y catálogos</div>
                    </div>
                    <div className="header-right">
                        <select value={grupoFilter} onChange={e => setGrupoFilter(e.target.value)} style={{ padding: '7px 12px' }}>
                            <option value="">Todos los grupos</option>
                            {grupos.map(g => (
                                <option key={g} value={g}>{(GRUPO_CONFIG[g]?.label) || g}</option>
                            ))}
                        </select>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* Group KPI cards */}
                    <div className="kpi-grid" style={{ gridTemplateColumns: `repeat(${Object.keys(GRUPO_CONFIG).length}, 1fr)` }}>
                        {Object.entries(GRUPO_CONFIG).map(([key, cfg]) => {
                            const count = configs.filter(c => c.grupo === key).length;
                            return (
                                <div key={key} className="kpi-card" style={{ borderTop: `3px solid ${cfg.color}`, cursor: 'pointer', opacity: grupoFilter && grupoFilter !== key ? 0.5 : 1 }}
                                    onClick={() => setGrupoFilter(grupoFilter === key ? '' : key)}>
                                    <div style={{ fontSize: 22, marginBottom: 4 }}>{cfg.icon}</div>
                                    <div className="kpi-value" style={{ color: cfg.color, fontSize: 24 }}>{count}</div>
                                    <div className="kpi-label">{cfg.label}</div>
                                </div>
                            );
                        })}
                    </div>

                    {loading ? (
                        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                            Cargando configuración...
                        </div>
                    ) : (
                        Object.entries(grouped).map(([grupo, items]) => {
                            const cfg = GRUPO_CONFIG[grupo] || { icon: '📦', label: grupo, color: '#6b7280' };
                            return (
                                <div key={grupo} className="card" style={{ marginBottom: 16 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                                        <span style={{ fontSize: 22 }}>{cfg.icon}</span>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: cfg.color }}>{cfg.label}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{items.length} parámetros</div>
                                        </div>
                                    </div>

                                    <div style={{ display: 'grid', gap: 10 }}>
                                        {items.map(c => {
                                            const isEditing = editando === c.clave;
                                            const isJson = c.tipo === 'json';
                                            let displayVal = c.valor;
                                            if (isJson) {
                                                try {
                                                    const arr = JSON.parse(c.valor);
                                                    displayVal = Array.isArray(arr) ? arr.join(', ') : c.valor;
                                                } catch { displayVal = c.valor; }
                                            }

                                            return (
                                                <div key={c.clave} style={{
                                                    background: 'var(--bg-main)', borderRadius: 10, padding: '14px 18px',
                                                    border: isEditing ? `1px solid ${cfg.color}` : '1px solid var(--border)',
                                                    transition: 'border-color 0.2s',
                                                }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20 }}>
                                                        <div style={{ flex: 1 }}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                                                <code style={{ fontSize: 12, color: cfg.color, background: `${cfg.color}1a`, padding: '2px 8px', borderRadius: 4 }}>{c.clave}</code>
                                                                <span className="badge badge-info" style={{ fontSize: 9 }}>{c.tipo}</span>
                                                            </div>
                                                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>{c.descripcion}</div>

                                                            {isEditing ? (
                                                                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                                                    {isJson ? (
                                                                        <textarea value={editValor} onChange={e => setEditValor(e.target.value)} rows={3}
                                                                            style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: 12, resize: 'vertical' }} />
                                                                    ) : (
                                                                        <input value={editValor} onChange={e => setEditValor(e.target.value)}
                                                                            type={c.tipo === 'numero' ? 'number' : 'text'} step={c.tipo === 'numero' ? '0.001' : undefined}
                                                                            style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontFamily: 'monospace' }} />
                                                                    )}
                                                                    <button className="btn btn-primary" style={{ padding: '6px 14px', fontSize: 12 }} disabled={saving}
                                                                        onClick={() => handleSave(c.clave)}>💾 Guardar</button>
                                                                    <button className="btn btn-ghost" style={{ padding: '6px 14px', fontSize: 12 }}
                                                                        onClick={() => setEditando(null)}>✕</button>
                                                                </div>
                                                            ) : (
                                                                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', fontFamily: isJson ? 'monospace' : 'inherit', fontSize: isJson ? 11 : 14 }}>
                                                                    {c.tipo === 'numero' ? (
                                                                        <span style={{ color: '#60a5fa' }}>{displayVal}</span>
                                                                    ) : isJson ? (
                                                                        <span style={{ color: '#a78bfa', wordBreak: 'break-all' }}>{displayVal}</span>
                                                                    ) : (
                                                                        displayVal
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {!isEditing && (
                                                            <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 11, whiteSpace: 'nowrap' }}
                                                                onClick={() => startEdit(c)}>✏️ Editar</button>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </main>
        </div>
    );
}
