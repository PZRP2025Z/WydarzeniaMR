<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';

  interface Event {
    id: number;
    name: string;
    location: string;
    time: string;
    description?: string;
    photo?: string | null;
  }

  let event: Event | null = null;
  let formData = {
    name: '',
    location: '',
    time: '',
    description: '',
    photo: null as string | null
  };
  let loading = true;
  let error = '';

  const API_URL = '/api/events';

  onMount(async () => {
    const id = Number($page.params.id);
    try {
      const res = await fetch(`${API_URL}/${id}`, { credentials: 'include' });
      if (!res.ok) throw new Error(t('error_loading_event', $lang));
      const data: Event = await res.json();
      event = data;

      formData = {
        ...data,
        time: data.time ? data.time.slice(0, 16) : '',
        photo: data.photo || null
      };
    } catch (err) {
      error = err instanceof Error ? err.message : t('error_loading', $lang);
    } finally {
      loading = false;
    }
  });

  function handleFileSelect(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      formData.photo = (reader.result as string).split(',')[1];
    };
    reader.readAsDataURL(file);
  }

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
        error = data.detail || t('error_update_event', $lang);
        return;
      }

      const updated = await res.json();
      goto(`/events/${updated.id}`);
    } catch (err) {
      error = t('server_error', $lang);
    }
  }
</script>

<div class="max-w-xl mx-auto mt-10 px-4">
  <div class="card p-6 space-y-4 bg-surface">

    {#if loading}
      <p class="text-surface-500">{t('loading', $lang)}</p>
    {:else if error}
      <div class="bg-error-100 text-error-700 p-3 rounded">
        {error}
      </div>
    {:else if event}

      <h1 class="text-2xl font-semibold">
        {t('edit_event', $lang)}
      </h1>

      <div class="space-y-3">
        <input
          class="input"
          placeholder={t('title', $lang)}
          bind:value={formData.name}
        />

        <input
          class="input"
          placeholder={t('event_location', $lang)}
          bind:value={formData.location}
        />

        <input
          class="input"
          type="datetime-local"
          bind:value={formData.time}
        />

        <textarea
          class="textarea"
          placeholder={t('description', $lang)}
          rows="4"
          bind:value={formData.description}
        ></textarea>

        <div class="space-y-1">
          <input
            id="photo-upload"
            type="file"
            accept="image/*"
            class="hidden"
            on:change={handleFileSelect}
          />

          <label
            for="photo-upload"
            class="btn btn-outline w-full flex justify-center items-center gap-2 cursor-pointer"
          >
            {#if formData.photo}
              {t('change_photo', $lang)}
            {:else}
              {t('choose_photo', $lang)}
            {/if}
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm6 3l2 3h-4l2-3z" />
            </svg>
          </label>

          {#if formData.photo}
            <p class="text-sm text-surface-500">{t('file_selected', $lang)}</p>
          {/if}
        </div>
      </div>

      <button
        on:click={updateEvent}
        class="btn btn-primary w-full font-semibold"
      >
        {t('save_changes', $lang)}
      </button>

    {/if}
  </div>
</div>
