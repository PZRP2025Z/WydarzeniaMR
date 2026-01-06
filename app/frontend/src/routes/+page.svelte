<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/currentUser';
  import { get } from 'svelte/store';

  interface EventItem {
    id: number;
    name: string;
    location: string;
    time: string; // ISO string
    owner_id: number;
    participation_status?: 'going' | 'maybe' | 'not_going' | null;
  }

  let events: EventItem[] = [];
  let loading = true;
  let error = "";
  let now = new Date(); // <-- teraz mamy globalną zmienną "teraz"

  async function fetchMyEvents() {
    const user = get(currentUser);
    if (!user) {
      loading = false;
      return;
    }

    try {
      const res = await fetch(`/api/participations/me/events`, { credentials: "include" });
      if (!res.ok) throw new Error("Nie udało się pobrać Twoich wydarzeń");
      const data: EventItem[] = await res.json();

      const nowDate = new Date();

      const futureEvents = data.filter(e => new Date(e.time) >= nowDate);
      const pastEvents = data.filter(e => new Date(e.time) < nowDate);

      futureEvents.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
      pastEvents.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

      events = [...futureEvents, ...pastEvents];
      now = nowDate; // aktualizujemy globalny "now"
    } catch (err) {
      console.error(err);
      error = err instanceof Error ? err.message : "Błąd przy pobieraniu wydarzeń";
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    const unsubscribe = currentUser.subscribe(user => {
      if (user) fetchMyEvents();
      else loading = false;
    });
  });

  function goToEvent(id: number) {
    goto(`/events/${id}`);
  }

  function daysUntilEvent(event: EventItem) {
    const eventDate = new Date(event.time);
    const diff = Math.ceil((eventDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diff === 0) return "Dzisiaj";
    if (diff > 0) return `Za ${diff} dni`;
    return null;
  }
</script>

<style>
  .tag {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: white;
  }
  .owner { background: #007BFF; }
  .going { background: #28a745; }
  .maybe { background: #ffc107; color: #333; }
  .past { background: #6c757d; }
  .separator { border-top: 1px solid #ccc; margin: 1rem 0; }
</style>

<div style="max-width: 600px; margin: 2rem auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
  <h2 style="font-size: 1.25rem; font-weight: 600;">Moje wydarzenia</h2>

  {#if loading}
    <p style="color:#666;">Ładowanie wydarzeń…</p>
  {:else if error}
    <p style="color:red;">{error}</p>
  {:else if events.length === 0}
    <p style="color:#666;">Nie masz jeszcze żadnych wydarzeń</p>
  {:else}
    {#each events as event, i (event.id)}
      {#if i > 0 && new Date(events[i-1].time) < now && new Date(event.time) >= now}
        <div class="separator"></div>
      {/if}

      <div 
        style="background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border-radius: 0.5rem; padding: 1rem; display: flex; justify-content: space-between; align-items: center;"
      >
        <div>
          <p style="font-weight: 600; margin: 0;">{event.name}</p>
          <p style="font-size: 0.875rem; color: #666; margin: 0;">{event.location}</p>
          
          <p style="margin: 0.25rem 0;">
            {#if event.owner_id === get(currentUser)?.user_id}
              <span class="tag owner">Właściciel</span>
            {:else if event.participation_status === "going"}
              <span class="tag going">Będę</span>
            {:else if event.participation_status === "maybe"}
              <span class="tag maybe">Może będę</span>
            {:else if new Date(event.time) < now}
              <span class="tag past">Już było</span>
            {/if}
          </p>

          {#if new Date(event.time) >= now}
            <p style="font-size: 0.75rem; color:#888; margin: 0;">{daysUntilEvent(event)}</p>
          {/if}

          <p style="font-size: 0.75rem; color:#888; margin: 0;">
            {new Date(event.time).toLocaleDateString()} {new Date(event.time).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
          </p>
        </div>

        <button 
          on:click={() => goToEvent(event.id)}
          style="padding: 0.5rem 0.75rem; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          Zobacz szczegóły
        </button>
      </div>
    {/each}
  {/if}
</div>
