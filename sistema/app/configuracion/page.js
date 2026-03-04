'use client';
import { useState, useEffect, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, API_URL } from '@/lib/api';

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

    // ── Import Excel state ──
    const [importFile, setImportFile] = useState(null);
    const [importing, setImporting] = useState(false);
    const [importResult, setImportResult] = useState(null);
    const [applyingRules, setApplyingRules] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);

    const handleImportExcel = async () => {
        if (!importFile) return;
        setImporting(true);
        setImportResult(null);
        try {
            const formData = new FormData();
            formData.append('archivo', importFile);
            const res = await fetch(`${API_URL}/importar/csv-polizas`, {
                method: 'POST',
                body: formData,
            });
            const result = await res.json();
            if (!res.ok) throw new Error(result.detail || `Error ${res.status}`);
            setImportResult(result);
            setImportFile(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
        } catch (e) {
            setImportResult({ ok: false, mensaje: e.message, errores: [] });
        }
        setImporting(false);
    };

    const handleApplyRules = async () => {
        setApplyingRules(true);
        try {
            const res = await fetch(`${API_URL}/importar/aplicar-reglas`, { method: 'POST' });
            const result = await res.json();
            setImportResult(result);
        } catch (e) {
            setImportResult({ ok: false, mensaje: e.message });
        }
        setApplyingRules(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files[0];
        if (f && f.name.endsWith('.csv')) setImportFile(f);
    };

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
                    {/* ── IMPORT EXCEL PANEL ── */}
                    <div className="card" style={{ marginBottom: 20, background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08))' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                            <span style={{ fontSize: 24 }}>📥</span>
                            <div>
                                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Importar Pólizas desde CSV</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Sube un archivo CSV con encabezados para importar pólizas (limpia tabla antes de importar)</div>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: 12, alignItems: 'stretch', flexWrap: 'wrap' }}>
                            {/* Drop zone */}
                            <div
                                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                style={{
                                    flex: 1, minWidth: 250, padding: '24px 20px',
                                    border: `2px dashed ${dragOver ? '#3b82f6' : 'var(--border)'}`,
                                    borderRadius: 12, textAlign: 'center', cursor: 'pointer',
                                    background: dragOver ? 'rgba(59,130,246,0.1)' : 'var(--bg-main)',
                                    transition: 'all 0.2s',
                                }}
                            >
                                <input ref={fileInputRef} type="file" accept=".csv" style={{ display: 'none' }}
                                    onChange={(e) => setImportFile(e.target.files[0])} />
                                {importFile ? (
                                    <div>
                                        <div style={{ fontSize: 28, marginBottom: 6 }}>📄</div>
                                        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{importFile.name}</div>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(importFile.size / 1024 / 1024).toFixed(1)} MB — Listo para importar</div>
                                    </div>
                                ) : (
                                    <div>
                                        <div style={{ fontSize: 28, marginBottom: 6 }}>📂</div>
                                        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Arrastra tu CSV aquí o <span style={{ color: '#3b82f6', fontWeight: 600 }}>haz clic para buscar</span></div>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Formato: .csv con encabezados (POLIZA, NOMRAMO, FECINI, etc.)</div>
                                    </div>
                                )}
                            </div>

                            {/* Action buttons */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 180 }}>
                                <button className="btn btn-primary" disabled={!importFile || importing}
                                    onClick={handleImportExcel}
                                    style={{ padding: '12px 20px', fontSize: 13, flex: 1, opacity: !importFile ? 0.5 : 1 }}>
                                    {importing ? '⏳ Importando...' : '📥 Importar Pólizas'}
                                </button>
                                <button className="btn btn-ghost" disabled={applyingRules}
                                    onClick={handleApplyRules}
                                    style={{ padding: '12px 20px', fontSize: 13, flex: 1, border: '1px solid var(--border)' }}>
                                    {applyingRules ? '⏳ Procesando...' : '🧮 Aplicar Reglas'}
                                </button>
                            </div>
                        </div>

                        {/* Import result */}
                        {importResult && (
                            <div style={{
                                marginTop: 14, padding: '12px 16px', borderRadius: 10,
                                background: importResult.ok !== false ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
                                border: `1px solid ${importResult.ok !== false ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'}`,
                            }}>
                                <div style={{ fontSize: 13, fontWeight: 700, color: importResult.ok !== false ? '#10b981' : '#f43f5e', marginBottom: 4 }}>
                                    {importResult.ok !== false ? '✅ Importación exitosa' : '❌ Error en importación'}
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{importResult.mensaje}</div>
                                {importResult.nuevos > 0 && <div style={{ fontSize: 12, color: '#10b981', marginTop: 2 }}>📊 Nuevos: {importResult.nuevos} | Actualizados: {importResult.actualizados || 0}</div>}
                                {importResult.errores?.length > 0 && (
                                    <details style={{ marginTop: 6 }}>
                                        <summary style={{ fontSize: 11, color: '#f43f5e', cursor: 'pointer' }}>Ver {importResult.errores.length} errores</summary>
                                        <div style={{ fontSize: 11, fontFamily: 'monospace', marginTop: 4, maxHeight: 150, overflow: 'auto', color: 'var(--text-muted)' }}>
                                            {importResult.errores.map((e, i) => <div key={i}>{e}</div>)}
                                        </div>
                                    </details>
                                )}
                            </div>
                        )}
                    </div>

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
