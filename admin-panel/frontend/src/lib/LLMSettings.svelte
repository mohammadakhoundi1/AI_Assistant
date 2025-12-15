<script>
    import { onMount } from 'svelte';
    import { api } from './api.js';

    let loading = true;
    let saving = false;
    let fetchingModels = false;
    let settings = {
        api_key: '',
        base_url: 'https://api.anthropic.com',
        model_name: 'claude-sonnet-4.5'
    };
    let originalApiKey = '';
    let message = { text: '', type: '' };
    let availableModels = [];
    let useCustomModel = false;
    let customModelName = '';

    onMount(async () => {
        try {
            const loadedSettings = await api.getLLMSettings();
            settings = { ...loadedSettings };
            originalApiKey = loadedSettings.api_key;
            loading = false;
        } catch (error) {
            console.error('❌ Failed to load LLM settings:', error);
            message = { text: 'خطا در بارگذاری تنظیمات', type: 'error' };
            loading = false;
        }
    });

    async function fetchModels() {
        const apiKeyToUse = settings.api_key === originalApiKey 
            ? originalApiKey 
            : settings.api_key;

        if (!settings.base_url.trim()) {
            message = { text: 'لطفاً ابتدا Base URL را وارد کنید', type: 'error' };
            return;
        }

        if (!apiKeyToUse.trim()) {
            message = { text: 'لطفاً ابتدا API Key را وارد کنید', type: 'error' };
            return;
        }

        fetchingModels = true;
        message = { text: '', type: '' };

        try {
            const response = await api.fetchModels(settings.base_url, apiKeyToUse);
            availableModels = response.models || [];
            
            if (availableModels.length === 0) {
                message = { text: '⚠️ هیچ مدلی یافت نشد', type: 'error' };
            } else {
                message = { text: `✅ ${availableModels.length} مدل یافت شد`, type: 'success' };
            }
        } catch (error) {
            console.error('❌ Failed to fetch models:', error);
            message = { text: 'خطا در دریافت لیست مدل‌ها. لطفاً Base URL و API Key را بررسی کنید.', type: 'error' };
            availableModels = [];
        } finally {
            fetchingModels = false;
        }
    }

    async function handleSave() {
        const finalModelName = useCustomModel ? customModelName : settings.model_name;
        const apiKeyToSave = settings.api_key === originalApiKey 
            ? originalApiKey 
            : settings.api_key;

        if (!apiKeyToSave.trim()) {
            message = { text: 'لطفاً API Key را وارد کنید', type: 'error' };
            return;
        }

        if (!settings.base_url.trim()) {
            message = { text: 'لطفاً Base URL را وارد کنید', type: 'error' };
            return;
        }

        if (!finalModelName.trim()) {
            message = { text: 'لطفاً نام مدل را وارد کنید', type: 'error' };
            return;
        }

        saving = true;
        message = { text: '', type: '' };

        try {
            await api.updateLLMSettings({
                api_key: apiKeyToSave,
                base_url: settings.base_url,
                model_name: finalModelName
            });
            message = { text: '✅ تنظیمات با موفقیت ذخیره شد', type: 'success' };
            originalApiKey = apiKeyToSave;
        } catch (error) {
            console.error('❌ Failed to save settings:', error);
            message = { text: 'خطا در ذخیره‌سازی تنظیمات', type: 'error' };
        } finally {
            saving = false;
        }
    }
</script>

{#if loading}
    <div class="loading-container">
        <div class="spinner"></div>
        <p>در حال بارگذاری تنظیمات...</p>
    </div>
{:else}
    <div class="llm-settings">
        <div class="settings-header">
            <h2>⚙️ تنظیمات سرویس هوش مصنوعی (LLM)</h2>
            <p class="subtitle">پیکربندی API و انتخاب مدل برای چت</p>
        </div>

        {#if message.text}
            <div class="message {message.type}">
                {message.text}
            </div>
        {/if}

        <form on:submit|preventDefault={handleSave}>
            <div class="form-group">
                <label for="api-key">
                    🔑 API Key
                    <span class="required">*</span>
                </label>
                <input
                    id="api-key"
                    type="password"
                    bind:value={settings.api_key}
                    placeholder="sk-ant-xxxxx یا OpenRouter Key"
                    required
                />
                <small class="help-text">
                    کلید API برای احراز هویت با سرویس LLM
                </small>
            </div>

            <div class="form-group">
                <label for="base-url">
                    🌐 Base URL
                    <span class="required">*</span>
                </label>
                <div class="input-with-button">
                    <input
                        id="base-url"
                        type="url"
                        bind:value={settings.base_url}
                        placeholder="https://api.anthropic.com"
                        required
                    />
                    <button
                        type="button"
                        class="fetch-models-btn"
                        on:click={fetchModels}
                        disabled={fetchingModels}
                    >
                        {#if fetchingModels}
                            <span class="spinner-small"></span>
                        {:else}
                            🔄
                        {/if}
                        بارگذاری مدل‌ها
                    </button>
                </div>
                <small class="help-text">
                    آدرس پایه API (مثلاً: https://openrouter.ai/api/v1)
                </small>
            </div>

            <div class="form-group">
                <label for="model-name">
                    🤖 Model Name
                    <span class="required">*</span>
                </label>
                
                <div class="model-selector">
                    <label class="radio-option">
                        <input
                            type="radio"
                            bind:group={useCustomModel}
                            value={false}
                        />
                        <span>انتخاب از لیست</span>
                    </label>
                    
                    <label class="radio-option">
                        <input
                            type="radio"
                            bind:group={useCustomModel}
                            value={true}
                        />
                        <span>وارد کردن دستی</span>
                    </label>
                </div>

                {#if !useCustomModel}
                    <select
                        id="model-name"
                        bind:value={settings.model_name}
                        disabled={availableModels.length === 0}
                        required
                    >
                        {#if availableModels.length === 0}
                            <option value="">ابتدا مدل‌ها را بارگذاری کنید</option>
                        {:else}
                            {#each availableModels as model}
                                <option value={model.id}>
                                    {model.name}
                                </option>
                            {/each}
                        {/if}
                    </select>
                {:else}
                    <input
                        type="text"
                        bind:value={customModelName}
                        placeholder="claude-sonnet-4.5"
                        required
                    />
                {/if}
                
                <small class="help-text">
                    نام مدل مورد استفاده برای تولید پاسخ‌ها
                </small>
            </div>

            <div class="form-actions">
                <button
                    type="submit"
                    class="save-btn"
                    disabled={saving}
                >
                    {#if saving}
                        <span class="spinner-small"></span>
                        در حال ذخیره...
                    {:else}
                        💾 ذخیره تنظیمات
                    {/if}
                </button>
            </div>
        </form>

        <div class="info-box">
            <h3>📝 راهنما</h3>
            <ul>
                <li>برای استفاده از Anthropic: Base URL را به <code>https://api.anthropic.com</code> تنظیم کنید</li>
                <li>برای استفاده از OpenRouter: Base URL را به <code>https://openrouter.ai/api/v1</code> تنظیم کنید</li>
                <li>پس از وارد کردن Base URL و API Key، دکمه "🔄 بارگذاری مدل‌ها" را بزنید</li>
                <li>می‌توانید مدل را از لیست انتخاب کنید یا به صورت دستی وارد نمایید</li>
            </ul>
        </div>
    </div>
{/if}

<style>
    .llm-settings {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
        direction: rtl;
    }

    .settings-header {
        margin-bottom: 2rem;
        text-align: center;
    }

    .settings-header h2 {
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        color: #7f8c8d;
        font-size: 0.95rem;
    }

    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 400px;
        gap: 1rem;
    }

    .spinner {
        width: 50px;
        height: 50px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    .spinner-small {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-left: 0.5rem;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .message {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .message.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .message.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    form {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .form-group {
        margin-bottom: 1.5rem;
    }

    label {
        display: block;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }

    .required {
        color: #e74c3c;
    }

    input[type="text"],
    input[type="url"],
    input[type="password"],
    select {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 1rem;
        transition: border-color 0.3s;
    }

    input:focus,
    select:focus {
        outline: none;
        border-color: #3498db;
    }

    .input-with-button {
        display: flex;
        gap: 0.5rem;
    }

    .input-with-button input {
        flex: 1;
    }

    .fetch-models-btn {
        padding: 0.75rem 1rem;
        background-color: #2ecc71;
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: background-color 0.3s;
    }

    .fetch-models-btn:hover:not(:disabled) {
        background-color: #27ae60;
    }

    .fetch-models-btn:disabled {
        background-color: #95a5a6;
        cursor: not-allowed;
    }

    .model-selector {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1rem;
    }

    .radio-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        font-weight: normal;
    }

    .radio-option input[type="radio"] {
        width: auto;
        cursor: pointer;
    }

    .help-text {
        display: block;
        color: #7f8c8d;
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }

    .form-actions {
        margin-top: 2rem;
        display: flex;
        justify-content: center;
    }

    .save-btn {
        padding: 0.875rem 2rem;
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.3s;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .save-btn:hover:not(:disabled) {
        background-color: #2980b9;
    }

    .save-btn:disabled {
        background-color: #95a5a6;
        cursor: not-allowed;
    }

    .info-box {
        margin-top: 2rem;
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-right: 4px solid #3498db;
    }

    .info-box h3 {
        color: #2c3e50;
        margin-bottom: 1rem;
    }

    .info-box ul {
        margin: 0;
        padding-right: 1.5rem;
    }

    .info-box li {
        margin-bottom: 0.5rem;
        color: #555;
        line-height: 1.6;
    }

    .info-box code {
        background-color: #e8e8e8;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }

    @media (max-width: 768px) {
        .llm-settings {
            padding: 1rem;
        }

        form {
            padding: 1.5rem;
        }

        .input-with-button {
            flex-direction: column;
        }

        .fetch-models-btn {
            width: 100%;
            justify-content: center;
        }

        .model-selector {
            flex-direction: column;
            gap: 0.75rem;
        }
    }
</style>
