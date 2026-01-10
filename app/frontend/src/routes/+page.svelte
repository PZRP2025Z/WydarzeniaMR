<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { currentUser } from '$lib/stores/currentUser';
  import { get } from 'svelte/store';
  import EventCard from '$lib/components/EventCard.svelte';

  interface EventItem {
    id: number;
    name: string;
    location: string;
    time: string;
    owner_id: number;
    participation_status?: 'going' | 'maybe' | 'not_going' | null;
  }

  let events: EventItem[] = [];
  let loading = true;
  let error = '';
  let now = new Date();

  async function fetchMyEvents() {
    const user = get(currentUser);
    if (!user) {
      loading = false;
      return;
    }

    try {
      const res = await fetch(`/api/participations/me/events`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Nie udało się pobrać Twoich wydarzeń');

      const data: EventItem[] = await res.json();
      const nowDate = new Date();

      const future = data.filter(e => new Date(e.time) >= nowDate);
      const past = data.filter(e => new Date(e.time) < nowDate);

      future.sort((a, b) => +new Date(a.time) - +new Date(b.time));
      past.sort((a, b) => +new Date(a.time) - +new Date(b.time));

      events = [...future, ...past];
      now = nowDate;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Błąd przy pobieraniu wydarzeń';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    const unsubscribe = currentUser.subscribe(user => {
      if (user) fetchMyEvents();
      else loading = false;
    });
    return unsubscribe;
  });

  function goToEvent(id: number) {
    goto(`/events/${id}`);
  }

  function daysUntilEvent(event: EventItem) {
    const diff = Math.ceil(
      (new Date(event.time).getTime() - now.getTime()) / 86400000
    );
    if (diff === 0) return 'Dzisiaj';
    if (diff > 0) return `Za ${diff} dni`;
    return null;
  }
</script>

<div class="max-w-xl mx-auto mt-8 p-6 flex flex-col gap-4">
  <h2 class="text-xl font-semibold">Moje wydarzenia</h2>

  {#if loading}
    {#each Array(3) as _}
      <div class="bg-surface-100 border border-surface-300 rounded-lg p-4 animate-pulse">
        <div class="h-4 w-2/3 bg-surface-300 rounded mb-2"></div>
        <div class="h-3 w-1/3 bg-surface-300 rounded"></div>
      </div>
    {/each}

  {:else if error}
    <div class="bg-surface-100 border border-error-300 text-error-700 p-4 rounded">
      {error}
    </div>

  {:else if events.length === 0}
    <p class="text-surface-600">Nie masz jeszcze żadnych wydarzeń</p>

  {:else}
    {#each events as event, i (event.id)}
      {#if i > 0 && new Date(events[i - 1].time) < now && new Date(event.time) >= now}
        <hr class="my-4 border-surface-300" />
      {/if}

      <EventCard onClick={() => goToEvent(event.id)}>
        <p class="font-semibold">{event.name}</p>
        <p class="text-sm text-surface-600">{event.location}</p>

        <div class="flex flex-wrap gap-2 mt-1">
          {#if event.owner_id === get(currentUser)?.user_id}
            <span class="px-2 py-0.5 text-xs rounded text-white" style="background:#007BFF">
              Właściciel
            </span>
          {:else if event.participation_status === 'going'}
            <span class="px-2 py-0.5 text-xs rounded text-white" style="background:#28a745">
              Będę
            </span>
          {:else if event.participation_status === 'maybe'}
            <span class="px-2 py-0.5 text-xs rounded text-black" style="background:#ffc107">
              Może
            </span>
          {:else if new Date(event.time) < now}
            <span class="px-2 py-0.5 text-xs rounded text-white" style="background:#6c757d">
              Już było
            </span>
          {/if}
        </div>

        {#if new Date(event.time) >= now}
          <p class="text-xs text-surface-500 mt-1">
            {daysUntilEvent(event)}
          </p>
        {/if}

        <p class="text-xs text-surface-500">
          {new Date(event.time).toLocaleDateString()}
          {new Date(event.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </EventCard>
    {/each}
  {/if}
</div>
