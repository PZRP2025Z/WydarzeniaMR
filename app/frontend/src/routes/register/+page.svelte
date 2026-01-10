<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/currentUser';

  let username = '';
  let email = '';
  let password = '';
  let passwordConfirm = '';
  let error = '';
  let loading = false;

  const API_URL = '/api/auth';

  async function handleRegister() {
    error = '';

    if (!username || !email || !password) {
      error = t('username_password_required', $lang);
      return;
    }

    if (password !== passwordConfirm) {
      error = t('passwords_do_not_match', $lang);
      return;
    }

    loading = true;

    try {
      const res = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: username, email, password }),
        credentials: 'include'
      });

      if (res.ok) {
        const userRes = await fetch(`${API_URL}/me`, { credentials: 'include' });
        currentUser.set(userRes.ok ? await userRes.json() : null);
        await goto('/events');
      } else {
        const data = await res.json();
        error = data.detail || t('registration_error', $lang);
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
      {t('register', $lang)}
    </h1>

    {#if error}
      <div class="mb-4 bg-error-100 text-error-700 p-3 rounded">
        {error}
      </div>
    {/if}

    <form on:submit|preventDefault={handleRegister} class="flex flex-col gap-4">
      <input class="input" placeholder={t('username', $lang)} bind:value={username} />
      <input class="input" type="email" placeholder={t('email', $lang)} bind:value={email} />
      <input class="input" type="password" placeholder={t('password', $lang)} bind:value={password} />
      <input class="input" type="password" placeholder={t('confirm_password', $lang)} bind:value={passwordConfirm} />

      <button type="submit" disabled={loading} class="btn btn-primary w-full font-semibold">
        {loading ? t('register_loading', $lang) : t('register', $lang)}
      </button>
    </form>

    <p class="mt-6 text-sm text-center text-surface-600">
      {t('already_account', $lang)}
      <a href="/login" class="text-primary font-medium hover:underline hover:text-primary-hover ml-1">
        {t('login', $lang)}
      </a>
    </p>
  </div>
</div>
