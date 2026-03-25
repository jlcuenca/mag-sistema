'use client';
import { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, getPolizaDocUrl } from '@/lib/api';

const MESES_ABR = { '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic' };

function StatusPill({ status }) {
    if (status === 'PAGADA') return <span className="status-pill status-pagada">Pagada</span>;
    if (status?.includes('CANC')) return <span className="status-pill status-cancelada">Cancelada</span>;
    return <span className="status-pill status-no-aplica">{status}</span>;
}

function TipoPill({ tipo, formalFlag }) {
    // La regla de negocio de flag_nueva_formal tiene prioridad sobre el tipo crudo de importación
    if (formalFlag === 1) return <span className="status-pill status-nueva">Nueva</span>;
    if (formalFlag === 0) return <span className="status-pill status-subsecuente">Subsec.</span>;
    
    if (tipo === 'NUEVA') return <span className="status-pill status-nueva">Nueva</span>;
    if (tipo === 'SUBSECUENTE') return <span className="status-pill status-subsecuente">Subsec.</span>;
    return <span className="status-pill status-no-aplica">No aplica</span>;
}

export default function Polizas() {
    const [polizas, setPolizas] = useState([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(1);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ ramo: '', tipo: '', anio: '', q: '' });
    const [docViewer, setDocViewer] = useState(null); // { poliza, url }

    const fetchPolizas = useCallback(() => {
        setLoading(true);
        const params = new URLSearchParams({ page, limit: 50 });
        Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
        apiFetch(`/polizas?${params}`)
            .then(d => {
                setPolizas(d.data || []);
                setTotal(d.total || 0);
                setPages(d.pages || 1);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [page, filters]);

    useEffect(() => { fetchPolizas(); }, [fetchPolizas]);

    const handleFilter = (key, val) => {
        setFilters(f => ({ ...f, [key]: val }));
        setPage(1);
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Pólizas</div>
                        <div className="header-subtitle">{total.toLocaleString()} registros encontrados</div>
                    </div>
                    <div className="header-right">
                        <button className="btn btn-primary" onClick={() => window.print()}>⬇ Exportar</button>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* Filtros */}
                    <div className="filters-bar">
                        <div className="filter-group">
                            <span className="filter-label">🔍</span>
                            <input
                                type="search"
                                placeholder="Buscar póliza, asegurado..."
                                value={filters.q}
                                onChange={e => handleFilter('q', e.target.value)}
                                style={{ width: 220 }}
                            />
                        </div>
                        <div className="filter-group">
                            <span className="filter-label">Ramo</span>
                            <select value={filters.ramo} onChange={e => handleFilter('ramo', e.target.value)}>
                                <option value="">Todos</option>
                                <option value="vida">Vida Individual</option>
                                <option value="gmm">GMM Individual</option>
                                <option value="autos">Autos</option>
                            </select>
                        </div>
                        <div className="filter-group">
                            <span className="filter-label">Tipo</span>
                            <select value={filters.tipo} onChange={e => handleFilter('tipo', e.target.value)}>
                                <option value="">Todos</option>
                                <option value="NUEVA">Nueva</option>
                                <option value="SUBSECUENTE">Subsecuente</option>
                                <option value="NO_APLICA">No aplica</option>
                            </select>
                        </div>
                        <div className="filter-group">
                            <span className="filter-label">Año</span>
                            <select value={filters.anio} onChange={e => handleFilter('anio', e.target.value)}>
                                <option value="">Todos</option>
                                {[2022, 2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
                            </select>
                        </div>
                        <button className="btn btn-ghost" onClick={() => { setFilters({ ramo: '', tipo: '', anio: '', q: '' }); setPage(1); }}>
                            ✕ Limpiar
                        </button>
                    </div>

                    {/* Tabla */}
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Póliza</th>
                                        <th style={{ textAlign: 'center', width: 50 }}>Doc</th>
                                        <th>Asegurado</th>
                                        <th>Agente</th>
                                        <th>Ramo</th>
                                        <th>Plan / Gama</th>
                                        <th>F. Inicio</th>
                                        <th>Forma Pago</th>
                                        <th>Prima Neta</th>
                                        <th>Status</th>
                                        <th>Tipo</th>
                                        <th>Prima Tipo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        Array(10).fill(0).map((_, i) => (
                                            <tr key={i}>
                                                {Array(12).fill(0).map((_, j) => (
                                                    <td key={j}><div className="loading-skeleton" style={{ height: 14, width: '80%' }} /></td>
                                                ))}
                                            </tr>
                                        ))
                                    ) : polizas.length === 0 ? (
                                        <tr>
                                            <td colSpan={12}>
                                                <div className="empty-state">
                                                    <div className="empty-state-icon">📋</div>
                                                    <div className="empty-state-title">Sin resultados</div>
                                                    <div className="empty-state-desc">Ajusta los filtros para ver pólizas</div>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : polizas.map((p, i) => (
                                        <tr key={i}>
                                            <td>
                                                <code style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>
                                                    {p.poliza_original}
                                                </code>
                                            </td>
                                            <td style={{ textAlign: 'center' }}>
                                                <button
                                                    className="btn btn-ghost"
                                                    title={`Ver PDF: ${p.poliza_original}`}
                                                    onClick={() => setDocViewer({ poliza: p.poliza_original, url: getPolizaDocUrl(p.poliza_original), asegurado: p.asegurado_nombre })}
                                                    style={{ padding: '3px 6px', fontSize: 14, lineHeight: 1, borderRadius: 6, minWidth: 30 }}
                                                >
                                                    📄
                                                </button>
                                            </td>
                                            <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{p.asegurado_nombre}</span>
                                            </td>
                                            <td>
                                                <div style={{ fontSize: 12 }}>
                                                    <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{p.agente_nombre?.split(',')[0]}</div>
                                                    <div style={{ color: 'var(--text-muted)' }}>{p.codigo_agente}</div>
                                                </div>
                                            </td>
                                            <td>
                                                <span className={`badge ${p.ramo_codigo === 11 ? 'badge-indigo' : p.ramo_codigo === 90 ? 'badge-blue' : 'badge-emerald'}`} style={{ background: p.ramo_codigo === 11 ? 'rgba(99,102,241,0.15)' : p.ramo_codigo === 90 ? 'rgba(59,130,246,0.15)' : 'rgba(16,185,129,0.15)', color: p.ramo_codigo === 11 ? '#818cf8' : p.ramo_codigo === 90 ? '#60a5fa' : '#34d399', borderRadius: 20, padding: '3px 8px', fontSize: 11, fontWeight: 600 }}>
                                                    {p.ramo_codigo === 11 ? 'Vida' : p.ramo_codigo === 90 ? 'Autos' : 'GMM'}
                                                </span>
                                            </td>
                                            <td>
                                                <div style={{ fontSize: 12 }}>
                                                    <div style={{ color: 'var(--text-primary)' }}>{p.plan}</div>
                                                    {p.gama && <div style={{ color: 'var(--text-muted)' }}>{p.gama}</div>}
                                                </div>
                                            </td>
                                            <td style={{ fontSize: 12 }}>
                                                {p.fecha_inicio ? (
                                                    <>
                                                        <span style={{ color: 'var(--text-primary)' }}>{MESES_ABR[p.fecha_inicio.slice(5, 7)]}</span>
                                                        {' '}{p.fecha_inicio.slice(0, 4)}
                                                    </>
                                                ) : '—'}
                                            </td>
                                            <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{p.forma_pago}</td>
                                            <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                                                ${(p.prima_neta || 0).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                            </td>
                                            <td><StatusPill status={p.status_recibo} /></td>
                                            <td><TipoPill tipo={p.tipo_poliza} formalFlag={p.flag_nueva_formal} /></td>
                                            <td>
                                                {p.tipo_prima ? (
                                                    <span style={{ fontSize: 11, fontWeight: 600, color: p.tipo_prima === 'BASICA' ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                                                        {p.tipo_prima === 'BASICA' ? '✅ Básica' : '❌ Excedente'}
                                                    </span>
                                                ) : <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>—</span>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Paginación */}
                        {pages > 1 && (
                            <div className="pagination">
                                <button className="btn btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Anterior</button>
                                <span className="pagination-info">Página {page} de {pages} • {total.toLocaleString()} registros</span>
                                <button className="btn btn-ghost" onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages}>Siguiente →</button>
                            </div>
                        )}
                    </div>
                </div>

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
                                background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(16,185,129,0.05))',
                            }}>
                                <div>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                                        📄 Documento de Póliza
                                        <code style={{ fontSize: 12, background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '2px 8px', borderRadius: 4 }}>
                                            {docViewer.poliza}
                                        </code>
                                    </div>
                                    {docViewer.asegurado && (
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                                            Asegurado: {docViewer.asegurado}
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
                                    title={`Póliza ${docViewer.poliza}`}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
