import { skeleton } from '@skeletonlabs/tw-plugin';
import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: { extend: {} },
  plugins: [
    skeleton({
      themes: { preset: ['cerberus'] }
    }),
    typography()
  ]
};
