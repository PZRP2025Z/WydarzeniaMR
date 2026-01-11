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
  <div class="max-w-md mx-auto mt-12 px-4">
    <div class="card p-6">
      <div class="animate-pulse space-y-4">
        <div class="h-48 bg-surface-200 rounded"></div>
        <div class="h-6 bg-surface-200 rounded w-3/4"></div>
        <div class="h-4 bg-surface-200 rounded w-1/2"></div>
      </div>
    </div>
  </div>

{:else if error}
  <div class="max-w-md mx-auto mt-12 px-4">
    <div class="card p-4 bg-error-100 text-error-700">
      {error}
    </div>
  </div>

{:else if event}
  <div class="max-w-3xl mx-auto mt-8 px-4">
    <div class="card p-6 space-y-4">
      <img
        src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"}
        alt="Zdjęcie wydarzenia"
        class="w-full h-72 object-cover rounded-lg shadow"
      />

      <div>
        <h1 class="text-2xl font-semibold">{event.name}</h1>
        <p class="text-sm text-surface-600">📍 {event.location}</p>
      </div>

      {#if event.description}
        <div class="bg-surface-100 dark:bg-surface-800 p-4 rounded break-words whitespace-pre-wrap">{event.description}</div>
      {/if}

      <hr class="my-4" />

      <div class="text-center">
        {#if isLoggedIn}
          <p class="mb-4 text-surface-600">Zostałeś zaproszony do tego wydarzenia</p>
          <button
            on:click={acceptInvitation}
            disabled={accepting}
            class="btn btn-primary w-full"
            style="opacity: {accepting ? 0.6 : 1};"
          >
            {accepting ? 'Przyjmowanie...' : 'Przyjmij zaproszenie'}
          </button>
        {:else}
          <p class="mb-4 text-surface-600">Aby przyjąć zaproszenie, musisz się zalogować</p>
          <div class="space-y-3 max-w-xs mx-auto">
            <button
              on:click={() => goto(`/login?next=/invite/${token}`)}
              class="btn btn-primary w-full"
            >
              Zaloguj się
            </button>
            <button
              on:click={() => goto(`/register?next=/invite/${token}`)}
              class="btn w-full"
              style="background:#6c757d; color:white"
            >
              Zarejestruj się
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}