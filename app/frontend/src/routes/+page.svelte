<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  interface EventItem {
    id: number;
    name: string;
    location: string;
  }

  let events: EventItem[] = [];
  const API_URL = 'http://127.0.0.1:8000/events';

  async function fetchEvents() {
    try {
      const res = await fetch(`${API_URL}/`);
      if (!res.ok) throw new Error("Couldn't fetch events");
      events = await res.json();
    } catch (err) {
      console.error(err);
    }
  }

  onMount(() => {
    fetchEvents();
  });

  function goToEvent(id: number) {
    goto(`/events/${id}`);
  }
</script>

<div style="max-width: 600px; margin: 2rem auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
  <h2 style="font-size: 1.25rem; font-weight: 600;">{t('title', $lang)}</h2>

  <div style="display: flex; flex-direction: column; gap: 0.75rem;">
    {#each events as event (event.id)}
      <div 
        style="background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border-radius: 0.5rem; padding: 1rem; display: flex; justify-content: space-between; align-items: center;"
      >
        <div>
          <p style="font-weight: 600; margin: 0;">{event.name}</p>
          <p style="font-size: 0.875rem; color: #666; margin: 0;">{event.location}</p>
        </div>
        <button 
          on:click={() => goToEvent(event.id)}
          style="padding: 0.5rem 0.75rem; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          Zobacz szczegóły
        </button>
      </div>
    {/each}

    {#if events.length === 0}
      <p style="color:#666;">{t('no_events', $lang)}</p>
    {/if}
  </div>
</div>
