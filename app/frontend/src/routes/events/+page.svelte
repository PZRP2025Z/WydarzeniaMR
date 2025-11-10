<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  import { onMount } from 'svelte';

  let events: { id: number; name: string; location: string }[] = [];
  let newEvent = { name: '', location: '' };

  const API_URL = 'http://127.0.0.1:8000/events';

  async function fetchEvents() {
    try {
      const res = await fetch(`${API_URL}/`);
      if (!res.ok) throw new Error('Couldn\'t fetch events');
      events = await res.json();
    } catch (err) {
      console.error(err);
    }
  }

  async function addEvent() {
    if (newEvent.name.trim() && newEvent.location.trim()) {
      const url = `${API_URL}/?name=${encodeURIComponent(newEvent.name)}&location=${encodeURIComponent(newEvent.location)}`;
      try {
        const response = await fetch(url, {
          method: 'POST'
        });

        if (response.ok) {
          const createdEvent = await response.json();
          events = [...events, createdEvent];
          newEvent = { name: '', location: '' };
        } else {
          console.error('Couldn\'t add event', await response.json());
        }
      } catch (err) {
        console.error(err);
      }
    }
  }

  async function deleteEvent(id: number) {
    try {
      const res = await fetch(`${API_URL}/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Couldn\'t delete event');
      events = events.filter(e => e.id !== id);
    } catch (err) {
      console.error(err);
    }
  }

  onMount(() => {
    fetchEvents();
  });
</script>

<div style="max-width: 600px; margin: 2rem auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem;">

  <h1 style="font-size: 2rem; font-weight: bold;">{t('title', $lang)}</h1>

  <!-- Formularz dodania wydarzenia -->
  <div style="background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border-radius: 0.5rem; padding: 1rem; display: flex; flex-direction: column; gap: 1rem;">
    <h2 style="font-size: 1.25rem; font-weight: 600;">{t('add_event', $lang)}</h2>

    <input
      placeholder={t('event_title', $lang)}
      bind:value={newEvent.name}
      style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;"
    />
    <input
      placeholder={t('event_location', $lang)}
      bind:value={newEvent.location}
      style="padding: 0.5rem; border: 1px solid #ccc; border-radius: 0.25rem; width: 100%;"
    />
    <button 
      on:click={addEvent}
      style="padding: 0.5rem; background-color: #007BFF; color: white; border: none; border-radius: 0.25rem; cursor: pointer;"
    >
      {t('add_event', $lang)}
    </button>
  </div>

  <!-- Lista gebeurteneń -->
  <div style="display: flex; flex-direction: column; gap: 0.75rem;">
    {#each events as event (event.id)}
      <div style="background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border-radius: 0.5rem; padding: 1rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <p style="font-weight: 600;">{event.name}</p>
          <p style="font-size: 0.875rem; color: #666;">{event.location}</p>
        </div>
        <button 
          on:click={() => deleteEvent(event.id)}
          style="padding: 0.25rem 0.5rem; border: 1px solid #dc3545; color: #dc3545; border-radius: 0.25rem; background: none; cursor: pointer;"
        >
          {t('remove_event', $lang)}
        </button>
      </div>
    {/each}
  </div>
</div>