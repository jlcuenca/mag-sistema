'use client';
import { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';

const MESES_ABR = { '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic' };

function StatusPill({ status }) {
    if (status === 'PAGADA') return <span className="status-pill status-pagada">Pagada</span>;
    if (status?.includes('CANC')) return <span className="status-pill status-cancelada">Cancelada</span>;
    return <span className="status-pill status-no-aplica">{status}</span>;
}

function TipoPill({ tipo }) {
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
                                                {Array(11).fill(0).map((_, j) => (
                                                    <td key={j}><div className="loading-skeleton" style={{ height: 14, width: '80%' }} /></td>
                                                ))}
                                            </tr>
                                        ))
                                    ) : polizas.length === 0 ? (
                                        <tr>
                                            <td colSpan={11}>
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
                                                <span className={`badge ${p.ramo_codigo === 11 ? 'badge-indigo' : 'badge-emerald'}`} style={{ background: p.ramo_codigo === 11 ? 'rgba(99,102,241,0.15)' : 'rgba(16,185,129,0.15)', color: p.ramo_codigo === 11 ? '#818cf8' : '#34d399', borderRadius: 20, padding: '3px 8px', fontSize: 11, fontWeight: 600 }}>
                                                    {p.ramo_codigo === 11 ? 'Vida' : 'GMM'}
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
                                            <td><TipoPill tipo={p.tipo_poliza} /></td>
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
            </main>
        </div>
    );
}
