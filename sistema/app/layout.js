import './globals.css';

export const metadata = {
  title: 'MAG Sistema - Promotoría AXA Seguros',
  description: 'Sistema de gestión de producción para Promotoría MAG - Ramos Vida Individual y GMM Individual AXA',
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
