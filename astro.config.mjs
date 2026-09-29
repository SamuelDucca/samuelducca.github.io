import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { readFileSync } from 'node:fs';
import yaml from 'yaml';

const { pages } = yaml.parse(readFileSync(new URL('./site.config.yml', import.meta.url), 'utf8'));

export default defineConfig({
  // Replace with your actual GitHub Pages URL
  devToolbar: { enabled: false },
  site: 'https://samuelducca.github.io',
  integrations: [mdx(), sitemap({
    filter: (page) => {
      const section = new URL(page).pathname.split('/')[1];
      return section ? pages[section] !== false : pages.about !== false;
    },
  })],
  output: 'static',
  vite: {
    plugins: [tailwindcss()],
  },
  markdown: {
    shikiConfig: {
      themes: { light: 'github-light', dark: 'github-dark' },
    },
  },
});
