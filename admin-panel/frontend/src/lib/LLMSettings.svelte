<script>
    import { onMount } from 'svelte';
    import { api } from './api.js';

    // ==================== STATE MANAGEMENT ====================
    let state = {
        loading: true,
        saving: false,
        fetchingModels: false
    };

    let settings = {
        api_key: '',
        base_url: 'https://api.anthropic.com',
        model_name: 'claude-sonnet-4.5'
    };

    let originalApiKey = '';
    let availableModels = [];
    let modelInputMode = 'select'; // 'select' or 'custom'
    let customModelName = '';
    
    let notification = {
        visible: false,
        message: '',
        type: '' // 'success' or 'error'
    };

    // ==================== COMPUTED VALUES ====================
    $: canFetchModels = settings.base_url.trim() && getCurrentApiKey().trim();
    $: hasModels = availableModels.length > 0;
    $: finalModelName = modelInputMode === 'custom' ? customModelName : settings.model_name;
    $: canSave = getCurrentApiKey().trim() && settings.base_url.trim() && finalModelName.trim();

    // ==================== HELPER FUNCTIONS ====================
    function getCurrentApiKey() {
        return settings.api_key === originalApiKey ? originalApiKey : settings.api_key;
    }

    function showNotification(message, type = 'success') {
        notification = { visible: true, message, type };
        setTimeout(() => {
            notification.visible = false;
        }, 4000);
    }

    function validateSettings() {
        if (!getCurrentApiKey().trim()) {
            throw new Error('لطفاً API Key را وارد کنید');
        }
        if (!settings.base_url.trim()) {
            throw new Error('لطفاً Base URL را وارد کنید');
        }
        if (!finalModelName.trim()) {
            throw new Error('لطفاً نام مدل را وارد کنید');
        }
    }

    // ==================== API CALLS ====================
    async function loadSettings() {
        try {
            state.loading = true;
            const loadedSettings = await api.getLLMSettings();
            settings = { ...loadedSettings };
            originalApiKey = loadedSettings.api_key;
        } catch (error) {
            console.error('❌ Failed to load settings:', error);
            showNotification('خطا در بارگذاری تنظیمات', 'error');
        } finally {
            state.loading = false;
        }
    }

    async function fetchModels() {
        if (!canFetchModels) {
            showNotification('لطفاً ابتدا Base URL و API Key را وارد کنید', 'error');
            return;
        }

        try {
            state.fetchingModels = true;
            const response = await api.fetchModels(settings.base_url, getCurrentApiKey());
            availableModels = response.models || [];
            
            if (availableModels.length === 0) {
                showNotification('⚠️ هیچ مدلی یافت نشد', 'error');
            } else {
                showNotification(`✅ ${availableModels.length} مدل یافت شد`, 'success');
                // اگر مدلی انتخاب نشده، اولین مدل را انتخاب کن
                if (!settings.model_name && availableModels.length > 0) {
                    settings.model_name = availableModels[0].model_id;
                }
            }
        } catch (error) {
            console.error('❌ Failed to fetch models:', error);
            showNotification('خطا در دریافت لیست مدل‌ها. Base URL و API Key را بررسی کنید.', 'error');
            availableModels = [];
        } finally {
            state.fetchingModels = false;
        }
    }

    async function saveSettings() {
        try {
            validateSettings();
            state.saving = true;

            await api.updateLLMSettings({
                api_key: getCurrentApiKey(),
                base_url: settings.base_url,
                model_name: finalModelName
            });

            originalApiKey = getCurrentApiKey();
            settings.model_name = finalModelName; // به‌روزرسانی مدل در state
            showNotification('✅ تنظیمات با موفقیت ذخیره شد', 'success');
        } catch (error) {
            console.error('❌ Failed to save settings:', error);
            showNotification(error.message || 'خطا در ذخیره‌سازی تنظیمات', 'error');
        } finally {
            state.saving = false;
        }
    }

    // ==================== EVENT HANDLERS ====================
    function handleModeChange(mode) {
        modelInputMode = mode;
        if (mode === 'select' && !hasModels) {
            showNotification('ابتدا مدل‌ها را بارگذاری کنید', 'error');
        }
    }

    // ==================== LIFECYCLE ====================
    onMount(loadSettings);
</script>

<!-- ==================== TEMPLATE ==================== -->
<div class="container">
    {#if state.loading}
        <div class="loading-state">
            <div class="spinner"></div>
            <p>در حال بارگذاری تنظیمات...</p>
        </div>
    {:else}
        <div class="settings-panel">
            <!-- Header -->
            <header class="panel-header">
                <h2>⚙️ تنظیمات سرویس هوش مصنوعی (LLM)</h2>
                <p class="subtitle">پیکربندی API و انتخاب مدل برای چت</p>
            </header>

            <!-- Notification -->
            {#if notification.visible}
                <div class="notification {notification.type}" role="alert">
                    {notification.message}
                </div>
            {/if}

            <!-- Form -->
            <form on:submit|preventDefault={saveSettings} class="settings-form">
                <!-- API Key -->
                <div class="field">
                    <label for="api-key" class="field-label">
                        🔑 API Key
                        <span class="required">*</span>
                    </label>
                    <input
                        id="api-key"
                        type="password"
                        bind:value={settings.api_key}
                        placeholder="sk-ant-xxxxx یا OpenRouter Key"
                        class="field-input"
                        required
                    />
                    <small class="field-hint">
                        کلید API برای احراز هویت با سرویس LLM
                    </small>
                </div>

                <!-- Base URL + Fetch Button -->
                <div class="field">
                    <label for="base-url" class="field-label">
                        🌐 Base URL
                        <span class="required">*</span>
                    </label>
                    <div class="field-group">
                        <input
                            id="base-url"
                            type="url"
                            bind:value={settings.base_url}
                            placeholder="https://api.anthropic.com"
                            class="field-input"
                            required
                        />
                        <button
                            type="button"
                            class="btn btn-secondary"
                            on:click={fetchModels}
                            disabled={state.fetchingModels || !canFetchModels}
                        >
                            {#if state.fetchingModels}
                                <span class="spinner-sm"></span>
                            {:else}
                                🔄
                            {/if}
                            بارگذاری مدل‌ها
                        </button>
                    </div>
                    <small class="field-hint">
                        آدرس پایه API (مثلاً: https://openrouter.ai/api/v1)
                    </small>
                </div>

                <!-- Model Selection Mode -->
                <div class="field">
                    <label class="field-label">
                        🤖 Model Name
                        <span class="required">*</span>
                    </label>
                    
                    <div class="mode-selector">
                        <label class="mode-option">
                            <input
                                type="radio"
                                name="model-mode"
                                checked={modelInputMode === 'select'}
                                on:change={() => handleModeChange('select')}
                            />
                            <span>انتخاب از لیست</span>
                        </label>
                        
                        <label class="mode-option">
                            <input
                                type="radio"
                                name="model-mode"
                                checked={modelInputMode === 'custom'}
                                on:change={() => handleModeChange('custom')}
                            />
                            <span>وارد کردن دستی</span>
                        </label>
                    </div>

                    <!-- Model Input Based on Mode -->
                    <div class="model-input-wrapper">
                        {#if modelInputMode === 'select'}
                            <select
                                bind:value={settings.model_name}
                                disabled={!hasModels}
                                class="field-input"
                                required
                            >
                                {#if !hasModels}
                                    <option value="">ابتدا مدل‌ها را بارگذاری کنید</option>
                                {:else}
                                    <option value="">-- انتخاب مدل --</option>
                                    {#each availableModels as model (model.model_id)}
                                        <option value={model.model_id}>
                                            {model.model_name}
                                        </option>
                                    {/each}
                                {/if}
                            </select>
                        {:else}
                            <input
                                type="text"
                                bind:value={customModelName}
                                placeholder="claude-sonnet-4.5"
                                class="field-input"
                                required
                            />
                        {/if}
                    </div>
                    
                    <small class="field-hint">
                        نام مدل مورد استفاده برای تولید پاسخ‌ها
                    </small>
                </div>

                <!-- Submit Button -->
                <div class="form-actions">
                    <button
                        type="submit"
                        class="btn btn-primary"
                        disabled={state.saving || !canSave}
                    >
                        {#if state.saving}
                            <span class="spinner-sm"></span>
                            در حال ذخیره...
                        {:else}
                            💾 ذخیره تنظیمات
                        {/if}
                    </button>
                </div>
            </form>

            <!-- Help Box -->
            <aside class="help-box">
                <h3>📝 راهنما</h3>
                <ul>
                    <li>برای استفاده از Anthropic: <code>https://api.anthropic.com</code></li>
                    <li>برای استفاده از OpenRouter: <code>https://openrouter.ai/api/v1</code></li>
                    <li>پس از وارد کردن اطلاعات، دکمه "🔄 بارگذاری مدل‌ها" را بزنید</li>
                    <li>می‌توانید مدل را از لیست انتخاب کنید یا دستی وارد کنید</li>
                </ul>
            </aside>
        </div>
    {/if}
</div>

<!-- ==================== STYLES ==================== -->
<style>
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem;
        direction: rtl;
        min-height: 100vh;
    }

    /* ===== Loading State ===== */
    .loading-state {
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

    .spinner-sm {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid currentColor;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ===== Panel ===== */
    .settings-panel {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        overflow: hidden;
    }

    .panel-header {
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    .panel-header h2 {
        margin: 0 0 0.5rem 0;
        font-size: 1.75rem;
    }

    .subtitle {
        margin: 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }

    /* ===== Notification ===== */
    .notification {
        margin: 1.5rem;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
    }

    .notification.success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .notification.error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    /* ===== Form ===== */
    .settings-form {
        padding: 2rem;
    }

    .field {
        margin-bottom: 1.75rem;
    }

    .field-label {
        display: block;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }

    .required {
        color: #e74c3c;
        margin-right: 0.25rem;
    }

    .field-input {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 2px solid #e1e8ed;
        border-radius: 8px;
        font-size: 1rem;
        transition: all 0.2s;
        box-sizing: border-box;
    }

    .field-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .field-input:disabled {
        background: #f8f9fa;
        cursor: not-allowed;
        opacity: 0.6;
    }

    .field-group {
        display: flex;
        gap: 0.75rem;
        align-items: stretch;
    }

    .field-group .field-input {
        flex: 1;
    }

    .field-hint {
        display: block;
        margin-top: 0.5rem;
        color: #6c757d;
        font-size: 0.85rem;
    }

    /* ===== Mode Selector ===== */
    .mode-selector {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1rem;
        padding: 0.75rem;
        background: #f8f9fa;
        border-radius: 8px;
    }

    .mode-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        font-weight: normal;
        color: #495057;
        transition: color 0.2s;
    }

    .mode-option:hover {
        color: #667eea;
    }

    .mode-option input[type="radio"] {
        cursor: pointer;
        width: auto;
    }

    .model-input-wrapper {
        margin-top: 0.5rem;
        min-height: 48px;
    }

    /* ===== Buttons ===== */
    .btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        justify-content: center;
        white-space: nowrap;
    }

    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }

    .btn-secondary {
        background: #2ecc71;
        color: white;
    }

    .btn-secondary:hover:not(:disabled) {
        background: #27ae60;
    }

    .form-actions {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e1e8ed;
    }

    .form-actions .btn {
        width: 100%;
    }

    /* ===== Help Box ===== */
    .help-box {
        margin: 1.5rem;
        padding: 1.5rem;
        background: #f8f9fa;
        border-radius: 8px;
        border-right: 4px solid #667eea;
    }

    .help-box h3 {
        margin: 0 0 1rem 0;
        color: #2c3e50;
        font-size: 1.1rem;
    }

    .help-box ul {
        margin: 0;
        padding-right: 1.5rem;
    }

    .help-box li {
        margin-bottom: 0.75rem;
        color: #495057;
        line-height: 1.6;
    }

    .help-box code {
        background: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.875rem;
        color: #667eea;
        border: 1px solid #e1e8ed;
    }

    /* ===== Responsive ===== */
    @media (max-width: 768px) {
        .container {
            padding: 1rem 0.5rem;
        }

        .settings-form {
            padding: 1.5rem;
        }

        .panel-header {
            padding: 1.5rem;
        }

        .panel-header h2 {
            font-size: 1.5rem;
        }

        .field-group {
            flex-direction: column;
        }

        .mode-selector {
            flex-direction: column;
            gap: 0.75rem;
        }
    }
</style>
