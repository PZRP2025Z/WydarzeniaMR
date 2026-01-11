<script lang="ts">
  import { t } from '$lib/i18n';
  import { lang } from '$lib/stores/stores';
  export let onClick: () => void;
</script>

<div class="
    bg-surface-50 dark:bg-surface-900 
    border border-surface-300 
    rounded-lg p-4 shadow-sm
    flex justify-between items-center
    transition
    hover:bg-surface-100
    dark:hover:bg-surface-800
">
  <div class="flex flex-col gap-1">
    <slot />
  </div>

  <button
    on:click={onClick}
    class="btn-primary px-3 py-2 rounded text-sm"
  >
    {t('event_details', $lang)}
  </button>
</div>
