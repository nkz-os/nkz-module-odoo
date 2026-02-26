/**
 * Vite config for building the Odoo module as an IIFE bundle (same as other NKZ modules).
 * Output: dist/nkz-module.js — upload to MinIO at nekazari-frontend/modules/odoo-erp/nkz-module.js
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @license AGPL-3.0
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MODULE_ID = 'odoo-erp';

const externals = ['react', 'react-dom', 'react-dom/client', 'react-router-dom'];
const globals: Record<string, string> = {
  react: 'React',
  'react-dom': 'ReactDOM',
  'react-dom/client': 'ReactDOM',
  'react-router-dom': 'ReactRouterDOM',
};

export default defineConfig({
  plugins: [
    react({ jsxRuntime: 'classic' }),
    {
      name: 'nkz-module-banner',
      generateBundle(_options, bundle) {
        for (const chunk of Object.values(bundle)) {
          if (chunk.type === 'chunk' && chunk.isEntry) {
            chunk.code = `/* NKZ Module: ${MODULE_ID} | Built: ${new Date().toISOString()} */\n${chunk.code}`;
          }
        }
      },
    },
  ],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/moduleEntry.ts'),
      name: 'NKZModule_odoo_erp',
      formats: ['iife'],
      fileName: () => 'nkz-module.js',
    },
    rollupOptions: {
      external: externals,
      output: {
        globals,
        inlineDynamicImports: true,
      },
    },
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    minify: 'esbuild',
    copyPublicDir: false,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
