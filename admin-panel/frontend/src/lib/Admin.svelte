<script>
    import { onMount } from 'svelte';
    import { api } from './api.js';
    import { authStore } from '../stores/auth.js';
    import UserManagement from './UserManagement.svelte';
    import LLMSettings from './LLMSettings.svelte';

    export let onLogout = () => {};

    let user = null;
    let loading = true;
    let activeTab = 'users'; // 'users' or 'llm-settings'

    console.log('🔵 Admin.svelte script executed');

    onMount(async () => {
        console.log('🟢 Admin.svelte onMount called');
        try {
            user = await api.getMe();
            console.log('👤 Admin user fetched:', user);
            loading = false;
        } catch (error) {
            console.error('❌ Auth failed in Admin:', error);
            onLogout();
        }
    });

    function switchTab(tab) {
        activeTab = tab;
    }
</script>

{#if loading}
    <div class="loading">در حال بارگذاری...</div>
{:else}
    <div class="admin-container">
        <header>
            <h1>پنل مدیریت</h1>
            <div class="user-info">
                <span>خوش آمدید، {user.full_name}</span>
                <button on:click={onLogout} class="logout-btn">خروج</button>
            </div>
        </header>

        <div class="tabs-container">
            <button 
                class="tab-btn" 
                class:active={activeTab === 'users'}
                on:click={() => switchTab('users')}
            >
                👥 مدیریت کاربران
            </button>
            <button 
                class="tab-btn" 
                class:active={activeTab === 'llm-settings'}
                on:click={() => switchTab('llm-settings')}
            >
                ⚙️ تنظیمات LLM
            </button>
        </div>

        <div class="tab-content">
            {#if activeTab === 'users'}
                {#key user}
                    <UserManagement />
                {/key}
            {:else if activeTab === 'llm-settings'}
                <LLMSettings />
            {/if}
        </div>
    </div>
{/if}

<style>
    .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        font-size: 1.5rem;
        direction: rtl;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    }

    .admin-container {
        min-height: 100vh;
        background: #f5f7fa;
        direction: rtl;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    }

    header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    h1 {
        margin: 0;
        font-size: 1.8rem;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .logout-btn {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 1px solid white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.3s;
        font-family: inherit;
        font-size: 0.95rem;
    }

    .logout-btn:hover {
        background: white;
        color: #667eea;
    }

    .tabs-container {
        background: white;
        padding: 0 2rem;
        display: flex;
        gap: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-bottom: 2px solid #e5e7eb;
    }

    .tab-btn {
        background: none;
        border: none;
        padding: 1rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        color: #6b7280;
        cursor: pointer;
        transition: all 0.3s;
        border-bottom: 3px solid transparent;
        font-family: inherit;
        position: relative;
        top: 2px;
    }

    .tab-btn:hover {
        color: #667eea;
        background: #f9fafb;
    }

    .tab-btn.active {
        color: #667eea;
        border-bottom-color: #667eea;
    }

    .tab-content {
        padding: 0 1rem;
    }
</style>
