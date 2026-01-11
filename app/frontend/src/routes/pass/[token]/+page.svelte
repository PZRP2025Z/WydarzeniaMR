<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { marked } from "marked";
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
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
  let status: "logged_in" | "unbound" | "login_required" | null = null;

  let event: Event | null = null;
  let eventDescriptionHtml = "";
  let isLoggedIn = false;

  const token = $page.params.token;

  async function loadPass() {
    try {
      // Check if user is already logged in
      const meRes = await fetch("/api/auth/me", { credentials: "include" });
      if (meRes.ok) {
        isLoggedIn = true;
        currentUser.set(await meRes.json());
      }

      const res = await fetch(`/api/passes/${token}`, {
        credentials: "include"
      });

      if (!res.ok) {
        error = t('error_bad_pass', $lang);
        return;
      }

      const data = await res.json();
      status = data.status;

      if (status === "logged_in") {
        const meRes = await fetch("/api/auth/me", { credentials: "include" });
        
        if (meRes.ok) {
            const userData = await meRes.json();
            console.log("User data received:", userData);
            currentUser.set(userData);
        } else {
            console.error("Failed to fetch user, status:", meRes.status);
            const errorText = await meRes.text();
            console.error("Error:", errorText);
            error = t('error_login_fail', $lang);
        }
        goto(`/events/${data.event_id}`);
        return;
      }

      if (status === "login_required") {
        const acceptRes = await fetch(`/api/passes/${token}/accept-login`, {
            method: "POST",
            credentials: "include"
        });
        if (!acceptRes.ok) {
            goto(`/login?next=/pass/${token}`);
            return;
        }

        const me = await fetch("/api/auth/me", { credentials: "include" });
        if (me.ok) {
            currentUser.set(await me.json());
        } else {
            currentUser.set(null);
        }

        goto(`/events/${data.event_id}`);
        return;
      }

      if (status === "unbound") {
        const eventRes = await fetch(`/api/events/${data.event_id}`);
        if (!eventRes.ok) {
          error = t('error_event_load_fail', $lang);
          return;
        }

        event = await eventRes.json();
        event.description ??= t('no_description', $lang);
        eventDescriptionHtml = marked(event.description);
      }
    } catch {
      error = t('server_error', $lang);
    } finally {
      loading = false;
    }
  }

  async function joinAsGuest() {
    try {
        const res = await fetch(`/api/passes/${token}/accept-guest`, {
            method: "POST",
            credentials: "include"
        });

        console.log("Response headers:", res.headers);
        console.log("Response status:", res.status);
        
        if (!res.ok) {
            error = t('error_guest_join_fail', $lang);
            return;
        }

        const data = await res.json();
        
        await new Promise(resolve => setTimeout(resolve, 100));

        const meRes = await fetch("/api/auth/me", { credentials: "include" });
        
        if (meRes.ok) {
            const userData = await meRes.json();
            console.log("User data received:", userData);
            currentUser.set(userData);
            goto(`/events/${event?.id}`);
        } else {
            console.error("Failed to fetch user, status:", meRes.status);
            const errorText = await meRes.text();
            console.error("Error:", errorText);
            error = t('error_login_fail', $lang);
        }
    } catch (err) {
        console.error("Error in joinAsGuest:", err);
        error = t('server_error', $lang);
    }
  }

  async function acceptInvitation() {
    try {
        const res = await fetch(`/api/passes/${token}/accept-login`, {
            method: "POST",
            credentials: "include"
        });

        if (!res.ok) {
            error = t('error_accept_invitation', $lang);
            return;
        }

        goto(`/events/${event?.id}`);
    } catch (err) {
        console.error("Error accepting invitation:", err);
        error = t('server_error', $lang);
    }
  }

  onMount(loadPass);
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

{:else if event && status === "unbound"} 
  <div class="max-w-3xl mx-auto mt-8 px-4">
    <div class="card p-6 space-y-4">
      <img
        src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"}
        alt={t('event_photo_alt', $lang)}
        class="w-full h-72 object-cover rounded-lg shadow"
      />

      <div>
        <h1 class="text-2xl font-semibold">{event.name}</h1>
        <p class="text-sm text-surface-600">📍 {event.location}</p>
      </div>

      <div class="bg-surface-100 dark:bg-surface-800 p-4 rounded break-words whitespace-pre-wrap">{@html eventDescriptionHtml}</div>

      <hr class="my-4" />

      <div>
        {#if isLoggedIn}
          <button
            on:click={acceptInvitation}
            class="btn btn-primary w-full"
          >
            {t('accept_invitation', $lang)}
          </button>
        {:else}
          <div class="space-y-3">
            <button
              on:click={joinAsGuest}
              class="btn w-full"
              style="background:#28a745; color:white"
            >
              {t('join_as_guest', $lang)}
            </button>

            <button
              on:click={() => goto(`/login?next=/pass/${token}`)}
              class="btn btn-primary w-full"
            >
              {t('login', $lang)}
            </button>

            <button
              on:click={() => goto(`/register?next=/pass/${token}`)}
              class="btn w-full"
              style="background:#6c757d; color:white"
            >
              {t('register', $lang)}
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}