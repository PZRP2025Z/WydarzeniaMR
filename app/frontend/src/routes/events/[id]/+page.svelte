<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  interface Event {
    id: number;
    name: string;
    location: string;
    // placeholders
    date?: string;
    time?: string;
    attendees?: number;
    description?: string;
  }
 
  let event: Event | null = null;
  let loading = true;
  let error = "";

  const API_URL = "http://127.0.0.1:8000/events";

  onMount(async () => {
    const id = Number($page.params.id);
    try {
      const res = await fetch(`${API_URL}/${id}`);
      if (!res.ok) throw new Error("Nie udało się pobrać wydarzenia.");
      const data: Event = await res.json();
      event = data;
      // fillers
      event.date ??= "31.02.2130";
      event.time ??= "25:37";
      event.attendees ??= 0;
      event.description ??= "Opis";
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
  <!-- Główna kolumna -->
  <div style="flex:3; display:flex; flex-direction:column; gap:1.5rem;">

    <img 
        src="/images/placeholder-event.jpg" 
        alt="Zdjęcie wydarzenia" 
        style="width:100%; height:300px; object-fit:cover; border-radius:8px;"
    />


    <!-- Nagłówek z podstawowymi informacjami -->
    <div style="display:flex; flex-direction:column; gap:0.5rem;">
      <h1 style="font-size:2rem; font-weight:bold; margin:0;">{event.name}</h1>
      <p style="margin:0; color:#555;">Data: {event.date} | Godzina: {event.time}</p>
      <p style="margin:0; color:#555;">Lokalizacja: {event.location}</p>
      <p style="margin:0; color:#555;">Liczba uczestników: {event.attendees}</p>
    </div>

    <!-- Opis wydarzenia -->
    <div style="background:#f9f9f9; padding:1rem; border-radius:8px; min-height:150px;">
      {event.description}
    </div>

    <!-- Sekcja komentarzy -->
    <div style="background:#fff; padding:1rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
      <h2 style="margin-top:0; font-size:1.25rem;">Komentarze</h2>
      <p style="color:#999;">Brak komentarzy</p>
    </div>

  </div>

  <!-- Panel kontrolny po prawej -->
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
