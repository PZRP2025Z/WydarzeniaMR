<script lang="ts">
  import { goto } from '$app/navigation';

  let newEvent = { name: '', location: '', time: '', description: '', photo: null as string | null };
  let loading = false;
  let error = '';

  function handleFileSelect(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      newEvent.photo = (reader.result as string).split(',')[1]; // Base64
    };
    reader.readAsDataURL(file);
  }

  async function addEvent() {
    if (!newEvent.name.trim() || !newEvent.location.trim() || !newEvent.time.trim()) return;

    loading = true;
    error = '';

    try {
      const res = await fetch(`/api/events/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEvent),
        credentials: 'include'
      });

      if (!res.ok) {
        const data = await res.json();
        error = data.detail || 'Nie udało się dodać wydarzenia';
        return;
      }

      const createdEvent = await res.json();
      goto(`/events/${createdEvent.id}`);
    } catch (err) {
      console.error(err);
      error = 'Błąd serwera';
    } finally {
      loading = false;
    }
  }
</script>

<div style="max-width:600px; margin:2rem auto; display:flex; flex-direction:column; gap:1rem;">
  <h1>Dodaj nowe wydarzenie</h1>

  {#if error}<p style="color:red">{error}</p>{/if}

  <input placeholder="Tytuł" bind:value={newEvent.name} />
  <input placeholder="Lokalizacja" bind:value={newEvent.location} />
  <input placeholder="Data i godzina" bind:value={newEvent.time} type="datetime-local" />
  <textarea placeholder="Opis" bind:value={newEvent.description}></textarea>
  <input type="file" accept="image/*" on:change={handleFileSelect} />

  <button on:click={addEvent} disabled={loading}>Dodaj wydarzenie</button>
</div>
