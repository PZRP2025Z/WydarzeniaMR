import { writable } from 'svelte/store';

export const currentUser = writable<{ 
    user_id: number; 
    login?: string; 
    email?: string 
} | null>(null);
