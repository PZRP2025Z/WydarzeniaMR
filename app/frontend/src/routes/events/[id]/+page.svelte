<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { marked } from 'marked';

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

  let event: Event | null = null;
  let eventDescriptionHtml = ""; // <- wygenerowany HTML z Markdown
  let loading = true;
  let error = "";

  let eventDate = "";
  let eventTime = "";

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
      const res = await fetch(
        `/api/events/${id}/comments?limit=${commentsLimit}&offset=${commentsOffset}`,
        { credentials: "include" }
      );

      if (!res.ok) {
        commentsError = "Nie udało się pobrać komentarzy.";
        return;
      }

      const data: Comment[] = await res.json();
      comments = [...comments, ...data];
      commentsOffset += data.length;

    } catch (err) {
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
      const res = await fetch(`/api/events/${id}/comments/`, {
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
      comments = [created, ...comments]; // dodaj na górę
      newComment = "";

    } catch (err) {
      addCommentError = "Błąd serwera";
    }
  }

  // -------------------------------
  // ŁADOWANIE WYDARZENIA
  // -------------------------------
  onMount(async () => {
    const id = Number($page.params.id);
    try {
      const res = await fetch(`/api/events/${id}/`);
      if (!res.ok) throw new Error("Nie udało się pobrać wydarzenia.");
      const data: Event = await res.json();
      event = data;

      if (event.time) {
        const d = new Date(event.time);
        eventDate = d.toLocaleDateString();
        eventTime = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else {
        eventDate = "Brak daty";
        eventTime = "Brak godziny";
      }

      event.attendees ??= 0;
      event.description ??= "Brak opisu";

      // render Markdown -> HTML
      eventDescriptionHtml = marked(event.description);

      // Ładujemy komentarze
      loadComments(true);

    } catch (err) {
      error = err instanceof Error ? err.message : "Błąd ładowania wydarzenia";
    } finally {
      loading = false;
    }
  });

  function editEvent() {
    if (!event) return;
    goto(`/events/${event.id}/edit`);
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
  <div style="flex:3; display:flex; flex-direction:column; gap:1.5rem;">

    <img 
      src={event.photo ? `data:image/jpeg;base64,${event.photo}` : "/images/placeholder-event.jpg"} 
      alt="Zdjęcie wydarzenia" 
      style="width:100%; height:300px; object-fit:fill; border-radius:8px;"
    />

    <div style="display:flex; flex-direction:column; gap:0.5rem;">
      <h1 style="font-size:2rem; font-weight:bold; margin:0;">{event.name}</h1>
      <p style="margin:0; color:#555;">Data: {eventDate} | Godzina: {eventTime}</p>
      <p style="margin:0; color:#555;">Lokalizacja: {event.location}</p>
      <p style="margin:0; color:#555;">Liczba uczestników: {event.attendees}</p>
    </div>

    <!-- Render Markdown -->
    <div style="background:#f9f9f9; padding:1rem; border-radius:8px; min-height:150px;">
      {@html eventDescriptionHtml}
    </div>

    <!-- ============================
         KOMENTARZE
    ============================== -->
    <div style="background:#fff; padding:1rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
      <h2 style="margin-top:0; font-size:1.25rem;">Komentarze</h2>

      <!-- Formularz dodawania -->
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

      <!-- Lista komentarzy -->
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

        <!-- Załaduj więcej -->
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

      <button style="padding:0.5rem; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">
        Utwórz link spersonalizowany
      </button>

      <button style="padding:0.5rem; background:#17a2b8; color:white; border:none; border-radius:4px; cursor:pointer;">
        Utwórz link niespersonalizowany
      </button>
    </div>
  </div>
</div>
{/if}
