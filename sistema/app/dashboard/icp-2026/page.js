'use client';
import { useState, useEffect, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch, fmt, API_URL } from '@/lib/api';

/* ── Componentes de Soporte ─────────────────────────────────── */

function StatusBadge({ segment }) {
    const colors = { 'ALFA+': 'var(--grad-indigo)', 'ALFA': 'var(--grad-blue)', 'OMEGA+': 'var(--grad-emerald)', 'OMEGA': 'var(--bg-secondary)' };
    return (
        <div style={{ background: colors[segment] || 'var(--bg-secondary)', padding: '20px 40px', borderRadius: 20, textAlign: 'center', boxShadow: '0 10px 30px rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Segmento Actual Alcanzado</div>
            <div style={{ fontSize: 42, fontWeight: 900, color: 'white', letterSpacing: 3 }}>{segment}</div>
        </div>
    );
}

function QualityCard({ label, value, threshold, inverse = false }) {
    const isSuccess = inverse ? value <= threshold : value >= threshold;
    return (
        <div className="card" style={{ padding: 20, textAlign: 'center', border: isSuccess ? '1px solid var(--accent-emerald)' : '1px solid var(--border)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>{label}</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: isSuccess ? 'var(--accent-emerald)' : 'var(--text-primary)' }}>
                {(value * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Meta: {inverse ? '<=' : '>='} {(threshold * 100).toFixed(0)}%</div>
        </div>
    );
}

function IndicatorRow({ indicator, onClick }) {
    const drilldowns = [1, 2, 3, 4, 5, 6];
    const isDetailAvailable = drilldowns.includes(indicator.id);
    return (
        <div onClick={() => isDetailAvailable && onClick(indicator.id)} style={{ display: 'grid', gridTemplateColumns: '50px 1fr 100px 100px 80px', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border)', background: indicator.cumple ? 'rgba(16,185,129,0.03)' : 'transparent', cursor: isDetailAvailable ? 'pointer' : 'default', transition: 'background 0.2s' }} className={isDetailAvailable ? 'hover-row' : ''}>
            <div style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 700 }}>{indicator.id}</div>
            <div style={{ fontSize: 15, color: 'var(--text-primary)', fontWeight: 600 }}>{indicator.nombre} {isDetailAvailable && <span style={{ fontSize: 10, color: 'var(--accent-blue)', marginLeft: 8 }}>👁️ Ver detalle</span>}</div>
            <div style={{ fontSize: 16, textAlign: 'center', fontWeight: 700, color: indicator.cumple ? 'var(--accent-emerald)' : 'var(--text-primary)' }}>{indicator.actual}</div>
            <div style={{ fontSize: 14, textAlign: 'center', color: 'var(--text-muted)' }}>{indicator.meta}</div>
            <div style={{ textAlign: 'right' }}>{indicator.cumple ? <span style={{ fontSize: 24 }}>✅</span> : <span style={{ fontSize: 24, opacity: 0.2 }}>❌</span>}</div>
        </div>
    );
}

function DetailModal({ title, isOpen, onClose, children }) {
    if (!isOpen) return null;
    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(10px)', padding: 20 }}>
            <div className="card fade-in" style={{ width: '100%', maxWidth: 1100, maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3 style={{ margin: 0 }}>{title}</h3><button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 24, cursor: 'pointer' }}>&times;</button></div>
                <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>{children}</div>
            </div>
        </div>
    );
}

/* ── Componentes de Tabla ───────────────────────────────────── */
function ReclutaTable({ data }) { return ( <div className="table-container"><table><thead><tr><th>Agente</th><th>Alta</th><th>Año</th><th>Vida Act/Meta</th><th>Prima Act/Meta</th><th>Estatus</th></tr></thead><tbody>{data.map((a, i) => ( <tr key={i}><td><div style={{ fontWeight: 600 }}>{a.nombre}</div><div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.codigo}</div></td><td>{a.fecha_alta.slice(0, 10)}</td><td>Año {a.anio_icp}</td><td>{a.actual_vida} / {a.meta_vida}</td><td>{fmt(a.actual_prima)} / {fmt(a.meta_prima)}</td><td>{a.cumple ? '✅ PRODUCTIVO' : '⏳ EN PROCESO'}</td></tr> ))}</tbody></table></div> ); }
function VidaTable({ data }) { return ( <div className="table-container"><table><thead><tr><th>Póliza</th><th>Agente</th><th>Inicio</th><th>Prima Anual</th><th>Puntos (M)</th></tr></thead><tbody>{data.map((p, i) => ( <tr key={i}><td style={{ fontWeight: 700 }}>{p.poliza}</td><td>{p.agente}</td><td>{p.fecha_inicio.slice(0, 10)}</td><td>{fmt(p.prima_anual)}</td><td><span className={p.puntos > 1 ? 'badge badge-emerald' : 'badge badge-blue'}>{p.puntos} {p.puntos > 1 ? 'X' : ''}</span></td></tr> ))}</tbody></table></div> ); }
function AlfaTable({ data }) { return ( <div className="table-container"><table><thead><tr><th>Agente</th><th>Código</th><th>Puntos Vida</th><th>Prima Vida</th><th>Meta Alfa</th><th>Estatus</th></tr></thead><tbody>{data.map((a, i) => ( <tr key={i}><td style={{ fontWeight: 600 }}>{a.agente}</td><td>{a.codigo}</td><td>{a.vida_puntos} / {a.meta_puntos}</td><td>{fmt(a.vida_prima)} / {fmt(a.meta_prima)}</td><td>18 Puntos + 700k Prima</td><td>{a.cumple ? <span className="badge badge-indigo">ALFA</span> : <span className="badge badge-rose">PENDIENTE</span>}</td></tr> ))}</tbody></table></div> ); }
function GmmTable({ data }) { return ( <div className="table-container"><table><thead><tr><th>Póliza</th><th>Agente</th><th>Inicio</th><th>Asegurados</th></tr></thead><tbody>{data.map((p, i) => ( <tr key={i}><td style={{ fontWeight: 700 }}>{p.poliza}</td><td>{p.agente}</td><td>{p.fecha_inicio.slice(0, 10)}</td><td style={{ textAlign: 'center', fontWeight: 700 }}>{p.num_asegurados}</td></tr> ))}</tbody></table></div> ); }
function CrecimientoTable({ data }) { return ( <div className="table-container"><table><thead><tr><th>Ramo</th><th>Prima 2025</th><th>Prima 2026</th><th>Crecimiento</th></tr></thead><tbody>{data.map((r, i) => ( <tr key={i}><td style={{ fontWeight: 700 }}>{r.ramo}</td><td>{fmt(r.monto_2025)}</td><td>{fmt(r.monto_2026)}</td><td><span className={r.crecimiento >= 0.1 ? 'badge badge-emerald' : 'badge badge-rose'}>{(r.crecimiento * 100).toFixed(1)}%</span></td></tr> ))}</tbody></table></div> ); }
function BonoTable({ data }) { return ( <div className="table-container"><table><thead><tr><th>Agente</th><th>Código</th><th>Producción Bonificable</th><th>Califica</th></tr></thead><tbody>{data.map((a, i) => ( <tr key={i}><td style={{ fontWeight: 600 }}>{a.agente}</td><td>{a.codigo}</td><td style={{ fontWeight: 700 }}>{fmt(a.produccion_total)}</td><td>{a.estatus_bono ? <span className="badge badge-amber">GANADOR BONO</span> : <span className="badge badge-rose">PENDIENTE</span>}</td></tr> ))}</tbody></table></div> ); }

/* ── Página Principal ────────────────────────────────────────── */

export default function ICP2026Page() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [detailData, setDetailData] = useState([]);
    const [activeDrilldown, setActiveDrilldown] = useState(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    
    const fileSiniestrosRef = useRef(null);
    const filePersistenciaRef = useRef(null);

    const loadData = () => {
        setLoading(true);
        apiFetch('/dashboard/icp-2026?anio=2026').then(d => { setData(d); setLoading(false); }).catch(err => { setError(err.message); setLoading(false); });
    };

    useEffect(() => { loadData(); }, []);

    const handleOpenDrilldown = (id) => {
        const endpoints = { 1: '/dashboard/icp-2026/detalle-recluta', 2: '/dashboard/icp-2026/detalle-vida', 3: '/dashboard/icp-2026/detalle-alfa', 4: '/dashboard/icp-2026/detalle-gmm', 5: '/dashboard/icp-2026/detalle-crecimiento', 6: '/dashboard/icp-2026/detalle-bono' };
        if (!endpoints[id]) return;
        setActiveDrilldown(id); setLoadingDetail(true);
        apiFetch(`${endpoints[id]}?anio=2026`).then(d => { setDetailData(d); setLoadingDetail(false); }).catch(err => { console.error(err); setLoadingDetail(false); });
    };

    const handleImportFile = async (event, endpoint) => {
        const file = event.target.files[0];
        if (!file) return;
        setIsImporting(true);
        const formData = new FormData();
        formData.append('file', file);
        try {
            const resp = await fetch(`${API_URL}${endpoint}`, { method: 'POST', body: formData });
            const resData = await resp.json();
            alert(`Éxito: Se procesaron ${resData.procesados} registros.`);
            loadData();
        } catch (err) {
            alert('Error al importar archivo: ' + err.message);
        } finally {
            setIsImporting(false);
            event.target.value = "";
        }
    };

    const handleExportExcel = () => { window.open(`${API_URL}/exportar/icp-2026-excel?anio=2026`, '_blank'); };

    if (loading) return <div className="layout"><Sidebar /><main className="main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="loader" /></main></div>;
    if (error) return <div className="layout"><Sidebar /><main className="main" style={{ padding: 40 }}><div className="card" style={{ border: '1px solid var(--accent-red)' }}><h2 style={{ color: 'var(--accent-red)' }}>Error al cargar indicadores</h2><p>{error}</p></div></main></div>;

    const getModalTitle = () => {
        const titles = { 1: "Agentes — Recluta Productiva", 2: "Pólizas — Vida (Multiplicadores)", 3: "Agentes — Clasificación ALFA", 4: "Asegurados — GMM Individual", 5: "Comparativo — Crecimiento de Cartera", 6: "Listado — Ganadores de Bono" };
        return titles[activeDrilldown] || "Detalle de Indicador";
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div><div className="header-title">Indicadores Básicos de Promotor — ICP 2026</div><div className="header-subtitle">Gestión de incentivos y estatus de segmento</div></div>
                    <div className="header-right"><div className="badge badge-amber" style={{ fontSize: 14, padding: '8px 16px', marginRight: 10 }}>Cartera: {data.cartera_categoria}</div><button className="btn btn-primary" onClick={handleExportExcel}>📥 Exportar Excel</button></div>
                </header>
                <div className="page-content fade-in" style={{ maxWidth: 1000, margin: '0 auto' }}>
                    
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 40, marginTop: 20 }}><StatusBadge segment={data.segmento_alcanzado} /></div>

                    <div style={{ marginBottom: 30 }}>
                        <h4 style={{ marginBottom: 15, paddingLeft: 10, borderLeft: '4px solid var(--accent-blue)' }}>Indicadores Básicos (Mantenimiento de Segmento)</h4>
                        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '50px 1fr 100px 100px 80px', padding: '16px 20px', background: 'var(--bg-secondary)', fontSize: 11, fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}><div>ID</div><div>Indicador</div><div style={{ textAlign: 'center' }}>Actual</div><div style={{ textAlign: 'center' }}>Meta</div><div style={{ textAlign: 'right' }}>Estatus</div></div>
                            {data.indicadores.map(ind => ( <IndicatorRow key={ind.id} indicator={ind} onClick={handleOpenDrilldown} /> ))}
                        </div>
                    </div>

                    <div style={{ marginBottom: 40 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
                            <h4 style={{ margin: 0, paddingLeft: 10, borderLeft: '4px solid var(--accent-emerald)' }}>Calidad (Abono de Bonos)</h4>
                            <div style={{ display: 'flex', gap: 10 }}>
                                <input type="file" ref={fileSiniestrosRef} onChange={(e) => handleImportFile(e, '/dashboard/icp-2026/importar-siniestros')} style={{ display: 'none' }} accept=".csv, .xlsx, .xls" />
                                <input type="file" ref={filePersistenciaRef} onChange={(e) => handleImportFile(e, '/dashboard/icp-2026/importar-persistencia')} style={{ display: 'none' }} accept=".csv, .xlsx, .xls" />
                                <button className="btn btn-secondary btn-sm" onClick={() => fileSiniestrosRef.current.click()} disabled={isImporting}>
                                    {isImporting ? '⌛' : '🏥 Reporte Siniestros'}
                                </button>
                                <button className="btn btn-secondary btn-sm" onClick={() => filePersistenciaRef.current.click()} disabled={isImporting}>
                                    {isImporting ? '⌛' : '📉 Reporte Persistencia'}
                                </button>
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
                            <QualityCard label="Persistencia K+1" value={data.persistencia_actual} threshold={0.89} />
                            <QualityCard label="Siniestralidad Total" value={data.siniestralidad_actual} threshold={0.55} inverse={true} />
                            <div className="card" style={{ padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: data.bono_calidad_aplica ? 'var(--grad-emerald)' : 'var(--bg-secondary)' }}>
                                <div style={{ fontSize: 10, color: data.bono_calidad_aplica ? 'rgba(255,255,255,0.8)' : 'var(--text-muted)', textTransform: 'uppercase' }}>Bono de Calidad</div>
                                <div style={{ fontSize: 24, fontWeight: 900, color: 'white' }}>{data.bono_calidad_aplica ? 'SI APLICA' : 'NO APLICA'}</div>
                                {data.bono_calidad_aplica && <div style={{ fontSize: 10, color: 'white', marginTop: 5 }}>Multiplicador: 100%</div>}
                            </div>
                        </div>
                    </div>

                    <div style={{ marginTop: 30, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
                        <div className="card" style={{ padding: 20, cursor: 'pointer' }} onClick={() => handleOpenDrilldown(5)}><h4 style={{ marginBottom: 10, color: 'var(--accent-emerald)' }}>📈 Crecimiento</h4><p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Comparativa 2025 vs 2026 por ramo.</p></div>
                        <div className="card" style={{ padding: 20, cursor: 'pointer' }} onClick={() => handleOpenDrilldown(6)}><h4 style={{ marginBottom: 10, color: 'var(--accent-amber)' }}>💰 Ganadores Bono</h4><p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Agentes con producción bonificable.</p></div>
                        <div className="card" style={{ padding: 20, cursor: 'pointer' }} onClick={handleExportExcel}><h4 style={{ marginBottom: 10, color: 'var(--accent-blue)' }}>📋 Exportación Full</h4><p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Descarga el reporte completo en Excel.</p></div>
                    </div>
                </div>

                <DetailModal isOpen={!!activeDrilldown} onClose={() => setActiveDrilldown(null)} title={getModalTitle()}>
                    {loadingDetail ? <div style={{ textAlign: 'center', padding: 40 }}><div className="loader" /></div> :
                        <>
                            {activeDrilldown === 1 && <ReclutaTable data={detailData} />}
                            {activeDrilldown === 2 && <VidaTable data={detailData} />}
                            {activeDrilldown === 3 && <AlfaTable data={detailData} />}
                            {activeDrilldown === 4 && <GmmTable data={detailData} />}
                            {activeDrilldown === 5 && <CrecimientoTable data={detailData} />}
                            {activeDrilldown === 6 && <BonoTable data={detailData} />}
                        </>
                    }
                </DetailModal>
                <style jsx>{` .hover-row:hover { background: rgba(255,255,255,0.05) !important; } `}</style>
            </main>
        </div>
    );
}
