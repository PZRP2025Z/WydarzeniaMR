import { writable } from 'svelte/store';
import type { Lang } from '../i18n';

export const lang = writable<Lang>('pl');