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
  <p style="text-align:center; color:#666;">Ładowanie wydarzenia...</p>
{:else if error}
  <div style="background:#ffe5e5; border:1px solid #ff9999; color:#900; padding:12px; border-radius:6px;">
    {error}
  </div>
{:else if event}
<div style="display:flex; max-width:1200px; margin:2rem auto; gap:2rem; font-family:system-ui, sans-serif;">

  <!-- Główna kolumna -->
  <div style="flex:3; display:flex; flex-direction:column; gap:1.5rem;">

    <img 
      src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"} 
      alt="Zdjęcie wydarzenia" 
      style="width:100%; height:300px; object-fit:fill; border-radius:8px;"
    />

    <div style="display:flex; gap:1rem; color:#555; font-size:0.95rem;">
      <span>✅ Będą: <strong>{participationStats.going}</strong></span>
      <span>🤔 Może: <strong>{participationStats.maybe}</strong></span>
      <span>❌ Nie będą: <strong>{participationStats.not_going}</strong></span>
    </div>

    <div style="display:flex; flex-direction:column; gap:0.5rem;">
      <h1 style="font-size:2rem; font-weight:bold; margin:0;">{event.name}</h1>
      <p style="margin:0; color:#555;">Data: {eventDate} | Godzina: {eventTime}</p>
      <p style="margin:0; color:#555;">Lokalizacja: {event.location}</p>
      <p style="margin:0; color:#555;">Liczba uczestników: {event.attendees}</p>
    </div>

    <div class="markdown-content" style="background:#f9f9f9; padding:1rem; border-radius:8px; min-height:150px;">
      {@html eventDescriptionHtml}
    </div>

    <!-- KOMENTARZE -->
    <div style="background:#fff; padding:1rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
      <h2 style="margin-top:0; font-size:1.25rem;">Komentarze</h2>

      {#if addCommentError}
        <p style="color:red;">{addCommentError}</p>
      {/if}

      <textarea
        rows="3"
        placeholder="Dodaj komentarz..."
        bind:value={newComment}
        style="width:100%; border:1px solid #ccc; border-radius:6px; padding:0.5rem; margin-bottom:0.5rem;"
      ></textarea>

      <button on:click={sendComment}
        style="padding:0.5rem 1rem; background:#007BFF; color:white; border:none; border-radius:4px; cursor:pointer;">
        Dodaj komentarz
      </button>

      <hr style="margin:1rem 0;" />

      {#if loadingComments}
        <p>Ładowanie komentarzy…</p>
      {:else if commentsError}
        <p style="color:red;">{commentsError}</p>
      {:else if comments.length === 0}
        <p style="color:#999;">Brak komentarzy</p>
      {:else}
        {#each comments as c}
          <div style="padding:0.5rem 0; border-bottom:1px solid #eee;">
            <strong>{c.user_login}</strong>
            <p style="margin:0.25rem 0;">{c.content}</p>
            <small style="color:#888;">{new Date(c.created_at).toLocaleString()}</small>
          </div>
        {/each}

        {#if comments.length >= commentsLimit}
          <button
            on:click={() => { loadingMoreComments = true; loadComments(false); }}
            disabled={loadingMoreComments}
            style="margin-top:1rem; padding:0.5rem; border:none; background:#eee; border-radius:4px; cursor:pointer;"
          >
            {loadingMoreComments ? "Ładowanie..." : "Załaduj więcej"}
          </button>
        {/if}
      {/if}
    </div>
  </div>

  <!-- Kolumna boczna -->
  <div style="flex:1; display:flex; flex-direction:column; gap:1rem;">
    <div style="background:#fff; padding:1rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.1); display:flex; flex-direction:column; gap:0.75rem;">
      <button on:click={editEvent} style="padding:0.5rem; background:#007BFF; color:white; border:none; border-radius:4px; cursor:pointer;">
        Edytuj wydarzenie
      </button>

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
      <button
        disabled={participationLoading}
        on:click={() => setParticipation("going")}
        style="padding:0.5rem; background:{myParticipation === 'going' ? '#1e7e34' : '#28a745'}; color:white; border:none; border-radius:4px; cursor:pointer;">
        Będę
      </button>

      <button
        disabled={participationLoading}
        on:click={() => setParticipation("maybe")}
        style="padding:0.5rem; background:{myParticipation === 'maybe' ? '#d39e00' : '#ffc107'}; color:black; border:none; border-radius:4px; cursor:pointer;">
        Może będę
      </button>

      <button
        disabled={participationLoading}
        on:click={() => setParticipation("not_going")}
        style="padding:0.5rem; background:{myParticipation === 'not_going' ? '#bd2130' : '#dc3545'}; color:white; border:none; border-radius:4px; cursor:pointer;">
        Nie będzie mnie
      </button>

      {#if participationError}
        <p style="color:red;">{participationError}</p>
      {/if}

      <hr />

      <button
        on:click={() => showInviteModal = true}
        style="padding:0.5rem; background:#17a2b8; color:white; border:none; border-radius:4px; cursor:pointer;">
        Utwórz zaproszenie
      </button>
      
      <button
        on:click={() => showPassModal = true}
        style="padding:0.5rem; background:#6f42c1; color:white; border:none; border-radius:4px; cursor:pointer;">
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
        max-width:400px;
        box-shadow:0 10px 30px rgba(0,0,0,0.2);
        display:flex;
        flex-direction:column;
        gap:0.75rem;
      "
    >
      <h3 style="margin:0;">Utwórz przepustkę</h3>

      <label style="font-size:0.9rem; color:#555;">
        Imię / nazwa gościa
      </label>

      <input
        type="text"
        bind:value={passDisplayName}
        placeholder="np. Jan Kowalski"
        style="padding:0.5rem; border:1px solid #ccc; border-radius:4px;"
      />

      {#if passError}
        <p style="color:red; font-size:0.9rem;">{passError}</p>
      {/if}

      {#if createdPassLink}
        <div style="background:#f5f5f5; padding:0.5rem; border-radius:4px;">
          <strong>Link:</strong>
          <div style="word-break:break-all; font-size:0.85rem;">
            {createdPassLink}
          </div>
        </div>

        <button
          on:click={() => navigator.clipboard.writeText(createdPassLink)}
          style="padding:0.5rem; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;"
        >
          Kopiuj link
        </button>
      {:else}
        <button
          disabled={creatingPass || !passDisplayName.trim()}
          on:click={createPass}
          style="padding:0.5rem; background:#007BFF; color:white; border:none; border-radius:4px; cursor:pointer;"
        >
          {creatingPass ? "Tworzenie..." : "Utwórz"}
        </button>
      {/if}

      <button
        on:click={closePassModal}
        style="padding:0.4rem; background:#eee; border:none; border-radius:4px; cursor:pointer;"
      >
        Zamknij
      </button>
    </div>
  </div>
{/if}

{#if showInviteModal}
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
        max-width:400px;
        box-shadow:0 10px 30px rgba(0,0,0,0.2);
        display:flex;
        flex-direction:column;
        gap:0.75rem;
      "
    >
      <h3 style="margin:0;">Utwórz zaproszenie</h3>
      <p style="font-size:0.9rem; color:#666; margin:0;">
        Link wielokrotnego użytku dla użytkowników z kontem
      </p>

      {#if inviteError}
        <p style="color:red; font-size:0.9rem;">{inviteError}</p>
      {/if}

      {#if createdInviteLink}
        <div style="background:#f5f5f5; padding:0.5rem; border-radius:4px;">
          <strong>Link zaproszenia:</strong>
          <div style="word-break:break-all; font-size:0.85rem;">
            {createdInviteLink}
          </div>
        </div>

        <button
          on:click={() => navigator.clipboard.writeText(createdInviteLink)}
          style="padding:0.5rem; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;"
        >
          Kopiuj link
        </button>
      {:else}
        <button
          disabled={creatingInvite}
          on:click={createInvite}
          style="padding:0.5rem; background:#007BFF; color:white; border:none; border-radius:4px; cursor:pointer; opacity:{creatingInvite ? 0.6 : 1};"
        >
          {creatingInvite ? "Tworzenie..." : "Utwórz zaproszenie"}
        </button>
      {/if}

      <button
        on:click={closeInviteModal}
        style="padding:0.4rem; background:#eee; border:none; border-radius:4px; cursor:pointer;"
      >
        Zamknij
      </button>
    </div>
  </div>
{/if}