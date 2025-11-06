import pl from './locales/pl.json';
import en from './locales/en.json';

// eksportujemy typ Lang
export type Lang = 'pl' | 'en';

type Translations = typeof pl;

export const locales: Record<Lang, Translations> = { pl, en };

export function t(key: keyof Translations, lang: Lang = 'pl') {
    return locales[lang][key] || key;
}
