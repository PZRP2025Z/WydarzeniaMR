<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { currentUser } from '$lib/stores/currentUser';

  interface Event {
    id: number;
    name: string;
    location: string;
    description?: string;
    photo?: string | null;
    time?: string;
  }

  let loading = true;
  let error = "";
  let event: Event | null = null;
  let isLoggedIn = false;
  let accepting = false;

  const token = $page.params.token;

  async function loadInvite() {
    try {
      // Check if user is logged in
      const meRes = await fetch("/api/auth/me", { credentials: "include" });
      if (meRes.ok) {
        isLoggedIn = true;
        currentUser.set(await meRes.json());
      }

      // Get invitation details
      const inviteRes = await fetch(`/api/invites/${token}`, {
        credentials: "include"
      });

      if (!inviteRes.ok) {
        if (inviteRes.status === 410) {
          error = "To zaproszenie wygasło";
        } else {
          error = "Nieprawidłowe zaproszenie";
        }
        return;
      }

      const inviteData = await inviteRes.json();

      // Get event details
      const eventRes = await fetch(`/api/events/${inviteData.event_id}`);
      if (!eventRes.ok) {
        error = "Nie udało się pobrać wydarzenia";
        return;
      }

      event = await eventRes.json();
    } catch (err) {
      console.error("Error loading invite:", err);
      error = "Błąd serwera";
    } finally {
      loading = false;
    }
  }

  async function acceptInvitation() {
    if (!isLoggedIn) {
      goto(`/login?next=/invite/${token}`);
      return;
    }

    accepting = true;
    try {
      const res = await fetch(`/api/invites/${token}/accept`, {
        method: "POST",
        credentials: "include"
      });

      if (!res.ok) {
        const errorData = await res.json();
        error = errorData.detail || "Nie udało się przyjąć zaproszenia";
        return;
      }

      const data = await res.json();
      goto(`/events/${data.event_id}`);
    } catch (err) {
      console.error("Error accepting invitation:", err);
      error = "Błąd serwera";
    } finally {
      accepting = false;
    }
  }

  onMount(loadInvite);
</script>

{#if loading}
  <p style="text-align:center; margin-top:3rem;">Ładowanie zaproszenia…</p>

{:else if error}
  <div style="max-width:600px; margin:3rem auto; background:#ffe5e5; padding:1rem; border-radius:6px;">
    {error}
  </div>

{:else if event}
  <div style="max-width:800px; margin:2rem auto; font-family:system-ui;">
    <img
      src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"}
      alt="Zdjęcie wydarzenia"
      style="width:100%; height:300px; object-fit:cover; border-radius:8px;"
    />

    <h1>{event.name}</h1>
    <p style="color:#555;">📍 {event.location}</p>

    {#if event.description}
      <div style="background:#f9f9f9; padding:1rem; border-radius:8px; margin:1rem 0;">
        {event.description}
      </div>
    {/if}

    <hr style="margin:2rem 0;" />

    <div style="text-align:center;">
      {#if isLoggedIn}
        <p style="margin-bottom:1rem; color:#555;">
          Zostałeś zaproszony do tego wydarzenia
        </p>
        <button
          on:click={acceptInvitation}
          disabled={accepting}
          style="padding:0.75rem 2rem; background:#28a745; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-size:1rem; opacity: {accepting ? 0.6 : 1};"
        >
          {accepting ? 'Przyjmowanie...' : 'Przyjmij zaproszenie'}
        </button>
      {:else}
        <p style="margin-bottom:1rem; color:#555;">
          Aby przyjąć zaproszenie, musisz się zalogować
        </p>
        <div style="display:flex; flex-direction:column; gap:0.75rem; max-width:300px; margin:0 auto;">
          <button
            on:click={() => goto(`/login?next=/invite/${token}`)}
            style="padding:0.75rem; background:#007BFF; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold;"
          >
            Zaloguj się
          </button>
          <button
            on:click={() => goto(`/register?next=/invite/${token}`)}
            style="padding:0.75rem; background:#6c757d; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold;"
          >
            Zarejestruj się
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}