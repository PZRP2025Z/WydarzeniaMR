<script lang="ts">
    import { t } from '$lib/i18n';
    import { lang } from '$lib/stores/stores';
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { page } from "$app/stores";

    interface Event {
        id: number;
        name: string;
        location: string;
    }

    let event: Event | null = null;
    let formData = { name: "", location: "" };
    let isEditing = false;
    let loading = true;
    let error = "";

    const API_URL = "http://127.0.0.1:8000/events";

    $: e = event as Event | null;

    onMount(async () => {
        const id = Number($page.params.id);
        try {
            const res = await fetch(`${API_URL}/${id}`);
            if (!res.ok) throw new Error("Event not found.");
            const data: Event = await res.json();
            event = data;
            formData = { name: data.name, location: data.location };
        } catch (err) {
            error = err instanceof Error ? err.message : "Loading error";
        } finally {
            loading = false;
        }
    });

    async function updateEvent() {
        if (!event) return;

        const res = await fetch(`${API_URL}/${event.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        if (!res.ok) {
            error = "Couldn't update event";
            return;
        }

        event = { ...event, ...formData };
        isEditing = false;
    }

    async function deleteEvent() {
        if (!event) return;
        if (!confirm(t('remove_event_confirm', $lang))) return;

        const res = await fetch(`${API_URL}/${event.id}`, { method: "DELETE" });

        if (res.ok) goto("/events");
        else error = "Couldn't delete event";
    }
</script>

<div class="container">
    {#if loading}
        <p style="text-align:center; color: #666;">{t('event_loading', $lang)}</p>

    {:else if error}
        <div style="background:#ffe5e5; border:1px solid #ff9999; color:#900; padding:12px; border-radius:6px;">
            {error}
        </div>

    {:else if e}
        <div style="background:#fff; padding:16px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">

            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <h1 style="font-size:1.5rem; font-weight:bold; margin:0;">{e.name}</h1>
                <button style="background:none; border:none; font-size:1.25rem; cursor:pointer;" on:click={() => goto(`/events/${e.id}`)}>
                    ✕
                </button>
            </div>

            {#if isEditing}
                <form on:submit|preventDefault={updateEvent} style="display:flex; flex-direction:column; gap:12px;">
                    <div style="display:flex; flex-direction:column;">
                        <label for="name" style="margin-bottom:4px; font-weight:600;">{t('event_title', $lang)}</label>
                        <input id="name" type="text" bind:value={formData.name} style="padding:8px; border:1px solid #ccc; border-radius:4px;"/>
                    </div>

                    <div style="display:flex; flex-direction:column;">
                        <label for="location" style="margin-bottom:4px; font-weight:600;">{t('event_location', $lang)}</label>
                        <input id="location" type="text" bind:value={formData.location} style="padding:8px; border:1px solid #ccc; border-radius:4px;"/>
                    </div>

                    <div style="display:flex; gap:8px; margin-top:8px;">
                        <button type="submit" style="background:#007BFF; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">
                            Zapisz
                        </button>
                        <button type="button" on:click={() => isEditing=false} style="background:#888; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">
                            {t('cancel', $lang)}
                        </button>
                    </div>
                </form>

            {:else}
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <div>
                        <h2 style="margin:0 0 4px 0; font-weight:100; color:#555; ; font-size:0.9rem;">{t('event_location', $lang)}</h2>
                        <p style="margin:0; color:#333;">{e.location}</p>
                    </div>

                    <div style="display:flex; gap:8px;">
                        <button on:click={() => isEditing=true} style="background:#007BFF; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">
                            {t('edit_event', $lang)}
                        </button>
                        <button on:click={deleteEvent} style="background:#d9534f; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">
                            {t('remove_event', $lang)}
                        </button>
                    </div>
                </div>
            {/if}

        </div>

    {:else}
        <p style="text-align:center; color:#666;">{t('no_events', $lang)}</p>
    {/if}
</div>

<style>
    .container {
        max-width:600px;
        margin:2rem auto;
        padding:16px;
        font-family: system-ui, sans-serif;
    }
</style>
