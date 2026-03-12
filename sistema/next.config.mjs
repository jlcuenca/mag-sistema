/** @type {import('next').NextConfig} */
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const nextConfig = {
  output: 'standalone',
  turbopack: {
    root: __dirname,
  },
  serverExternalPackages: ['better-sqlite3'],
};

export default nextConfig;
