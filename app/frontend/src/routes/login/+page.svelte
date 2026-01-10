<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/currentUser';

  let mail = '';
  let password = '';
  let error = '';
  let loading = false;

  const API_URL = '/api/auth';

  async function handleLogin() {
    error = '';

    if (!mail.trim() || !password.trim()) {
      error = t('mail_password_required', $lang);
      return;
    }

    loading = true;

    try {
      const formData = new FormData();
      formData.append('mail', mail);
      formData.append('password', password);

      const response = await fetch(`${API_URL}/token`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      if (response.ok) {
        const userRes = await fetch(`${API_URL}/me`, { credentials: 'include' });
        currentUser.set(userRes.ok ? await userRes.json() : null);
        await goto('/events');
      } else {
        error = t('invalid_credentials', $lang);
      }
    } catch {
      error = t('server_unreachable', $lang);
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-[70vh] flex items-center justify-center px-4">
  <div class="w-full max-w-md bg-surface border border-surface-300 rounded-xl p-6 shadow">
    <h1 class="text-2xl font-bold mb-6">
      {t('login', $lang)}
    </h1>

    {#if error}
      <div class="mb-4 bg-error-100 text-error-700 p-3 rounded">
        {error}
      </div>
    {/if}

    <form on:submit|preventDefault={handleLogin} class="flex flex-col gap-4">
      <input
        type="email"
        placeholder={t('email', $lang)}
        bind:value={mail}
        class="input"
      />

      <input
        type="password"
        placeholder={t('password', $lang)}
        bind:value={password}
        class="input"
      />

      <button
        type="submit"
        disabled={loading}
        class="btn btn-primary w-full font-semibold"
      >
        {loading ? t('login_loading', $lang) : t('login', $lang)}
      </button>
    </form>

    <p class="mt-6 text-sm text-center text-surface-600">
      {t('no_account', $lang)}
      <a href="/register" class="text-primary font-medium hover:underline hover:text-primary-hover ml-1">
        {t('register', $lang)}
      </a>
    </p>
  </div>
</div>
