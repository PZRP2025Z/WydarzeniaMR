<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { marked } from "marked";
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
        error = "Nieprawidłowa lub wygasła przepustka";
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
            error = "Nie udało się zalogować";
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
          error = "Nie udało się pobrać wydarzenia";
          return;
        }

        event = await eventRes.json();
        event.description ??= "Brak opisu";
        eventDescriptionHtml = marked(event.description);
      }
    } catch {
      error = "Błąd serwera";
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
            error = "Nie udało się dołączyć";
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
            error = "Nie udało się zalogować";
        }
    } catch (err) {
        console.error("Error in joinAsGuest:", err);
        error = "Błąd serwera";
    }
  }

  async function acceptInvitation() {
    try {
        const res = await fetch(`/api/passes/${token}/accept-login`, {
            method: "POST",
            credentials: "include"
        });

        if (!res.ok) {
            error = "Nie udało się przyjąć zaproszenia";
            return;
        }

        goto(`/events/${event?.id}`);
    } catch (err) {
        console.error("Error accepting invitation:", err);
        error = "Błąd serwera";
    }
  }

  onMount(loadPass);
</script>

{#if loading}
  <p style="text-align:center; margin-top:3rem;">Ładowanie przepustki…</p>

{:else if error}
  <div style="max-width:600px; margin:3rem auto; background:#ffe5e5; padding:1rem; border-radius:6px;">
    {error}
  </div>

{:else if event && status === "unbound"}
  <div style="max-width:800px; margin:2rem auto; font-family:system-ui;">

    <img
      src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"}
      alt="Zdjęcie wydarzenia"
      style="width:100%; height:300px; object-fit:cover; border-radius:8px;"
    />

    <h1>{event.name}</h1>
    <p style="color:#555;">📍 {event.location}</p>

    <div style="background:#f9f9f9; padding:1rem; border-radius:8px;">
      {@html eventDescriptionHtml}
    </div>

    <hr style="margin:2rem 0;" />

    <div style="display:flex; flex-direction:column; gap:0.75rem;">
      {#if isLoggedIn}
        <!-- Show single button for logged-in users -->
        <button
          on:click={acceptInvitation}
          style="padding:0.75rem; background:#28a745; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold;"
        >
          Przyjmij zaproszenie
        </button>
      {:else}
        <!-- Show all options for non-logged-in users -->
        <button
          on:click={joinAsGuest}
          style="padding:0.75rem; background:#28a745; color:white; border:none; border-radius:6px; cursor:pointer;"
        >
          Dołącz bez konta
        </button>

        <button
          on:click={() => goto(`/login?next=/pass/${token}`)}
          style="padding:0.75rem; background:#007BFF; color:white; border:none; border-radius:6px; cursor:pointer;"
        >
          Zaloguj się
        </button>

        <button
          on:click={() => goto(`/register?next=/pass/${token}`)}
          style="padding:0.75rem; background:#6c757d; color:white; border:none; border-radius:6px; cursor:pointer;"
        >
          Zarejestruj się
        </button>
      {/if}
    </div>
  </div>
{/if}