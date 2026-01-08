<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { currentUser } from '$lib/stores/currentUser';

  let mail = '';
  let password = '';
  let error = '';
  let loading = false;

  const API_URL = '/api/auth';

  $: nextUrl = $page.url.searchParams.get('next') || '/events';

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
        // fetch current user po zalogowaniu
        const userRes = await fetch(`${API_URL}/me`, { credentials: 'include' });
        if (userRes.ok) {
          currentUser.set(await userRes.json());
        } else {
          currentUser.set(null);
        }
        await goto(nextUrl);
      } else {
        error = t('invalid_credentials', $lang);
      }
    } catch (err) {
      error = t('server_unreachable', $lang);
      console.error(err);
    } finally {
      loading = false;
    }
  }
</script>

<div style="max-width: 400px; margin: 2rem auto; padding: 1.5rem;">
  <h1 style="font-size: 2rem; font-weight: bold; margin-bottom: 1.5rem;">
    {t('login', $lang)}
  </h1>

  {#if error}
    <div style="background-color: #f8d7da; color: #721c24; padding: 0.75rem; border-radius: 0.25rem; margin-bottom: 1rem;">
      {error}
    </div>
  {/if}

  <form on:submit|preventDefault={handleLogin} style="display: flex; flex-direction: column; gap: 1rem;">
    <input type="text" placeholder={t('Email', $lang)} bind:value={mail} style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;" />
    <input type="password" placeholder={t('password', $lang)} bind:value={password} style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;" />
    <button type="submit" disabled={loading} style="padding: 0.5rem; background-color: #007BFF; color: white; border: none; border-radius: 0.25rem; cursor: pointer; opacity: {loading ? 0.6 : 1};">
      {loading ? t('login_loading', $lang) : t('login', $lang)}
    </button>
  </form>

  <p style="margin-top: 1rem; text-align: center;">
    {t('no_account', $lang)} <a href="/register" style="color: #007BFF; text-decoration: none;">{t('register', $lang)}</a>
  </p>
</div>
