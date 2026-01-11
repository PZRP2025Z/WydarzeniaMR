<script lang="ts">
  import '../app.css';
  import favicon from '$lib/assets/favicon.svg';
  import { lang } from '$lib/stores/stores';
  import { t } from '$lib/i18n';
  import { goto } from '$app/navigation';
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
    await goto('/login');
  } catch (err) {
    console.error("Błąd przy wylogowaniu:", err);
  } finally {
    currentUser.set(null);
    location.reload();
  }
}

// wywołanie onMount poza funkcją logout
onMount(() => {
  // ustawienie motywu Skeletona
  document.documentElement.setAttribute('data-theme', 'cerberus');
  fetchCurrentUser();
});

</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<!-- NAVBAR -->
<nav
  class="flex items-center gap-4 p-4 border-b border-surface-300
         bg-surface-200 dark:bg-surface-900 shadow-sm"
>
  <a href="/" class="font-semibold text-surface hover:underline">
    {t('home_title', $lang)}
  </a>
  <a href="/events" class="font-semibold text-surface hover:underline">
    {t('add_event', $lang)}
  </a>

  {#if $currentUser === undefined}
    <div class="ml-auto h-6 w-32 bg-surface-200 rounded animate-pulse"></div>

  {:else if $currentUser}
    <div class="ml-auto flex items-center gap-2">
      <span class="font-semibold">
        Witaj: {$currentUser.login ?? $currentUser.email}
      </span>
      <button on:click={logout} class="btn-danger px-3 py-1 rounded">
        Wyloguj
      </button>
    </div>

  {:else}
    <div class="ml-auto flex gap-2">
      <a href="/login" class="btn-primary px-3 py-1 rounded">
        Logowanie
      </a>
      <a href="/register"
         class="px-3 py-1 rounded text-white hover:brightness-110"
         style="background:#6F42C1">
        Rejestracja
      </a>
    </div>
  {/if}
</nav>

<button
  on:click={toggleLang}
  class="ml-4 mt-4 px-3 py-1 rounded
         bg-surface-300 text-surface-900
         dark:bg-surface-700 dark:text-surface-50
         hover:bg-surface-400 dark:hover:bg-surface-600
         transition"
>
  { $lang === 'pl' ? 'EN' : 'PL' }
</button>


<!-- STRONA -->
<main class="mt-4">
  {@render children()}
</main>
