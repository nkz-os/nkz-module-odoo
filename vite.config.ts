/**
 * Vite Configuration for Nekazari Odoo ERP Module
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'odoo_erp_module',
      filename: 'remoteEntry.js',
      exposes: {
        './App': './src/App.tsx',
        './viewerSlots': './src/slots/index.tsx',
        './OdooEntityLink': './src/components/slots/OdooEntityLink.tsx',
        './OdooQuickActions': './src/components/slots/OdooQuickActions.tsx',
        './OdooStatusWidget': './src/components/slots/OdooStatusWidget.tsx'
      },
      shared: {
        'react': {
          singleton: true,
          requiredVersion: '^18.3.1',
          import: false,
          shareScope: 'default'
        },
        'react-dom': {
          singleton: true,
          requiredVersion: '^18.3.1',
          import: false,
          shareScope: 'default'
        },
        'react-router-dom': {
          singleton: true,
          requiredVersion: '^6.26.0',
          import: false,
          shareScope: 'default'
        }
      }
    })
  ],
  server: {
    port: 5010,
    cors: true,
    proxy: {
      '/api/odoo': {
        target: 'http://localhost:8001',
        changeOrigin: true
      },
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    target: 'esnext',
    minify: false,
    cssCodeSplit: false,
    rollupOptions: {
      external: [
        '@nekazari/design-tokens',
        '@nekazari/viewer-kit',
      ],
      output: {
        format: 'esm',
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        globals: {
          '@nekazari/design-tokens': '__NKZ_DESIGN_TOKENS__',
          '@nekazari/viewer-kit': '__NKZ_VIEWER_KIT__',
        },
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
});
