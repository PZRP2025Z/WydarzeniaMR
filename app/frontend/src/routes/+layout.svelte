<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { lang } from '$lib/stores/stores';
	import { t } from '$lib/i18n';

	let { children } = $props();

	function toggleLang() {
		lang.set($lang === 'pl' ? 'en' : 'pl');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<nav>
    <a href="/">{t('home_title', $lang)}</a>
    <a href="/events">{t('add_event', $lang)}</a>
    <a href="/login">Logowanie</a>
    <a href="/register">Rejestracja</a>
</nav>

<button onclick={toggleLang}>
	{ $lang === 'pl' ? 'EN' : 'PL' }
</button>

{@render children()}
