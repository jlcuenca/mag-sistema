'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';

function fmt(n) {
    return `$${(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

const EMPTY_FORM = { nombre: '', rfc: '', telefono: '', email: '', domicilio: '', notas: '', referido_por_id: null, agente_id: null };

export default function Contratantes() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ ...EMPTY_FORM });
    const [editId, setEditId] = useState(null);
    const [saving, setSaving] = useState(false);

    const fetchData = () => {
        setLoading(true);
        const p = search ? `?q=${encodeURIComponent(search)}` : '';
        apiFetch(`/contratantes${p}`)
            .then(d => { setData(d || []); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [search]);

    const handleSave = async () => {
        setSaving(true);
        const body = { ...form };
        if (!body.referido_por_id) delete body.referido_por_id;
        if (!body.agente_id) delete body.agente_id;
        try {
            if (editId) {
                await apiFetch(`/contratantes/${editId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            } else {
                await apiFetch('/contratantes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            }
            setShowModal(false);
            setForm({ ...EMPTY_FORM });
            setEditId(null);
            fetchData();
        } catch (e) { alert('Error al guardar'); }
        setSaving(false);
    };

    const openEdit = (c) => {
        setForm({ nombre: c.nombre, rfc: c.rfc || '', telefono: c.telefono || '', email: c.email || '', domicilio: c.domicilio || '', notas: c.notas || '', referido_por_id: c.referido_por_id, agente_id: c.agente_id });
        setEditId(c.id);
        setShowModal(true);
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Contratantes</div>
                        <div className="header-subtitle">Gestión de clientes, contacto y referidos</div>
                    </div>
                    <div className="header-right">
                        <input type="text" placeholder="🔍 Buscar nombre o RFC..." value={search} onChange={e => setSearch(e.target.value)}
                            style={{ padding: '8px 14px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, color: 'var(--text-primary)', width: 260 }} />
                        <button className="btn btn-primary" onClick={() => { setForm({ ...EMPTY_FORM }); setEditId(null); setShowModal(true); }}>
                            + Nuevo Contratante
                        </button>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {/* KPI Summary */}
                    <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-blue)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-blue)', fontSize: 26 }}>{data.length}</div>
                            <div className="kpi-label">Total Contratantes</div>
                        </div>
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-emerald)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-emerald)', fontSize: 26 }}>
                                {data.filter(c => c.num_polizas > 0).length}
                            </div>
                            <div className="kpi-label">Con Pólizas</div>
                        </div>
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-amber)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-amber)', fontSize: 26 }}>
                                {data.filter(c => c.referido_por_id).length}
                            </div>
                            <div className="kpi-label">Referidos</div>
                        </div>
                        <div className="kpi-card" style={{ borderTop: '3px solid var(--accent-cyan)' }}>
                            <div className="kpi-value" style={{ color: 'var(--accent-cyan)', fontSize: 20 }}>
                                {fmt(data.reduce((s, c) => s + (c.prima_total || 0), 0))}
                            </div>
                            <div className="kpi-label">Prima Total</div>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="card">
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Nombre</th>
                                        <th>RFC</th>
                                        <th>Teléfono</th>
                                        <th>Email</th>
                                        <th style={{ textAlign: 'center' }}>Pólizas</th>
                                        <th style={{ textAlign: 'right' }}>Prima Total</th>
                                        <th>Referido por</th>
                                        <th style={{ textAlign: 'center' }}>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        Array(5).fill(0).map((_, i) => (
                                            <tr key={i}>
                                                {Array(8).fill(0).map((_, j) => (
                                                    <td key={j}><div className="loading-skeleton" style={{ height: 16, width: '70%' }} /></td>
                                                ))}
                                            </tr>
                                        ))
                                    ) : data.length === 0 ? (
                                        <tr><td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                                            <div style={{ fontSize: 40, marginBottom: 10 }}>🧑‍💼</div>
                                            No hay contratantes registrados.  Haz clic en "+ Nuevo Contratante" para comenzar.
                                        </td></tr>
                                    ) : data.map(c => (
                                        <tr key={c.id}>
                                            <td style={{ fontWeight: 600 }}>{c.nombre}</td>
                                            <td><code style={{ fontSize: 11, background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: 4 }}>{c.rfc || '—'}</code></td>
                                            <td>{c.telefono || '—'}</td>
                                            <td style={{ fontSize: 12 }}>{c.email || '—'}</td>
                                            <td style={{ textAlign: 'center' }}>
                                                <span className={`badge ${c.num_polizas > 0 ? 'badge-success' : 'badge-info'}`}>{c.num_polizas}</span>
                                            </td>
                                            <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(c.prima_total)}</td>
                                            <td>
                                                {c.referido_por_nombre ? (
                                                    <span style={{ fontSize: 12, color: 'var(--accent-amber)' }}>🔗 {c.referido_por_nombre}</span>
                                                ) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                                            </td>
                                            <td style={{ textAlign: 'center' }}>
                                                <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => openEdit(c)}>✏️ Editar</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Modal */}
                {showModal && (
                    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
                        onClick={() => setShowModal(false)}>
                        <div className="card" style={{ width: 520, maxHeight: '85vh', overflow: 'auto' }} onClick={e => e.stopPropagation()}>
                            <h3 style={{ marginBottom: 20 }}>{editId ? '✏️ Editar' : '➕ Nuevo'} Contratante</h3>
                            <div style={{ display: 'grid', gap: 14 }}>
                                {[
                                    { key: 'nombre', label: 'Nombre completo *', placeholder: 'APELLIDO PATERNO, NOMBRE' },
                                    { key: 'rfc', label: 'RFC', placeholder: 'XAXX010101000' },
                                    { key: 'telefono', label: 'Teléfono', placeholder: '55 1234 5678' },
                                    { key: 'email', label: 'Email', placeholder: 'correo@ejemplo.com' },
                                    { key: 'domicilio', label: 'Domicilio', placeholder: 'Dirección completa' },
                                    { key: 'notas', label: 'Notas', placeholder: 'Observaciones...' },
                                ].map(f => (
                                    <div key={f.key}>
                                        <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>{f.label}</label>
                                        <input value={form[f.key] || ''} onChange={e => setForm({ ...form, [f.key]: e.target.value })} placeholder={f.placeholder}
                                            style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
                                    </div>
                                ))}
                            </div>
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
                                <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancelar</button>
                                <button className="btn btn-primary" disabled={!form.nombre || saving} onClick={handleSave}>
                                    {saving ? 'Guardando...' : editId ? 'Guardar cambios' : 'Crear Contratante'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
