<script lang="ts">
  export let events: { id: number; title: string; date: string }[] = [];
</script>

<ul>
  {#each events as event}
    <li>
      <strong>{event.title}</strong> - {event.date}
    </li>
  {/each}
</ul>
