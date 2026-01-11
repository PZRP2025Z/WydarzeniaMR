<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { marked } from 'marked';

  // -------------------------------
  // TYPY
  // -------------------------------
  interface Event {
    id: number;
    name: string;
    location: string;
    photo?: string | null;
    time?: string;
    description?: string;
    attendees?: number;
  }

  interface Comment {
    id: number;
    content: string;
    user_login: string;
    created_at: string;
  }

  type ParticipationStatus = "going" | "maybe" | "not_going" | null;

  // -------------------------------
  // EVENT
  // -------------------------------
  let event: Event | null = null;
  let eventDescriptionHtml = "";
  let loading = true;
  let error = "";

  let eventDate = "";
  let eventTime = "";

  // -------------------------------
  // PARTICIPATION (RSVP)
  // -------------------------------
  let myParticipation: ParticipationStatus = null;
  let participationLoading = false;
  let participationError = "";

  let participationStats = {
    going: 0,
    maybe: 0,
    not_going: 0
  };

  async function loadMyParticipation() {
    const id = Number($page.params.id);

    try {
      const res = await fetch(`/api/participations/events/${id}/me`, { credentials: "include" });
      if (!res.ok) {
        myParticipation = null;
        return;
      }
      const data = await res.json();
      myParticipation = data?.status ?? null;
    } catch {
      myParticipation = null;
    }
  }

  async function loadParticipationStats() {
    const id = Number($page.params.id);
    try {
      const res = await fetch(`/api/participations/events/${id}/stats`, { credentials: "include" });
      if (!res.ok) return;
      participationStats = await res.json();
    } catch {
      // ignorujemy błędy statystyk
    }
  }

  async function setParticipation(status: ParticipationStatus) {
    if (!status) return;
    participationLoading = true;
    participationError = "";

    const id = Number($page.params.id);

    try {
      const res = await fetch(`/api/participations/events/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status }),
      });


      if (!res.ok) {
        participationError = "Nie udało się zapisać decyzji";
        return;
      }

      myParticipation = status;
      await loadParticipationStats();
    } catch {
      participationError = "Błąd serwera";
    } finally {
      participationLoading = false;
    }
  }

  // -------------------------------
  // KOMENTARZE
  // -------------------------------
  let comments: Comment[] = [];
  let newComment = "";
  let commentsOffset = 0;
  const commentsLimit = 10;
  let loadingComments = false;
  let loadingMoreComments = false;
  let addCommentError = "";
  let commentsError = "";

  async function loadComments(initial = false) {
    try {
      if (initial) {
        commentsOffset = 0;
        comments = [];
      }
      loadingComments = true;
      const id = Number($page.params.id);
      const res = await fetch(`/api/events/${id}/comments?limit=${commentsLimit}&offset=${commentsOffset}`, { credentials: "include" });
      if (!res.ok) {
        commentsError = "Nie udało się pobrać komentarzy.";
        return;
      }
      const data: Comment[] = await res.json();
      comments = [...comments, ...data];
      commentsOffset += data.length;
    } catch {
      commentsError = "Błąd podczas ładowania komentarzy";
    } finally {
      loadingComments = false;
      loadingMoreComments = false;
    }
  }

  async function sendComment() {
    addCommentError = "";
    if (!newComment.trim()) return;
    const id = Number($page.params.id);

    try {
      const res = await fetch(`/api/events/${id}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ content: newComment })
      });

      if (!res.ok) {
        let j;
        try { j = await res.json(); } catch {}
        addCommentError = j?.detail ?? "Nie udało się dodać komentarza";
        return;
      }

      const created: Comment = await res.json();
      comments = [created, ...comments];
      newComment = "";
    } catch {
      addCommentError = "Błąd serwera";
    }
  }

  // -------------------------------
  // ŁADOWANIE WYDARZENIA
  // -------------------------------
  onMount(async () => {
    const id = Number($page.params.id);

    try {
      const res = await fetch(`/api/events/${id}`);
      if (!res.ok) throw new Error("Nie udało się pobrać wydarzenia.");
      event = await res.json();

      if (event.time) {
        const d = new Date(event.time);
        eventDate = d.toLocaleDateString();
        eventTime = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else {
        eventDate = "Brak daty";
        eventTime = "Brak godziny";
      }

      event.description ??= "Brak opisu";
      event.attendees ??= 0;
      eventDescriptionHtml = marked(event.description);

      await loadComments(true);
      await loadMyParticipation();
      await loadParticipationStats();
    } catch (err) {
      error = err instanceof Error ? err.message : "Błąd ładowania wydarzenia";
    } finally {
      loading = false;
    }
  });

  // -------------------------------
  // POWIADOMIENIA
  // -------------------------------
  let showNotificationModal = false;
  let notificationPreferences: NotificationPreference[] = [];
  let loadingPreferences = false;
  let savingPreferences = false;
  let preferencesError = "";

  // Struktura do zarządzania preferencjami w UI
  const notificationTypes: { type: NotificationType; label: string }[] = [
    { type: "event_updated", label: "Aktualizacje wydarzenia" },
    { type: "participant_joined", label: "Nowi uczestnicy" }
  ];

  const channels: { channel: NotificationChannel; label: string; icon: string }[] = [
    { channel: "email", label: "Email", icon: "📧" }
  ];

  // Mapa preferencji
  let preferencesMap: Record<string, boolean> = {};

  function getPreferenceKey(type: NotificationType, channel: NotificationChannel): string {
    return `${type}:${channel}`;
  }

  async function loadNotificationPreferences() {
    if (!event) return;
    
    loadingPreferences = true;
    preferencesError = "";

    try {
      const res = await fetch(`/api/notifications/events/${event.id}/preferences`, {
        credentials: "include"
      });

      if (!res.ok) {
        throw new Error("Nie udało się pobrać preferencji");
      }

      notificationPreferences = await res.json();
      
      preferencesMap = {};
      notificationPreferences.forEach(pref => {
        const key = getPreferenceKey(pref.notification_type, pref.channel);
        preferencesMap[key] = pref.subscribed;
      });

    } catch (err) {
      preferencesError = err instanceof Error ? err.message : "Błąd ładowania preferencji";
    } finally {
      loadingPreferences = false;
    }
  }

  function isSubscribed(type: NotificationType, channel: NotificationChannel): boolean {
    const key = getPreferenceKey(type, channel);
    return preferencesMap[key] ?? false;
  }

  function togglePreference(type: NotificationType, channel: NotificationChannel) {
    const key = getPreferenceKey(type, channel);
    preferencesMap[key] = !preferencesMap[key];
  }

  async function saveNotificationPreferences() {
    if (!event) return;

    savingPreferences = true;
    preferencesError = "";

    try {
      const preferences = [];
      for (const { type } of notificationTypes) {
        for (const { channel } of channels) {
          preferences.push({
            notification_type: type,
            channel: channel,
            subscribed: isSubscribed(type, channel)
          });
        }
      }

      const res = await fetch(`/api/notifications/events/${event.id}/preferences`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ preferences })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? "Nie udało się zapisać preferencji");
      }

      notificationPreferences = await res.json();
      showNotificationModal = false;
    } catch (err) {
      preferencesError = err instanceof Error ? err.message : "Błąd zapisywania preferencji";
    } finally {
      savingPreferences = false;
    }
  }

  function closeNotificationModal() {
    showNotificationModal = false;
    preferencesError = "";
    loadNotificationPreferences();
  }

  // -------------------------------
  // PRZEPUSTKI
  // -------------------------------
  let showPassModal = false;
  let passDisplayName = "";
  let creatingPass = false;
  let passError = "";
  let createdPassLink: string | null = null;

  async function createPass() {
    if (!event) return;

    passError = "";
    createdPassLink = null;
    creatingPass = true;

    try {
      const res = await fetch(`/api/passes/personal/${event.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ display_name: passDisplayName })
      });

      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        passError = j?.detail ?? "Nie udało się utworzyć przepustki";
        return;
      }

      const data = await res.json();
      createdPassLink = data.link;
    } catch {
      passError = "Błąd serwera";
    } finally {
      creatingPass = false;
    }
  }

  function closePassModal() {
    showPassModal = false;
    passDisplayName = "";
    passError = "";
    createdPassLink = null;
  }

  // -------------------------------
  // ZAPROSZENIA
  // -------------------------------
  let showInviteModal = false;
  let creatingInvite = false;
  let inviteError = "";
  let createdInviteLink: string | null = null;

  async function createInvite() {
    if (!event) return;

    inviteError = "";
    createdInviteLink = null;
    creatingInvite = true;

    try {
      const res = await fetch(`/api/invites/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ event_id: event.id })
      });

      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        inviteError = j?.detail ?? "Nie udało się utworzyć zaproszenia";
        return;
      }

      const data = await res.json();
      createdInviteLink = data.link;
    } catch {
      inviteError = "Błąd serwera";
    } finally {
      creatingInvite = false;
    }
  }

  function closeInviteModal() {
    showInviteModal = false;
    inviteError = "";
    createdInviteLink = null;
  }


  // -------------------------------
  // INNE FUNKCJE
  // -------------------------------
  function editEvent() {
    if (!event) return;
    goto(`/events/${event.id}/edit`);
  }

  function formatDateForGoogleCalendar(dateStr?: string) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toISOString().replace(/-|:|\.\d+/g, "");
  }

  function addToGoogleCalendar() {
    if (!event) return;
    const start = formatDateForGoogleCalendar(event.time);
    const endDate = event.time ? new Date(new Date(event.time).getTime() + 60*60*1000) : null;
    const end = endDate ? formatDateForGoogleCalendar(endDate.toISOString()) : start;
    const params = new URLSearchParams({
      action: "TEMPLATE",
      text: event.name,
      dates: `${start}/${end}`,
      details: event.description ?? "",
      location: event.location ?? ""
    });
    window.open(`https://www.google.com/calendar/render?${params.toString()}`, "_blank");
  }
</script>

{#if loading}
  <div class="max-w-3xl mx-auto mt-8 px-4">
    <div class="card p-6">
      <div class="animate-pulse space-y-4">
        <div class="h-64 bg-surface-200 rounded"></div>
        <div class="h-6 bg-surface-200 rounded w-1/2"></div>
        <div class="h-4 bg-surface-200 rounded w-1/3"></div>
      </div>
    </div>
  </div>
{:else if error}
  <div class="max-w-3xl mx-auto mt-8 px-4">
    <div class="card p-4 bg-error-100 text-error-700">
      {error}
    </div>
  </div>
{:else if event}
<div class="max-w-6xl mx-auto mt-8 px-4 grid grid-cols-1 lg:grid-cols-4 gap-6">

  <!-- Główna kolumna -->
  <div class="lg:col-span-3 space-y-6">

    <img 
      src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"} 
      alt="Zdjęcie wydarzenia" 
      class="w-full h-72 object-cover rounded-lg shadow"
    />

    <div class="flex gap-4 text-sm text-surface-600">
      <span class="inline-flex items-center gap-2 px-2 py-1 bg-surface-100 dark:bg-surface-700 rounded text-surface-700 dark:text-white">✅ Będą: <strong class="ml-1">{participationStats.going}</strong></span>
      <span class="inline-flex items-center gap-2 px-2 py-1 bg-surface-100 dark:bg-surface-700 rounded text-surface-700 dark:text-white">🤔 Może: <strong class="ml-1">{participationStats.maybe}</strong></span>
      <span class="inline-flex items-center gap-2 px-2 py-1 bg-surface-100 dark:bg-surface-700 rounded text-surface-700 dark:text-white">❌ Nie będą: <strong class="ml-1">{participationStats.not_going}</strong></span>
    </div>

    <div class="card p-6 bg-surface">
      <h1 class="text-2xl font-semibold mb-1">{event.name}</h1>
      <p class="text-sm text-surface-600 mb-1">Data: {eventDate} | Godzina: {eventTime}</p>
      <p class="text-sm text-surface-600 mb-1">Lokalizacja: {event.location}</p>
      <p class="text-sm text-surface-600">Liczba uczestników: {event.attendees}</p>

      <hr class="my-4" />

      <div class="prose max-w-none break-words whitespace-pre-wrap">
        {@html eventDescriptionHtml}
      </div>
    </div>

    <!-- KOMENTARZE -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold mb-3">Komentarze</h2>

      {#if addCommentError}
        <div class="bg-error-100 text-error-700 p-2 rounded mb-3">{addCommentError}</div>
      {/if}

      <textarea
        rows="3"
        placeholder="Dodaj komentarz..."
        bind:value={newComment}
        class="textarea w-full mb-2"
      ></textarea>

      <div class="flex items-center gap-2">
        <button on:click={sendComment} class="btn btn-primary" disabled={loadingComments}>{loadingComments ? 'Dodawanie…' : 'Dodaj komentarz'}</button>
      </div>

      <hr class="my-4" />

      {#if loadingComments}
        <p>Ładowanie komentarzy…</p>
      {:else if commentsError}
        <div class="text-error-700">{commentsError}</div>
      {:else if comments.length === 0}
        <p class="text-surface-500">Brak komentarzy</p>
      {:else}
        {#each comments as c}
          <div class="py-3 border-b border-surface-200">
            <strong>{c.user_login}</strong>
            <p class="mt-1 break-words whitespace-pre-wrap">{c.content}</p>
            <small class="text-surface-500">{new Date(c.created_at).toLocaleString()}</small>
          </div>
        {/each}

        {#if comments.length >= commentsLimit}
          <button
            on:click={() => { loadingMoreComments = true; loadComments(false); }}
            disabled={loadingMoreComments}
            class="btn w-full mt-4"
          >
            {loadingMoreComments ? "Ładowanie..." : "Załaduj więcej"}
          </button>
        {/if}
      {/if}
    </div>
  </div>

  <!-- Kolumna boczna -->
  <div class="space-y-6">
    <div class="card p-4 space-y-3">
      <button on:click={editEvent} class="btn btn-primary w-full">Edytuj wydarzenie</button>

      <hr />

      <button 
        on:click={() => showNotificationModal = true} 
        style="padding:0.5rem; background:#ff9800; color:white; border:none; border-radius:4px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:0.5rem;">
        🔔 Powiadomienia
      </button>

      <button on:click={addToGoogleCalendar} style="padding:0.5rem; background:#f44336; color:white; border:none; border-radius:4px; cursor:pointer;">
        Dodaj do kalendarza Google
      </button>

      <hr />

      <strong>Twoja obecność</strong>
      <div class="space-y-2">
        <button
          disabled={participationLoading}
          on:click={() => setParticipation("going")}
          class="btn w-full"
          class:bg-emerald-600={myParticipation === 'going'}
          class:text-white={myParticipation === 'going'}
        >
          Będę
        </button>

        <button
          disabled={participationLoading}
          on:click={() => setParticipation("maybe")}
          class="btn w-full"
          class:bg-amber-400={myParticipation === 'maybe'}
          class:text-black={myParticipation === 'maybe'}
        >
          Może będę
        </button>

        <button
          disabled={participationLoading}
          on:click={() => setParticipation("not_going")}
          class="btn w-full"
          class:bg-rose-600={myParticipation === 'not_going'}
          class:text-white={myParticipation === 'not_going'}
        >
          Nie będzie mnie
        </button>

        {#if participationError}
          <div class="text-error-700">{participationError}</div>
        {/if}
      </div>

      <hr />

      <button
        on:click={() => showInviteModal = true}
        class="btn w-full bg-teal-600 text-white"
      >
        Utwórz zaproszenie
      </button>
      
      <button
        on:click={() => showPassModal = true}
        class="btn w-full"
        style="background:#6f42c1; color:white"
      >
        Utwórz przepustkę
      </button>
    </div>
  </div>

</div>
{/if}

<!-- Modal powiadomień -->
{#if showNotificationModal}
  <div
    style="
      position:fixed;
      inset:0;
      background:rgba(0,0,0,0.5);
      display:flex;
      align-items:center;
      justify-content:center;
      z-index:1000;
    "
  >
    <div
      style="
        background:white;
        padding:1.5rem;
        border-radius:8px;
        width:100%;
        max-width:500px;
        max-height:80vh;
        overflow-y:auto;
        box-shadow:0 10px 30px rgba(0,0,0,0.2);
        display:flex;
        flex-direction:column;
        gap:1rem;
      "
    >
      <h3 style="margin:0; font-size:1.5rem;">Ustawienia powiadomień</h3>
      <p style="margin:0; color:#666; font-size:0.9rem;">
        Wybierz, jakie powiadomienia chcesz otrzymywać o tym wydarzeniu
      </p>

      {#if loadingPreferences}
        <p style="color:#666; text-align:center;">Ładowanie...</p>
      {:else}
        <div style="display:flex; flex-direction:column; gap:1.5rem;">
          {#each notificationTypes as { type, label }}
            <div style="border:1px solid #e0e0e0; border-radius:6px; padding:1rem;">
              <h4 style="margin:0 0 0.75rem 0; font-size:1rem; color:#333;">{label}</h4>
              
              <div style="display:flex; flex-direction:column; gap:0.5rem;">
                {#each channels as { channel, label: channelLabel, icon }}
                  <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer; padding:0.5rem; border-radius:4px; background:{isSubscribed(type, channel) ? '#f0f7ff' : 'transparent'}; border:1px solid {isSubscribed(type, channel) ? '#007BFF' : '#e0e0e0'};">
                    <input
                      type="checkbox"
                      checked={isSubscribed(type, channel)}
                      on:change={() => togglePreference(type, channel)}
                      style="cursor:pointer;"
                    />
                    <span>{icon} {channelLabel}</span>
                  </label>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}

      {#if preferencesError}
        <p style="color:red; font-size:0.9rem; margin:0;">{preferencesError}</p>
      {/if}

      <div style="display:flex; gap:0.5rem; margin-top:0.5rem;">
        <button
          disabled={savingPreferences}
          on:click={saveNotificationPreferences}
          style="flex:1; padding:0.75rem; background:#007BFF; color:white; border:none; border-radius:4px; cursor:pointer; opacity:{savingPreferences ? 0.6 : 1}; font-weight:500;"
        >
          {savingPreferences ? "Zapisywanie..." : "Zapisz"}
        </button>

        <button
          on:click={closeNotificationModal}
          style="flex:1; padding:0.75rem; background:#f5f5f5; color:#333; border:none; border-radius:4px; cursor:pointer; font-weight:500;"
        >
          Anuluj
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showPassModal}
  <div class="fixed inset-0 flex items-center justify-center z-50 bg-black/40 backdrop-blur-sm">
    <div class="card p-6 w-full max-w-sm space-y-4 mx-4 bg-surface shadow-lg rounded-lg">
      <h3 class="text-lg font-semibold m-0">Utwórz przepustkę</h3>

      <label class="text-sm text-surface-600">Imię / nazwa gościa</label>

      <input
        type="text"
        bind:value={passDisplayName}
        placeholder="np. Jan Kowalski"
        class="input"
      />

      {#if passError}
        <div class="text-error-700 text-sm">{passError}</div>
      {/if}

      {#if createdPassLink}
        <div class="bg-surface-100 dark:bg-surface-800 p-2 rounded">
          <strong>Link:</strong>
          <div class="break-words text-sm mt-1">{createdPassLink}</div>
        </div>

        <button
          on:click={() => navigator.clipboard.writeText(createdPassLink)}
          class="btn btn-success w-full"
        >
          Kopiuj link
        </button>
      {:else}
        <button
          disabled={creatingPass || !passDisplayName.trim()}
          on:click={createPass}
          class="btn btn-primary w-full"
        >
          {creatingPass ? "Tworzenie..." : "Utwórz"}
        </button>
      {/if}

      <button
        on:click={closePassModal}
        class="btn w-full mt-2"
      >
        Zamknij
      </button>
    </div>
  </div>
{/if}

{#if showInviteModal}
  <div class="fixed inset-0 flex items-center justify-center z-50 bg-black/40 backdrop-blur-sm">
    <div class="card p-6 w-full max-w-sm space-y-4 mx-4 bg-surface shadow-lg rounded-lg">
      <h3 class="text-lg font-semibold m-0">Utwórz zaproszenie</h3>
      <p class="text-sm text-surface-600 m-0">Link wielokrotnego użytku dla użytkowników z kontem</p>

      {#if inviteError}
        <div class="text-error-700 text-sm">{inviteError}</div>
      {/if}

      {#if createdInviteLink}
        <div class="bg-surface-100 dark:bg-surface-800 p-2 rounded">
          <strong>Link zaproszenia:</strong>
          <div class="break-words text-sm mt-1">{createdInviteLink}</div>
        </div>

        <button
          on:click={() => navigator.clipboard.writeText(createdInviteLink)}
          class="btn btn-success w-full"
        >
          Kopiuj link
        </button>
      {:else}
        <button
          disabled={creatingInvite}
          on:click={createInvite}
          class="btn btn-primary w-full"
        >
          {creatingInvite ? "Tworzenie..." : "Utwórz zaproszenie"}
        </button>
      {/if}

      <button
        on:click={closeInviteModal}
        class="btn w-full mt-2"
      >
        Zamknij
      </button>
    </div>
  </div>
{/if}