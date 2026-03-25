'use client';
import { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/Sidebar';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    PieChart, Pie, Cell, Legend
} from 'recharts';
import { apiFetch } from '@/lib/api';

const COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

const fmtMoney = (v) => {
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
    return `$${(v || 0).toFixed(0)}`;
};

const MESES_CORTO = {
    '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun',
    '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic',
};

export default function TopAgentes() {
    const [tab, setTab] = useState('ranking');  // ranking | pivot
    const [data, setData] = useState(null);
    const [pivotData, setPivotData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [anio, setAnio] = useState(2025);

    // Filtros
    const [ramo, setRamo] = useState('gmm');
    const [gama, setGama] = useState('');
    const [segmento, setSegmento] = useState('');
    const [formaPago, setFormaPago] = useState('');
    const [trimestre, setTrimestre] = useState('');
    const [tipo, setTipo] = useState('');
    const [lider, setLider] = useState('');
    const [moneda, setMoneda] = useState('');
    const [nuevaFormal, setNuevaFormal] = useState(false);
    const [orden, setOrden] = useState('prima');
    const [topN, setTopN] = useState(20);

    // Pivot filters
    const [pivotRamo, setPivotRamo] = useState('');
    const [pivotMetrica, setPivotMetrica] = useState('prima');
    const [pivotTipo, setPivotTipo] = useState('');

    const fetchRanking = useCallback(() => {
        setLoading(true);
        const params = new URLSearchParams({ anio: String(anio), orden, top_n: String(topN) });
        if (ramo) params.append('ramo', ramo);
        if (gama) params.append('gama', gama);
        if (segmento) params.append('segmento', segmento);
        if (formaPago) params.append('forma_pago', formaPago);
        if (trimestre) params.append('trimestre', trimestre);
        if (tipo) params.append('tipo', tipo);
        if (lider) params.append('lider', lider);
        if (moneda) params.append('moneda', moneda);
        if (nuevaFormal) params.append('nueva_formal', 'true');

        apiFetch(`/dashboard/top-agentes-ramo?${params}`)
            .then(d => {
                setData(d);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error al cargar top agentes ramo:", err);
                setLoading(false);
            });
    }, [anio, ramo, gama, segmento, formaPago, trimestre, tipo, lider, moneda, nuevaFormal, orden, topN]);

    const fetchPivot = useCallback(async () => {
        setLoading(true);
        const params = new URLSearchParams({
            anio: String(anio),
            metrica: pivotMetrica,
            top_n: '30'
        });
        if (pivotRamo) params.append('ramo', pivotRamo);
        if (pivotTipo) params.append('tipo', pivotTipo);

        apiFetch(`/dashboard/pivot-agentes?${params}`)
            .then(d => {
                setPivotData(d); // Changed from setPivot to setPivotData
                setLoading(false); // Changed from setLoadingPivot to setLoading
            })
            .catch(err => {
                console.error("Error al cargar pivot:", err);
                setLoading(false); // Changed from setLoadingPivot to setLoading
            });
    }, [anio, pivotRamo, pivotMetrica, pivotTipo]);

    useEffect(() => {
        if (tab === 'ranking') fetchRanking();
        else fetchPivot();
    }, [tab, fetchRanking, fetchPivot]);

    // ── Heatmap helper ──
    const getHeatColor = (val, max) => {
        if (!val || !max) return 'transparent';
        const pct = val / max;
        if (pct > 0.7) return 'rgba(99, 102, 241, 0.35)';
        if (pct > 0.4) return 'rgba(99, 102, 241, 0.2)';
        if (pct > 0.1) return 'rgba(99, 102, 241, 0.1)';
        return 'rgba(99, 102, 241, 0.04)';
    };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <div className="page-content fade-in">
            <div className="page-header">
                <div>
                    <h1 className="page-title">🏆 Top Agentes</h1>
                    <p className="page-subtitle">Rankings con filtros granulares y tabla dinámica</p>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <select value={anio} onChange={e => setAnio(Number(e.target.value))} className="filter-select">
                        <option value={2025}>2025</option>
                        <option value={2024}>2024</option>
                        <option value={2023}>2023</option>
                    </select>
                </div>
            </div>

            {/* ── TABS ── */}
            <div className="tabs-container" style={{ marginBottom: 20 }}>
                <div className="tab-buttons" style={{ display: 'flex', gap: 4, background: 'rgba(30,32,40,0.7)', borderRadius: 12, padding: 4, width: 'fit-content' }}>
                    {[
                        { key: 'ranking', icon: '🏅', label: 'Ranking por Ramo' },
                        { key: 'pivot', icon: '📊', label: 'Tabla Dinámica' },
                    ].map(t => (
                        <button key={t.key}
                            onClick={() => setTab(t.key)}
                            style={{
                                padding: '10px 20px', borderRadius: 10, border: 'none', cursor: 'pointer',
                                background: tab === t.key ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                                color: tab === t.key ? '#fff' : '#94a3b8',
                                fontWeight: tab === t.key ? 700 : 500,
                                fontSize: 14, transition: 'all 0.2s',
                            }}>
                            {t.icon} {t.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* ══════════════ TAB 1: RANKING POR RAMO ══════════════ */}
            {tab === 'ranking' && (
                <div>
                    {/* Filtros granulares */}
                    <div className="card" style={{ marginBottom: 20, padding: 16 }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-end' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Ramo</label>
                                <select value={ramo} onChange={e => setRamo(e.target.value)} className="filter-select">
                                    <option value="">Todos</option>
                                    <option value="gmm">GMM</option>
                                    <option value="vida">Vida</option>
                                    <option value="autos">Autos</option>
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Gama</label>
                                <select value={gama} onChange={e => setGama(e.target.value)} className="filter-select">
                                    <option value="">Todas</option>
                                    {(data?.filtros_disponibles?.gamas || []).map(g => (
                                        <option key={g} value={g}>{g}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Segmento</label>
                                <select value={segmento} onChange={e => setSegmento(e.target.value)} className="filter-select">
                                    <option value="">Todos</option>
                                    {(data?.filtros_disponibles?.segmentos || []).map(s => (
                                        <option key={s} value={s}>{s}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Forma de Pago</label>
                                <select value={formaPago} onChange={e => setFormaPago(e.target.value)} className="filter-select">
                                    <option value="">Todas</option>
                                    {(data?.filtros_disponibles?.formas_pago || []).map(fp => (
                                        <option key={fp} value={fp}>{fp}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Trimestre</label>
                                <select value={trimestre} onChange={e => setTrimestre(e.target.value)} className="filter-select">
                                    <option value="">Todos</option>
                                    {(data?.filtros_disponibles?.trimestres || []).map(t => (
                                        <option key={t} value={t}>{t}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Tipo</label>
                                <select value={tipo} onChange={e => setTipo(e.target.value)} className="filter-select">
                                    <option value="">Todas</option>
                                    <option value="NUEVA">Nueva</option>
                                    <option value="SUBSECUENTE">Subsecuente</option>
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Líder</label>
                                <select value={lider} onChange={e => setLider(e.target.value)} className="filter-select">
                                    <option value="">Todos</option>
                                    {(data?.filtros_disponibles?.lideres || []).map(l => (
                                        <option key={l} value={l}>{l}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Moneda</label>
                                <select value={moneda} onChange={e => setMoneda(e.target.value)} className="filter-select">
                                    <option value="">Todas</option>
                                    {(data?.filtros_disponibles?.monedas || []).map(m => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Nueva Formal</label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', padding: '6px 10px', background: nuevaFormal ? 'rgba(99,102,241,0.15)' : 'rgba(30,32,40,0.7)', borderRadius: 8, border: nuevaFormal ? '1px solid rgba(99,102,241,0.4)' : '1px solid rgba(255,255,255,0.06)' }}>
                                    <input type="checkbox" checked={nuevaFormal} onChange={e => setNuevaFormal(e.target.checked)} style={{ accentColor: '#6366f1' }} />
                                    <span style={{ fontSize: 12, color: nuevaFormal ? '#818cf8' : '#94a3b8' }}>Solo formal</span>
                                </label>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Ordenar por</label>
                                <select value={orden} onChange={e => setOrden(e.target.value)} className="filter-select">
                                    <option value="prima">Prima Total</option>
                                    <option value="asegurados">Asegurados</option>
                                    <option value="polizas">Pólizas</option>
                                    <option value="equivalencias">Equivalencias</option>
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Top N</label>
                                <select value={topN} onChange={e => setTopN(Number(e.target.value))} className="filter-select">
                                    <option value={5}>Top 5</option>
                                    <option value={10}>Top 10</option>
                                    <option value={20}>Top 20</option>
                                    <option value={50}>Top 50</option>
                                    <option value={0}>Todos</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {loading ? (
                        <div className="card" style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                            ⏳ Cargando ranking...
                        </div>
                    ) : data && (
                        <>
                            {/* KPIs */}
                            <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 20 }}>
                                {[
                                    { label: 'Agentes', value: data.total_agentes, icon: '👥', color: '#6366f1' },
                                    { label: 'Pólizas', value: data.total_polizas, icon: '📋', color: '#10b981' },
                                    { label: 'Prima Total', value: fmtMoney(data.total_prima), icon: '💰', color: '#f59e0b' },
                                    { label: 'Asegurados', value: data.total_asegurados?.toLocaleString(), icon: '🛡️', color: '#ef4444' },
                                    { label: 'Equivalencias', value: data.total_equivalencias?.toFixed(1), icon: '⭐', color: '#8b5cf6' },
                                ].map((kpi, i) => (
                                    <div key={i} className="card" style={{ padding: 16, borderLeft: `3px solid ${kpi.color}` }}>
                                        <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase' }}>
                                            {kpi.icon} {kpi.label}
                                        </div>
                                        <div style={{ fontSize: 22, fontWeight: 800, color: kpi.color }}>
                                            {kpi.value}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Chart + Gama Distribution */}
                            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 20 }}>
                                <div className="card" style={{ padding: 16 }}>
                                    <h3 className="section-title" style={{ marginBottom: 12 }}>📊 Top Agentes — {ramo?.toUpperCase() || 'Todos'}</h3>
                                    <ResponsiveContainer width="100%" height={Math.min(data.agentes?.length * 32 + 40, 500)}>
                                        <BarChart data={(data.agentes || []).slice(0, 15)} layout="vertical" margin={{ left: 120 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                            <XAxis type="number" tickFormatter={fmtMoney} stroke="#64748b" fontSize={11} />
                                            <YAxis type="category" dataKey="nombre_completo" width={120} stroke="#94a3b8" fontSize={11}
                                                tickFormatter={v => v?.length > 18 ? v.substring(0, 18) + '...' : v} />
                                            <Tooltip
                                                contentStyle={{ background: '#1e2028', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, fontSize: 12 }}
                                                formatter={(v) => [fmtMoney(v), '']}
                                            />
                                            <Bar dataKey="prima_nueva" name="Prima Nueva" stackId="a" fill="#6366f1" radius={[0, 0, 0, 0]} />
                                            <Bar dataKey="prima_subsecuente" name="Prima Subs." stackId="a" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="card" style={{ padding: 16 }}>
                                    <h3 className="section-title" style={{ marginBottom: 12 }}>🎯 Distribución por Gama</h3>
                                    {data.distribucion_gama?.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={250}>
                                            <PieChart>
                                                <Pie data={data.distribucion_gama} dataKey="total" nameKey="gama" cx="50%" cy="50%"
                                                    outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                                    {data.distribucion_gama.map((_, i) => (
                                                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                                    ))}
                                                </Pie>
                                                <Tooltip contentStyle={{ background: '#1e2028', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, fontSize: 12 }} />
                                                <Legend />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div style={{ textAlign: 'center', color: '#64748b', padding: 40 }}>Sin datos de gama</div>
                                    )}
                                </div>
                            </div>

                            {/* Table */}
                            <div className="card" style={{ padding: 0, overflow: 'auto' }}>
                                <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                                    <thead>
                                        <tr style={{ background: 'rgba(99,102,241,0.1)' }}>
                                            <th style={thStyle}>#</th>
                                            <th style={thStyle}>Agente</th>
                                            <th style={thStyle}>Clave</th>
                                            <th style={thStyle}>Segmento</th>
                                            <th style={thStyle}>Líder</th>
                                            <th style={thStyle}>Gestión</th>
                                            <th style={{...thStyle, textAlign: 'center'}}>Moneda</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Pól. Nuevas</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Pól. Subs.</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Nva. Formal</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Asegs.</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Equiv.</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Prima Nueva</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Prima Subs.</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Prima Anual $</th>
                                            <th style={{...thStyle, textAlign: 'right'}}>Prima s/FP</th>
                                            <th style={{...thStyle, textAlign: 'right', color: '#6366f1', fontWeight: 800}}>Prima Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(data.agentes || []).map((a, i) => (
                                            <tr key={a.codigo_agente} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', background: i < 3 ? 'rgba(99,102,241,0.04)' : 'transparent' }}>
                                                <td style={tdStyle}>
                                                    {i < 3 ? ['🥇', '🥈', '🥉'][i] : <span style={{ color: '#64748b' }}>{i + 1}</span>}
                                                </td>
                                                <td style={{...tdStyle, fontWeight: 600, color: '#e2e8f0', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{a.nombre_completo}</td>
                                                <td style={{...tdStyle, color: '#94a3b8', fontFamily: 'monospace'}}>{a.codigo_agente}</td>
                                                <td style={tdStyle}>
                                                    <span style={{
                                                        padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 700,
                                                        background: a.segmento === 'ALFA' ? 'rgba(99,102,241,0.2)' : a.segmento === 'BETA' ? 'rgba(245,158,11,0.2)' : 'rgba(100,116,139,0.2)',
                                                        color: a.segmento === 'ALFA' ? '#818cf8' : a.segmento === 'BETA' ? '#fbbf24' : '#94a3b8',
                                                    }}>{a.segmento || '—'}</span>
                                                </td>
                                                <td style={{...tdStyle, color: '#94a3b8', fontFamily: 'monospace', fontSize: 10}}>{a.lider_codigo || '—'}</td>
                                                <td style={{...tdStyle, color: '#94a3b8', fontSize: 11, maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{a.gestion || '—'}</td>
                                                <td style={{...tdStyle, textAlign: 'center'}}>
                                                    {a.monedas && Object.keys(a.monedas).length > 0 ? (
                                                        Object.entries(a.monedas).map(([m, cnt]) => (
                                                            <span key={m} style={{
                                                                padding: '1px 5px', borderRadius: 4, fontSize: 9, fontWeight: 700, marginRight: 2,
                                                                background: m === 'UDIS' ? 'rgba(16,185,129,0.2)' : 'rgba(100,116,139,0.15)',
                                                                color: m === 'UDIS' ? '#34d399' : '#94a3b8',
                                                            }}>{m}:{cnt}</span>
                                                        ))
                                                    ) : '—'}
                                                </td>
                                                <td style={{...tdStyle, textAlign: 'right', fontWeight: 600}}>{a.polizas_nuevas}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: '#94a3b8'}}>{a.polizas_subsecuentes}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: a.polizas_nueva_formal > 0 ? '#10b981' : '#3f3f46'}}>{a.polizas_nueva_formal || 0}</td>
                                                <td style={{...tdStyle, textAlign: 'right', fontWeight: 600}}>{a.asegurados}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: '#8b5cf6', fontWeight: 600}}>{a.equivalencias?.toFixed(1)}</td>
                                                <td style={{...tdStyle, textAlign: 'right'}}>{fmtMoney(a.prima_nueva)}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: '#94a3b8'}}>{fmtMoney(a.prima_subsecuente)}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: '#10b981'}}>{fmtMoney(a.prima_anual_pesos)}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: '#94a3b8'}}>{fmtMoney(a.prima_sin_fp)}</td>
                                                <td style={{...tdStyle, textAlign: 'right', color: '#6366f1', fontWeight: 800, fontSize: 13}}>{fmtMoney(a.prima_total)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* ══════════════ TAB 2: TABLA DINÁMICA (PIVOT) ══════════════ */}
            {tab === 'pivot' && (
                <div>
                    {/* Pivot Filters */}
                    <div className="card" style={{ marginBottom: 20, padding: 16 }}>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Ramo</label>
                                <select value={pivotRamo} onChange={e => setPivotRamo(e.target.value)} className="filter-select">
                                    <option value="">Todos</option>
                                    <option value="gmm">GMM</option>
                                    <option value="vida">Vida</option>
                                    <option value="autos">Autos</option>
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Métrica</label>
                                <select value={pivotMetrica} onChange={e => setPivotMetrica(e.target.value)} className="filter-select">
                                    <option value="prima">Prima ($)</option>
                                    <option value="polizas">Pólizas (#)</option>
                                    <option value="asegurados">Asegurados (#)</option>
                                    <option value="equivalencias">Equivalencias</option>
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Tipo</label>
                                <select value={pivotTipo} onChange={e => setPivotTipo(e.target.value)} className="filter-select">
                                    <option value="">Todas</option>
                                    <option value="NUEVA">Nuevas</option>
                                    <option value="SUBSECUENTE">Subsecuentes</option>
                                </select>
                            </div>
                            <div style={{ fontSize: 12, color: '#94a3b8', padding: '8px 0' }}>
                                📊 {pivotData?.total_agentes || 0} agentes × {pivotData?.periodos_disponibles?.length || 0} periodos
                            </div>
                        </div>
                    </div>

                    {loading ? (
                        <div className="card" style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                            ⏳ Construyendo tabla dinámica...
                        </div>
                    ) : pivotData && (
                        <div className="card" style={{ padding: 0, overflow: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                                <thead>
                                    <tr style={{ background: 'rgba(99,102,241,0.1)' }}>
                                        <th style={{ ...thStyle, position: 'sticky', left: 0, background: '#1a1c24', zIndex: 2, minWidth: 180 }}>Agente</th>
                                        <th style={{ ...thStyle, position: 'sticky', left: 180, background: '#1a1c24', zIndex: 2, minWidth: 60 }}>Seg.</th>
                                        {(pivotData.periodos_disponibles || []).map(p => (
                                            <th key={p} style={{ ...thStyle, textAlign: 'center', minWidth: 75, fontSize: 10 }}>
                                                {MESES_CORTO[p?.split('-')[1]] || p} {p?.split('-')[0]?.slice(-2)}
                                            </th>
                                        ))}
                                        <th style={{ ...thStyle, textAlign: 'right', color: '#6366f1', fontWeight: 800, minWidth: 90, position: 'sticky', right: 0, background: '#1a1c24', zIndex: 2 }}>TOTAL</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(() => {
                                        // compute max for heatmap
                                        let maxVal = 0;
                                        (pivotData.filas || []).forEach(row => {
                                            Object.values(row.periodos || {}).forEach(v => {
                                                const val = v?.[pivotMetrica] || 0;
                                                if (val > maxVal) maxVal = val;
                                            });
                                        });

                                        return (pivotData.filas || []).map((row, i) => (
                                            <tr key={row.codigo_agente} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                                <td style={{ ...tdStyle, position: 'sticky', left: 0, background: '#1a1c24', zIndex: 1, fontWeight: 600, color: '#e2e8f0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 180 }}>
                                                    {i < 3 ? ['🥇', '🥈', '🥉'][i] + ' ' : ''}{row.nombre_completo}
                                                </td>
                                                <td style={{ ...tdStyle, position: 'sticky', left: 180, background: '#1a1c24', zIndex: 1 }}>
                                                    <span style={{
                                                        padding: '1px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700,
                                                        background: row.segmento === 'ALFA' ? 'rgba(99,102,241,0.2)' : row.segmento === 'BETA' ? 'rgba(245,158,11,0.2)' : 'rgba(100,116,139,0.2)',
                                                        color: row.segmento === 'ALFA' ? '#818cf8' : row.segmento === 'BETA' ? '#fbbf24' : '#94a3b8',
                                                    }}>{row.segmento || '—'}</span>
                                                </td>
                                                {(pivotData.periodos_disponibles || []).map(p => {
                                                    const cell = row.periodos?.[p];
                                                    const val = cell?.[pivotMetrica] || 0;
                                                    return (
                                                        <td key={p} style={{
                                                            ...tdStyle, textAlign: 'right', fontFamily: 'monospace', fontSize: 10,
                                                            background: getHeatColor(val, maxVal),
                                                            color: val > 0 ? '#e2e8f0' : '#3f3f46',
                                                        }}>
                                                            {val > 0 ? (pivotMetrica === 'prima' ? fmtMoney(val) : val?.toFixed?.(1) || val) : '—'}
                                                        </td>
                                                    );
                                                })}
                                                <td style={{
                                                    ...tdStyle, textAlign: 'right', position: 'sticky', right: 0,
                                                    background: '#1a1c24', zIndex: 1, color: '#6366f1', fontWeight: 800, fontSize: 12
                                                }}>
                                                    {pivotMetrica === 'prima' ? fmtMoney(row.total_prima) :
                                                     pivotMetrica === 'polizas' ? row.total_polizas :
                                                     pivotMetrica === 'asegurados' ? row.total_asegurados :
                                                     row.total_equivalencias?.toFixed(1)}
                                                </td>
                                            </tr>
                                        ));
                                    })()}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
                </div>
            </main>
        </div>
    );
}

const thStyle = {
    padding: '10px 12px',
    textAlign: 'left',
    fontSize: 11,
    fontWeight: 700,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    whiteSpace: 'nowrap',
};

const tdStyle = {
    padding: '8px 12px',
    color: '#cbd5e1',
    borderBottom: '1px solid rgba(255,255,255,0.03)',
};
