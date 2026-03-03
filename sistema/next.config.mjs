/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  turbopack: {},
  serverExternalPackages: ['better-sqlite3'],
};

export default nextConfig;
