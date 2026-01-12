<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';

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
        participationError = t('error_save_participation', $lang);
        return;
      }

      myParticipation = status;
      await loadParticipationStats();
    } catch {
      participationError = t('server_error', $lang);
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
        commentsError = t('error_comments_load', $lang);
        return;
      }
      const data: Comment[] = await res.json();
      comments = [...comments, ...data];
      commentsOffset += data.length;
    } catch {
      commentsError = t('error_comments_loading', $lang);
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
        addCommentError = j?.detail ?? t('error_add_comment', $lang);
        return;
      }

      const created: Comment = await res.json();
      comments = [created, ...comments];
      newComment = "";
    } catch {
      addCommentError = t('server_error', $lang);
    }
  }

  // -------------------------------
  // ŁADOWANIE WYDARZENIA
  // -------------------------------
  onMount(async () => {
    const id = Number($page.params.id);

    try {
      const res = await fetch(`/api/events/${id}`);
      if (!res.ok) throw new Error(t('error_loading_event', $lang));
      event = await res.json();

      if (event.time) {
        const d = new Date(event.time);
        eventDate = d.toLocaleDateString();
        eventTime = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else {
        eventDate = t('no_date', $lang);
        eventTime = t('no_time', $lang);
      }

      event.description ??= t('no_description', $lang);
      event.attendees ??= 0;
      eventDescriptionHtml = marked(event.description);

      await loadComments(true);
      await loadMyParticipation();
      await loadParticipationStats();
    } catch (err) {
      error = err instanceof Error ? err.message : t('error_loading_event', $lang);
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
    { type: "event_updated", label: t('notification_event_updated', $lang) },
    { type: "participant_joined", label: t('notification_participant_joined', $lang) }
  ];

  const channels: { channel: NotificationChannel; label: string; icon: string }[] = [
    { channel: "email", label: t('channel_email', $lang), icon: "📧" }
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
        throw new Error(t('error_load_preferences', $lang));
      }

      notificationPreferences = await res.json();
      
      preferencesMap = {};
      notificationPreferences.forEach(pref => {
        const key = getPreferenceKey(pref.notification_type, pref.channel);
        preferencesMap[key] = pref.subscribed;
      });

    } catch (err) {
      preferencesError = err instanceof Error ? err.message : t('error_loading_preferences', $lang);
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
        throw new Error(data?.detail ?? t('error_save_preferences', $lang));
      }

      notificationPreferences = await res.json();
      showNotificationModal = false;
    } catch (err) {
      preferencesError = err instanceof Error ? err.message : t('error_saving_preferences', $lang);
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
        passError = j?.detail ?? t('error_create_pass', $lang);
        return;
      }

      const data = await res.json();
      createdPassLink = data.link;
    } catch {
      passError = t('server_error', $lang);
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
        inviteError = j?.detail ?? t('error_create_invite', $lang);
        return;
      }

      const data = await res.json();
      createdInviteLink = data.link;
    } catch {
      inviteError = t('server_error', $lang);
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

  function downloadICS() {
    if (!event || !event.time) return;

    const start = new Date(event.time);
    const end = new Date(start.getTime() + 60 * 60 * 1000);

    const formatICSDate = (d: Date) =>
      d.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

    const icsContent = `
  BEGIN:VCALENDAR
  VERSION:2.0
  PRODID:-//YourApp//Event Calendar//EN
  CALSCALE:GREGORIAN
  BEGIN:VEVENT
  UID:event-${event.id}@yourapp
  DTSTAMP:${formatICSDate(new Date())}
  DTSTART:${formatICSDate(start)}
  DTEND:${formatICSDate(end)}
  SUMMARY:${event.name}
  DESCRIPTION:${(event.description ?? "").replace(/\n/g, "\\n")}
  LOCATION:${event.location ?? ""}
  END:VEVENT
  END:VCALENDAR
  `.trim();

    const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `${event.name}.ics`;
    document.body.appendChild(a);
    a.click();

    document.body.removeChild(a);
    URL.revokeObjectURL(url);s
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
      <span class="inline-flex items-center gap-2 px-2 py-1 bg-surface-100 dark:bg-surface-700 rounded text-surface-700 dark:text-white">{t('stat_going', $lang)} <strong class="ml-1">{participationStats.going}</strong></span>
      <span class="inline-flex items-center gap-2 px-2 py-1 bg-surface-100 dark:bg-surface-700 rounded text-surface-700 dark:text-white">{t('stat_maybe', $lang)} <strong class="ml-1">{participationStats.maybe}</strong></span>
      <span class="inline-flex items-center gap-2 px-2 py-1 bg-surface-100 dark:bg-surface-700 rounded text-surface-700 dark:text-white">{t('stat_not_going', $lang)} <strong class="ml-1">{participationStats.not_going}</strong></span>
    </div>

    <div class="card p-6 bg-surface">
      <h1 class="text-2xl font-semibold mb-1">{event.name}</h1>
      <p class="text-sm text-surface-600 mb-1">{t('date_label', $lang)}: {eventDate} | {t('time_label', $lang)}: {eventTime}</p>
      <p class="text-sm text-surface-600 mb-1">{t('event_location', $lang)}: {event.location}</p>
      <!-- <p class="text-sm text-surface-600">{t('attendees', $lang)}: {event.attendees}</p> -->

      <hr class="my-4" />

      <div class="prose max-w-none break-words whitespace-pre-wrap">
        {@html eventDescriptionHtml}
      </div>
    </div>

    <!-- KOMENTARZE -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold mb-3">{t('comments', $lang)}</h2>

      {#if addCommentError}
        <div class="bg-error-100 text-error-700 p-2 rounded mb-3">{addCommentError}</div>
      {/if}

      <textarea
        rows="3"
        placeholder={t('add_comment_placeholder', $lang)}
        bind:value={newComment}
        class="textarea w-full mb-2"
      ></textarea>

      <div class="flex items-center gap-2">
        <button on:click={sendComment} class="btn btn-primary" disabled={loadingComments}>{loadingComments ? t('adding_comment', $lang) : t('add_comment', $lang)}</button>
      </div>

      <hr class="my-4" />

      {#if loadingComments}
        <p>{t('loading_comments', $lang)}</p>
      {:else if commentsError}
        <div class="text-error-700">{commentsError}</div>
      {:else if comments.length === 0}
        <p class="text-surface-500">{t('no_comments', $lang)}</p>
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
            {loadingMoreComments ? t('loading_more', $lang) : t('load_more', $lang)}
          </button>
        {/if}
      {/if}
    </div>
  </div>

  <!-- Kolumna boczna -->
  <div class="space-y-6">
    <div class="card p-4 space-y-3">
      <button on:click={editEvent} class="btn btn-primary w-full">{t('edit_event', $lang)}</button>

      <hr />

      <button
        on:click={() => showNotificationModal = true}
        class="btn w-full bg-amber-500 text-white flex items-center justify-center gap-2 px-3"
      >
        <span class="text-lg">🔔</span>
        <span class="text-center whitespace-normal">{t('notifications', $lang)}</span>
      </button>

      <button
        on:click={addToGoogleCalendar}
        class="btn btn-danger w-full flex items-center justify-center gap-2 px-3"
      >
        <img src="/images/Google_Calendar_icon_(2020).svg.png" alt="Google Calendar" class="w-5 h-5 shrink-0" />
        <span class="text-center whitespace-normal">{t('add_to_google_calendar', $lang)}</span>
      </button>

      <button
        on:click={downloadICS}
        class="btn w-full flex items-center justify-center gap-2 px-3 bg-indigo-600 text-white"
      >
        <span class="text-lg">📅</span>
        <span class="text-center whitespace-normal">
          {t('download_ics', $lang)}
        </span>
      </button>

      <hr />

      <strong>{t('your_attendance', $lang)}</strong>
      <div class="space-y-2">
        <button
          disabled={participationLoading}
          on:click={() => setParticipation("going")}
          class="btn w-full"
          class:bg-emerald-600={myParticipation === 'going'}
          class:text-white={myParticipation === 'going'}
        >
          {t('participation_going', $lang)}
        </button>

        <button
          disabled={participationLoading}
          on:click={() => setParticipation("maybe")}
          class="btn w-full"
          class:bg-amber-400={myParticipation === 'maybe'}
          class:text-black={myParticipation === 'maybe'}
        >
          {t('participation_maybe', $lang)}
        </button>

        <button
          disabled={participationLoading}
          on:click={() => setParticipation("not_going")}
          class="btn w-full"
          class:bg-rose-600={myParticipation === 'not_going'}
          class:text-white={myParticipation === 'not_going'}
        >
          {t('participation_not_going', $lang)}
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
        {t('create_invite', $lang)}
      </button>
      
      <button
        on:click={() => showPassModal = true}
        class="btn w-full"
        style="background:#6f42c1; color:white"
      >
        {t('create_pass', $lang)}
      </button>
    </div>
  </div>

</div>
{/if}

<!-- Modal powiadomień -->
{#if showNotificationModal}
  <div class="fixed inset-0 flex items-center justify-center z-50 bg-black/40 backdrop-blur-sm">
    <div class="bg-surface-50 dark:bg-surface-900 border-surface-200 dark:border-surface-800 card p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto space-y-4 mx-4">
      <h3 class="text-lg font-semibold m-0">{t('notification_settings', $lang)}</h3>
      <p class="text-surface-700 dark:text-surface-300 text-sm m-0">{t('notification_settings_desc', $lang)}</p>

      {#if loadingPreferences}
        <div class="text-center text-surface-600 py-6">{t('loading_preferences', $lang)}</div>
      {:else}
        <div class="flex flex-col gap-4">
          {#each notificationTypes as { type, label }}
            <div class="bg-surface-50 dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded p-4">
              <h4 class="text-sm font-medium mb-3 text-surface-700 dark:text-surface-300">{label}</h4>

              <div class="flex flex-col gap-2">
                {#each channels as { channel, label: channelLabel, icon }}
                  <label
                    class="flex items-center gap-2 p-3 rounded cursor-pointer border border-surface-200 dark:border-surface-800 transition"
                    class:bg-primary-100={isSubscribed(type, channel)}
                    class:border-primary-600={isSubscribed(type, channel)}
                  >
                    <input
                      type="checkbox"
                      checked={isSubscribed(type, channel)}
                      on:change={() => togglePreference(type, channel)}
                      class="cursor-pointer"
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
        <div class="text-error-700 text-sm">{preferencesError}</div>
      {/if}

      <div class="grid grid-cols-2 gap-2 mt-2">
        <button
          disabled={savingPreferences}
          on:click={saveNotificationPreferences}
          class="btn btn-primary"
          style="opacity: {savingPreferences ? 0.6 : 1};"
        >
          {savingPreferences ? t('saving_preferences', $lang) : t('save', $lang)}
        </button>

        <button
          on:click={closeNotificationModal}
          class="btn w-full bg-surface-100 text-surface-900"
        >
          {t('cancel', $lang)}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showPassModal}
  <div class="fixed inset-0 flex items-center justify-center z-50 bg-black/40 backdrop-blur-sm">
    <div class="bg-surface-50 dark:bg-surface-900 border-surface-200 dark:border-surface-800 card p-6 w-full max-w-sm space-y-4 mx-4 bg-surface shadow-lg rounded-lg">
      <h3 class="text-lg font-semibold m-0">{t('create_pass', $lang)}</h3>

      <label class="text-sm text-surface-700 dark:text-surface-300">{t('pass_display_name_label', $lang)}</label>

      <input
        type="text"
        bind:value={passDisplayName}
        placeholder={t('pass_display_placeholder', $lang)}
        class="input"
      />

      {#if passError}
        <div class="text-error-700 text-sm">{passError}</div>
      {/if}

      {#if createdPassLink}
        <div class="bg-surface-100 dark:bg-surface-800 p-2 rounded">
          <strong>{t('link_label', $lang)}</strong>
          <div class="break-words text-sm mt-1">{createdPassLink}</div>
        </div>

        <button
          on:click={() => navigator.clipboard.writeText(createdPassLink)}
          class="btn btn-success w-full"
        >
          {t('copy_link', $lang)}
        </button>
      {:else}
        <button
          disabled={creatingPass || !passDisplayName.trim()}
          on:click={createPass}
          class="btn btn-primary w-full"
        >
          {creatingPass ? t('creating_pass', $lang) : t('create', $lang)}
        </button>
      {/if}

      <button
        on:click={closePassModal}
        class="btn w-full mt-2"
      >
        {t('close', $lang)}
      </button>
    </div>
  </div>
{/if}

{#if showInviteModal}
  <div class="fixed inset-0 flex items-center justify-center z-50 bg-black/40 backdrop-blur-sm">
    <div class="bg-surface-50 dark:bg-surface-900 border-surface-200 dark:border-surface-800 card p-6 w-full max-w-sm space-y-4 mx-4 bg-surface shadow-lg rounded-lg">
      <h3 class="text-lg font-semibold m-0">{t('create_invite', $lang)}</h3>
      <p class="text-sm text-surface-700 dark:text-surface-300 m-0">{t('invite_description', $lang)}</p>

      {#if inviteError}
        <div class="text-error-700 text-sm">{inviteError}</div>
      {/if}

      {#if createdInviteLink}
        <div class="bg-surface-100 dark:bg-surface-800 p-2 rounded">
          <strong>{t('invite_link_label', $lang)}</strong>
          <div class="break-words text-sm mt-1">{createdInviteLink}</div>
        </div>

        <button
          on:click={() => navigator.clipboard.writeText(createdInviteLink)}
          class="btn btn-success w-full"
        >
          {t('copy_link', $lang)}
        </button>
      {:else}
        <button
          disabled={creatingInvite}
          on:click={createInvite}
          class="btn btn-primary w-full"
        >
          {creatingInvite ? t('creating_invite', $lang) : t('create_invite', $lang)}
        </button>
      {/if}

      <button
        on:click={closeInviteModal}
        class="btn w-full mt-2"
      >
        {t('close', $lang)}
      </button>
    </div>
  </div>
{/if}