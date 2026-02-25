'use client';
import { usePathname } from 'next/navigation';
import Link from 'next/link';

const navSections = [
    {
        title: 'Principal',
        items: [
            { href: '/dashboard', icon: '📊', label: 'Dashboard' },
            { href: '/ejecutivo', icon: '🏛️', label: 'Vista Ejecutiva' },
            { href: '/finanzas', icon: '💰', label: 'Finanzas' },
            { href: '/cobranza', icon: '💳', label: 'Cobranza' },
        ],
    },
    {
        title: 'Operación',
        items: [
            { href: '/polizas', icon: '📋', label: 'Pólizas' },
            { href: '/agentes', icon: '👥', label: 'Agentes' },
            { href: '/contratantes', icon: '🧑‍💼', label: 'Contratantes' },
            { href: '/solicitudes', icon: '📝', label: 'Solicitudes' },
        ],
    },
    {
        title: 'Análisis',
        items: [
            { href: '/conciliacion', icon: '🔄', label: 'Conciliación AXA' },
            { href: '/produccion', icon: '📈', label: 'Producción Histórica' },
            { href: '/cartera', icon: '💼', label: 'Cartera' },
        ],
    },
    {
        title: 'Sistema',
        items: [
            { href: '/configuracion', icon: '⚙️', label: 'Configuración' },
        ],
    },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">M</div>
                <div className="sidebar-logo-text">
                    <h2>MAG Sistema</h2>
                    <span>Promotoría AXA Seguros</span>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navSections.map(section => (
                    <div key={section.title}>
                        <div className="nav-section-title">{section.title}</div>
                        {section.items.map(item => (
                            <Link key={item.href} href={item.href} className={`nav-item ${pathname === item.href ? 'active' : ''}`}>
                                <span className="nav-item-icon">{item.icon}</span>
                                {item.label}
                            </Link>
                        ))}
                    </div>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="sidebar-footer-text">
                    🛡️ MAG — Ramos Vida & GMM<br />
                    <span style={{ color: '#3b82f6' }}>AXA Seguros México</span>
                </div>
            </div>
        </aside>
    );
}
