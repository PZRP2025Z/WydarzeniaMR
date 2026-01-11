<script lang="ts">
  import { goto } from '$app/navigation';
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';

  let newEvent = { name: '', location: '', time: '', description: '', photo: null as string | null };
  let loading = false;
  let error = '';

  function handleFileSelect(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      newEvent.photo = (reader.result as string).split(',')[1];
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
        error = data.detail || t('error_add_event', $lang);
        return;
      }

      const createdEvent = await res.json();
      goto(`/events/${createdEvent.id}`);
    } catch (err) {
      error = t('server_error', $lang);
    } finally {
      loading = false;
    }
  }
</script>

<div class="max-w-xl mx-auto mt-10 px-4">
  <div class="card p-6 space-y-4 bg-surface">

    <h1 class="text-2xl font-semibold">
      {t('add_new_event', $lang)}
    </h1>

    {#if error}
      <div class="bg-error-100 text-error-700 p-3 rounded">
        {error}
      </div>
    {/if}

    <div class="space-y-3">
      <input
        class="input"
        placeholder={t('title', $lang)}
        bind:value={newEvent.name}
      />

      <input
        class="input"
        placeholder={t('event_location', $lang)}
        bind:value={newEvent.location}
      />

      <input
        class="input"
        type="datetime-local"
        bind:value={newEvent.time}
      />

      <textarea
        class="textarea"
        placeholder={t('description', $lang)}
        rows="4"
        bind:value={newEvent.description}
      ></textarea>

      <div class="space-y-1">
        <input
          id="photo-upload"
          type="file"
          accept="image/*"
          class="hidden"
          on:change={handleFileSelect}
        />
        <label for="photo-upload" class="btn btn-outline w-full flex justify-center items-center gap-2 cursor-pointer">
          {#if newEvent.photo}
            {t('change_photo', $lang)}
          {:else}
            {t('choose_photo', $lang)}
          {/if}
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm6 3l2 3h-4l2-3z" />
          </svg>
        </label>
        {#if newEvent.photo}
          <p class="text-sm text-surface-500">{t('file_selected', $lang)}</p>
        {/if}
      </div>
    </div>

    <button
      on:click={addEvent}
      disabled={loading}
      class="btn btn-primary w-full font-semibold"
    >
      {loading ? t('adding_event', $lang) : t('add_event', $lang)}
    </button>

  </div>
</div>
