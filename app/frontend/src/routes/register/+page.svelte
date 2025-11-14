<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  import { goto } from '$app/navigation';

  let username = '';
  let email = '';
  let password = '';
  let passwordConfirm = '';
  let error = '';
  let loading = false;

  const API_URL = 'http://127.0.0.1:8000/auth';

  async function handleRegister() {
    error = '';
    
    if (!username.trim() || !email.trim() || !password.trim()) {
      error = 'Wszystkie pola są wymagane';
      return;
    }

    if (password !== passwordConfirm) {
      error = 'Hasła się nie zgadzają';
      return;
    }

    loading = true;

    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          first_name: username,
          last_name: '',
          email, 
          password 
        })
      });

      if (response.ok) {
        await goto('/login');
      } else {
        const data = await response.json();
        error = data.detail || 'Błąd rejestracji';
      }
    } catch (err) {
      error = 'Nie można połączyć się z serwerem';
      console.error(err);
    } finally {
      loading = false;
    }
  }
</script>

<div style="max-width: 400px; margin: 2rem auto; padding: 1.5rem;">
  <h1 style="font-size: 2rem; font-weight: bold; margin-bottom: 1.5rem;">Rejestracja</h1>

  {#if error}
    <div style="background-color: #f8d7da; color: #721c24; padding: 0.75rem; border-radius: 0.25rem; margin-bottom: 1rem;">
      {error}
    </div>
  {/if}

  <form onsubmit={(e) => { e.preventDefault(); handleRegister(); }} style="display: flex; flex-direction: column; gap: 1rem;">
    <input
      type="text"
      placeholder="Nazwa użytkownika"
      bind:value={username}
      style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;"
    />
    
    <input
      type="email"
      placeholder="Email"
      bind:value={email}
      style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;"
    />
    
    <input
      type="password"
      placeholder="Hasło"
      bind:value={password}
      style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;"
    />
    
    <input
      type="password"
      placeholder="Potwierdź hasło"
      bind:value={passwordConfirm}
      style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;"
    />
    
    <button
      type="submit"
      disabled={loading}
      style="padding: 0.5rem; background-color: #007BFF; color: white; border: none; border-radius: 0.25rem; cursor: pointer; opacity: {loading ? 0.6 : 1};"
    >
      {loading ? 'Rejestrowanie...' : 'Zarejestruj się'}
    </button>
  </form>

  <p style="margin-top: 1rem; text-align: center;">
    Masz już konto? <a href="/login" style="color: #007BFF; text-decoration: none;">Zaloguj się</a>
  </p>
</div>