'use client';
import { usePathname } from 'next/navigation';
import Link from 'next/link';

const navItems = [
    { href: '/dashboard', icon: '📊', label: 'Dashboard' },
    { href: '/polizas', icon: '📋', label: 'Pólizas' },
    { href: '/agentes', icon: '👥', label: 'Agentes' },
    { href: '/conciliacion', icon: '🔄', label: 'Conciliación AXA' },
    { href: '/produccion', icon: '📈', label: 'Producción Histórica' },
    { href: '/cartera', icon: '💼', label: 'Cartera' },
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
                <div className="nav-section-title">Principal</div>
                {navItems.slice(0, 4).map(item => (
                    <Link key={item.href} href={item.href} className={`nav-item ${pathname === item.href ? 'active' : ''}`}>
                        <span className="nav-item-icon">{item.icon}</span>
                        {item.label}
                    </Link>
                ))}

                <div className="nav-section-title">Análisis</div>
                {navItems.slice(4).map(item => (
                    <Link key={item.href} href={item.href} className={`nav-item ${pathname === item.href ? 'active' : ''}`}>
                        <span className="nav-item-icon">{item.icon}</span>
                        {item.label}
                    </Link>
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
