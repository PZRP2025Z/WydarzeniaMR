<script lang="ts">
  import favicon from '$lib/assets/favicon.svg';
  import { lang } from '$lib/stores/stores';
  import { t } from '$lib/i18n';
  import { onMount } from 'svelte';
  import { currentUser } from '$lib/stores/currentUser';

  let { children } = $props();

  function toggleLang() {
    lang.set($lang === 'pl' ? 'en' : 'pl');
  }

  async function fetchCurrentUser() {
    try {
      const res = await fetch(`/api/auth/me`, { credentials: 'include' });
      if (!res.ok) {
        currentUser.set(null);
        return;
      }
      currentUser.set(await res.json());
    } catch (err) {
      console.error("Błąd przy fetch /auth/me:", err);
      currentUser.set(null);
    }
  }

  async function logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    } catch (err) {
      console.error("Błąd przy wylogowaniu:", err);
    } finally {
      currentUser.set(null);
    }
  }

  onMount(() => {
    fetchCurrentUser();
  });
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<nav style="display:flex; align-items:center; gap:1rem; padding:1rem; border-bottom:1px solid #ccc;">
  <a href="/">{t('home_title', $lang)}</a>
  <a href="/events">{t('add_event', $lang)}</a>

  {#if $currentUser}
    <span style="margin-left:auto; font-weight:600;">
      Witaj: {$currentUser.login ?? $currentUser.email}
      <button on:click={logout} style="margin-left:0.5rem;">Wyloguj</button>
    </span>
  {:else}
    <a href="/login" style="margin-left:auto;">Logowanie</a>
    <a href="/register">Rejestracja</a>
  {/if}
</nav>

<button on:click={toggleLang} style="margin:1rem;">
  { $lang === 'pl' ? 'EN' : 'PL' }
</button>

{@render children()}
