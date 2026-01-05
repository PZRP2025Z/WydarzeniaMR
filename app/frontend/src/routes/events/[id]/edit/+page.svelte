<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

  interface Event {
    id: number;
    name: string;
    location: string;
    time: string;          // ISO string z backendu
    description?: string;
    photo?: string | null; // Base64
  }

  let event: Event | null = null;
  let formData = { name: '', location: '', time: '', description: '', photo: null as string | null };
  let loading = true;
  let error = '';

  const API_URL = '/api/events';

  // Ładowanie danych wydarzenia
  onMount(async () => {
    const id = Number($page.params.id);
    try {
      const res = await fetch(`${API_URL}/${id}`, { credentials: 'include' });
      if (!res.ok) throw new Error("Nie udało się pobrać wydarzenia");
      const data: Event = await res.json();
      event = data;

      // Format dla datetime-local: YYYY-MM-DDTHH:MM
      formData = {
        ...data,
        time: data.time ? data.time.slice(0, 16) : '',
        photo: data.photo || null
      };
    } catch (err) {
      error = err instanceof Error ? err.message : "Błąd ładowania";
    } finally {
      loading = false;
    }
  });

  // Obsługa wczytania pliku zdjęcia
  function handleFileSelect(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      formData.photo = (reader.result as string).split(',')[1]; // Base64
    };
    reader.readAsDataURL(file);
  }

  // Aktualizacja wydarzenia
  async function updateEvent() {
    if (!event) return;

    try {
      const res = await fetch(`${API_URL}/${event.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        credentials: 'include'
      });

      if (!res.ok) {
        const data = await res.json();
        error = data.detail || "Nie udało się zaktualizować wydarzenia";
        return;
      }

      const updated = await res.json();
      goto(`/events/${updated.id}`);
    } catch (err) {
      console.error(err);
      error = "Błąd serwera";
    }
  }
</script>

<div style="max-width:600px; margin:2rem auto; display:flex; flex-direction:column; gap:1rem;">
  {#if loading}
    <p>Ładowanie...</p>
  {:else if error}
    <p style="color:red">{error}</p>
  {:else if event}
    <h1>Edytuj wydarzenie</h1>

    <input placeholder="Tytuł" bind:value={formData.name} />
    <input placeholder="Lokalizacja" bind:value={formData.location} />
    <input type="datetime-local" bind:value={formData.time} />
    <textarea placeholder="Opis" bind:value={formData.description}></textarea>
    <input type="file" accept="image/*" on:change={handleFileSelect} />

    <button on:click={updateEvent}>Zapisz zmiany</button>
  {/if}
</div>
