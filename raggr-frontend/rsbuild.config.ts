import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';

export default defineConfig({
  plugins: [pluginReact()],
  html: {
    title: 'Ask Simba',
    favicon: './src/assets/favicon.svg',
    tags: [
      { tag: 'link', attrs: { rel: 'manifest', href: '/manifest.json' } },
      { tag: 'meta', attrs: { name: 'theme-color', content: '#2A4D38' } },
      { tag: 'link', attrs: { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' } },
      { tag: 'meta', attrs: { name: 'apple-mobile-web-app-capable', content: 'yes' } },
    ],
  },
  output: {
    copy: [{ from: './public', to: '.' }],
  },
});
