'use client';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { apiFetch } from '@/lib/api';
import {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const YEARS = [2022, 2023, 2024, 2025, 2026];
const YEAR_COLORS = ['#f59e0b', '#10b981', '#6366f1', '#3b82f6', '#f43f5e'];
const MESES = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
const MESES_LABEL = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const RAMO_TABS = ['vida', 'gmm', 'autos'];

function fmt(n) {
    if (!n) return '$0';
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}

export default function Produccion() {
    const [allData, setAllData] = useState({});
    const [loading, setLoading] = useState(true);
    const [vista, setVista] = useState('polizas'); // 'polizas' | 'prima'
    const [ramoTab, setRamoTab] = useState('vida');

    useEffect(() => {
        const fetches = YEARS.map(y =>
            apiFetch(`/dashboard?anio=${y}`)
                .then(d => ({ anio: y, ...d }))
        );
        Promise.all(fetches).then(results => {
            const byYear = {};
            for (const r of results) byYear[r.anio] = r;
            setAllData(byYear);
            setLoading(false);
        });
    }, []);

    // Datos comparativos por año (totales)
    const comparativoAnual = YEARS.map(y => ({
        anio: String(y),
        polizas_vida: allData[y]?.kpis?.polizas_nuevas_vida || 0,
        polizas_gmm: allData[y]?.kpis?.polizas_nuevas_gmm || 0,
        polizas_autos: allData[y]?.kpis?.polizas_nuevas_autos || 0,
        prima_vida: Math.round(allData[y]?.kpis?.prima_nueva_vida || 0),
        prima_gmm: Math.round(allData[y]?.kpis?.prima_nueva_gmm || 0),
        prima_autos: Math.round(allData[y]?.kpis?.prima_nueva_autos || 0),
    }));

    // Datos mensuales multi-año para gráfica de líneas
    const mensualMultianio = MESES.map((m, i) => {
        const row = { mes: MESES_LABEL[i] };
        for (const y of YEARS) {
            const mData = (allData[y]?.produccion_mensual || []).find(d => d.periodo?.endsWith(m));
            const suffix = ramoTab;
            row[`val_${y}`] = vista === 'polizas'
                ? (mData?.[`polizas_${suffix}`] || 0)
                : Math.round(mData?.[`prima_${suffix}`] || 0);
        }
        return row;
    });

    const ramoLabel = { vida: '🛡️ Vida', gmm: '🏥 GMM', autos: '🚗 Autos' };
    const ramoColor = { vida: '#6366f1', gmm: '#10b981', autos: '#3b82f6' };

    return (
        <div className="layout">
            <Sidebar />
            <main className="main">
                <header className="header">
                    <div>
                        <div className="header-title">Producción Histórica</div>
                        <div className="header-subtitle">Evolución anual 2022–2026 · Vida · GMM · Autos</div>
                    </div>
                    <div className="header-right">
                        <div style={{ display: 'flex', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                            {['polizas', 'prima'].map(v => (
                                <button
                                    key={v}
                                    onClick={() => setVista(v)}
                                    style={{
                                        padding: '7px 14px', border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                                        background: vista === v ? 'var(--grad-blue)' : 'transparent',
                                        color: vista === v ? 'white' : 'var(--text-muted)',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {v === 'polizas' ? '📋 Pólizas' : '💰 Prima'}
                                </button>
                            ))}
                        </div>
                    </div>
                </header>

                <div className="page-content fade-in">
                    {loading ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}>
                            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                                <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
                                Cargando datos históricos...
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Ramo selector */}
                            <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--bg-card)', padding: 4, borderRadius: 12, width: 'fit-content', border: '1px solid var(--border)' }}>
                                {RAMO_TABS.map(r => (
                                    <button key={r} onClick={() => setRamoTab(r)}
                                        style={{
                                            padding: '8px 20px', border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, borderRadius: 8,
                                            background: ramoTab === r ? ramoColor[r] : 'transparent',
                                            color: ramoTab === r ? 'white' : 'var(--text-muted)', transition: 'all 0.2s'
                                        }}>
                                        {ramoLabel[r]}
                                    </button>
                                ))}
                            </div>

                            {/* KPI strip — evolución del ramo seleccionado */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 28 }}>
                                {comparativoAnual.map((y, i) => {
                                    const val = vista === 'polizas' ? y[`polizas_${ramoTab}`] : y[`prima_${ramoTab}`];
                                    const prevVal = i > 0 ? (vista === 'polizas' ? comparativoAnual[i-1][`polizas_${ramoTab}`] : comparativoAnual[i-1][`prima_${ramoTab}`]) : 0;
                                    const growth = prevVal > 0 ? (((val - prevVal) / prevVal) * 100).toFixed(0) : null;
                                    return (
                                        <div key={y.anio} className="kpi-card" style={{ padding: '16px' }}>
                                            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: YEAR_COLORS[i] }} />
                                            <div style={{ fontSize: 20, fontWeight: 800, color: YEAR_COLORS[i] }}>{y.anio}</div>
                                            <div style={{ fontSize: 24, fontWeight: 800, color: ramoColor[ramoTab], marginTop: 8 }}>
                                                {vista === 'polizas' ? val : fmt(val)}
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                                                {vista === 'polizas' ? 'pólizas nuevas' : 'prima nueva'}
                                            </div>
                                            {growth !== null && (
                                                <div style={{ fontSize: 11, fontWeight: 700, marginTop: 4, color: Number(growth) >= 0 ? '#10b981' : '#ef4444' }}>
                                                    {Number(growth) >= 0 ? '▲' : '▼'} {growth}% vs {Number(y.anio) - 1}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Gráfica: Evolución anual del ramo seleccionado */}
                            <div className="card" style={{ marginBottom: 24 }}>
                                <div style={{ marginBottom: 20 }}>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                                        {ramoLabel[ramoTab]} — Evolución Anual {vista === 'polizas' ? 'Pólizas Nuevas' : 'Prima Nueva'}
                                    </div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Comportamiento 2022 al 2026</div>
                                </div>
                                <div style={{ height: 300 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={comparativoAnual} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                            <XAxis dataKey="anio" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                            <YAxis tickFormatter={v => vista === 'polizas' ? v : fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <Tooltip
                                                formatter={v => vista === 'polizas' ? [`${v} pólizas`] : [fmt(v)]}
                                                contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }}
                                                labelStyle={{ color: '#f1f5f9' }}
                                            />
                                            <Bar
                                                dataKey={vista === 'polizas' ? `polizas_${ramoTab}` : `prima_${ramoTab}`}
                                                name={ramoLabel[ramoTab]}
                                                fill={ramoColor[ramoTab]}
                                                radius={[6, 6, 0, 0]}
                                            />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <div className="card">
                                <div style={{ marginBottom: 20 }}>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                                        Curva Mensual por Año — {ramoLabel[ramoTab]} {vista === 'polizas' ? 'Pólizas' : 'Prima'}
                                    </div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Comparativo mes a mes entre años</div>
                                </div>
                                <div style={{ height: 300 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={mensualMultianio} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                            <XAxis dataKey="mes" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <YAxis tickFormatter={v => vista === 'polizas' ? v : fmt(v)} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <Tooltip
                                                formatter={v => vista === 'polizas' ? [`${v} pólizas`] : [fmt(v)]}
                                                contentStyle={{ background: '#1a2235', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }}
                                                labelStyle={{ color: '#f1f5f9' }}
                                            />
                                            <Legend wrapperStyle={{ fontSize: 12 }} />
                                            {YEARS.map((y, i) => (
                                                <Line
                                                    key={y}
                                                    type="monotone"
                                                    dataKey={`val_${y}`}
                                                    name={String(y)}
                                                    stroke={YEAR_COLORS[i]}
                                                    strokeWidth={2}
                                                    dot={{ fill: YEAR_COLORS[i], r: 3 }}
                                                    activeDot={{ r: 5 }}
                                                />
                                            ))}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
