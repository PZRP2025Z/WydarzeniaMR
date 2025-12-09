<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  interface Event {
    id: number;
    name: string;
    location: string;
    photo?: string | null;
    time?: string;
    description?: string;
    attendees?: number;
  }
 
  let event: Event | null = null;
  let loading = true;
  let error = "";

  let eventDate = "";
  let eventTime = "";


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

      // Fallback dla innych pól
      event.attendees ??= 0;
      event.description ??= "Brak opisu";

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

    <div style="background:#f9f9f9; padding:1rem; border-radius:8px; min-height:150px;">
      {event.description}
    </div>

    <div style="background:#fff; padding:1rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
      <h2 style="margin-top:0; font-size:1.25rem;">Komentarze</h2>
      <p style="color:#999;">Brak komentarzy</p>
    </div>

  </div>

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
