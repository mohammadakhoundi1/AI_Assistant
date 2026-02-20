<script>
    import { onMount } from 'svelte';
    import { api } from './api.js';

    let groups = [
        { id: 7, name: 'گروه 7' },   
    ];

    let selectedGroupId = 7;
    let documents = [];
    let loading = false;
    let uploadFile = null;
    let uploadStatus = '';
    let fileInputElement;

    // متغیرهای مربوط به تنظیمات Top K
    let topK = 3; 
    let settingsStatus = '';
    let settingsTimeout;
    let isSavingSettings = false; // متغیر جدید برای جلوگیری از کلیک همزمان

    onMount(() => {
        loadDocuments();
        loadSettings(); // بارگذاری تنظیمات در هنگام لود صفحه
    });

    // تابع جدید برای دریافت تنظیمات از سرور
    async function loadSettings() {
        try {
            const data = await api.getRagSettings(selectedGroupId);
            if (data && data.top_k !== undefined) {
                topK = data.top_k;
            } else {
                topK = 3; // مقدار پیش‌فرض در صورتی که دیتایی نباشد
            }
        } catch (error) {
            console.error('❌ خطا در دریافت تنظیمات:', error);
            topK = 3; // تنظیم روی مقدار پیش‌فرض در صورت خطا
        }
    }

    // تابع ذخیره تنظیمات تغییر یافته به async
    async function saveSettings() {
        isSavingSettings = true;
        settingsStatus = '⏳ در حال ذخیره...';
        
        try {
            // فراخوانی API برای ذخیره تنظیمات
            await api.updateRagSettings(selectedGroupId, topK);
            
            console.log('💾 تنظیمات جستجو ذخیره شد. مقدار K:', topK);
            settingsStatus = '✅ تنظیمات با موفقیت ذخیره شد!';
            
        } catch (error) {
            console.error('❌ خطا در ذخیره تنظیمات:', error);
            settingsStatus = '❌ خطا در ذخیره تنظیمات.';
        } finally {
            isSavingSettings = false;
            
            // پاک کردن پیام بعد از 3 ثانیه
            clearTimeout(settingsTimeout);
            settingsTimeout = setTimeout(() => {
                settingsStatus = '';
            }, 3000);
        }
    }

    async function loadDocuments() {
        loading = true;
        uploadStatus = '';
        try {
            const response = await api.getRAGDocuments(selectedGroupId);
            console.log('📦 Raw response:', response);
            
            if (response && response.documents && Array.isArray(response.documents)) {
                documents = response.documents;
            } 
            else if (Array.isArray(response)) {
                documents = response;
            }
            else if (response && typeof response === 'object') {
                const firstKey = Object.keys(response)[0];
                if (Array.isArray(response[firstKey])) {
                    documents = response[firstKey];
                } else {
                    console.error('❌ Response format unknown:', response);
                    documents = [];
                }
            }
            else {
                console.error('❌ Unexpected response format:', response);
                documents = [];
            }
        } catch (error) {
            console.error('❌ خطا در بارگذاری اسناد:', error);
            uploadStatus = '❌ خطا در بارگذاری لیست اسناد: ' + error.message;
            documents = [];
        } finally {
            loading = false;
        }
    }

    async function handleUpload() {
        if (!uploadFile) {
            uploadStatus = '⚠️ لطفاً یک فایل انتخاب کنید';
            return;
        }

        const allowedTypes = [
            'application/pdf', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
            'text/plain'
        ];

        if (!allowedTypes.includes(uploadFile.type)) {
            uploadStatus = '❌ فقط فایل‌های PDF، DOCX و TXT مجاز هستند';
            return;
        }

        if (uploadFile.size > 10 * 1024 * 1024) {
            uploadStatus = '❌ حجم فایل نباید بیشتر از 10 مگابایت باشد';
            return;
        }

        loading = true;
        uploadStatus = '📤 در حال آپلود...';

        try {
            // آپلود فایل فقط با groupId و uploadFile (بدون نیاز به ارسال topK)
            await api.uploadRAGDocument(selectedGroupId, uploadFile);
            uploadStatus = '✅ فایل با موفقیت آپلود شد';
            uploadFile = null;
            
            if (fileInputElement) {
                fileInputElement.value = '';
            }
            
            setTimeout(() => {
                loadDocuments();
            }, 500);
            
        } catch (error) {
            console.error('❌ خطا در آپلود:', error);
            uploadStatus = '❌ خطا در آپلود فایل: ' + (error.message || 'خطای نامشخص');
        } finally {
            loading = false;
        }
    }

    async function deleteDocument(docId, filename) {
        if (!confirm(`آیا مطمئن هستید که می‌خواهید "${filename}" را حذف کنید؟`)) {
            return;
        }

        loading = true;
        uploadStatus = '🗑️ در حال حذف...';
        
        try {
            await api.deleteRAGDocument(docId);
            uploadStatus = '✅ سند با موفقیت حذف شد';
            await loadDocuments();
        } catch (error) {
            console.error('❌ خطا در حذف:', error);
            uploadStatus = '❌ خطا در حذف سند: ' + error.message;
        } finally {
            loading = false;
        }
    }

    function handleFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            uploadFile = file;
            uploadStatus = `✅ فایل "${file.name}" آماده آپلود است`;
        } else {
            uploadFile = null;
            uploadStatus = '';
        }
    }

    function handleGroupChange() {
        uploadStatus = '';
        uploadFile = null;
        settingsStatus = ''; // پاک کردن پیام‌های قبلی تنظیمات
        if (fileInputElement) {
            fileInputElement.value = '';
        }
        
        loadDocuments();
        loadSettings(); // آپدیت تنظیمات K بر اساس گروه جدید
    }

    function formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fa-IR') + ' ' + date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
        } catch {
            return dateString;
        }
    }
</script>

<div class="rag-container">
    <div class="section-header">
        <h2>📚 مدیریت اسناد RAG</h2>
        <p>آپلود و مدیریت اسناد برای سیستم پاسخگویی هوشمند</p>
    </div>

    <div class="group-selector">
        <label for="group-select">انتخاب گروه:</label>
        <select id="group-select" bind:value={selectedGroupId} on:change={handleGroupChange}>
            {#each groups as group}
                <option value={group.id}>{group.name}</option>
            {/each}
        </select>
    </div>

    <!-- بخش تنظیمات K -->
    <div class="settings-section">
        <div class="settings-header">
            <h3>⚙️ تنظیمات جستجو (Top K)</h3>
            <span class="badge">K = {topK}</span>
        </div>
        
        <div class="slider-container">
            <label for="topK-slider">تعداد تکه‌های متنی که برای پاسخ به هوش مصنوعی ارسال می‌شود:</label>
            <div class="slider-wrapper">
                <span class="slider-limit">1</span>
                <input 
                    id="topK-slider" 
                    type="range" 
                    min="1" 
                    max="10" 
                    step="1" 
                    bind:value={topK} 
                    class="k-slider"
                    disabled={isSavingSettings}
                />
                <span class="slider-limit">10</span>
            </div>
            <p class="hint-text">
                * عدد بالاتر دقت جستجو را افزایش می‌دهد، اما مصرف توکن را بالا برده و سرعت پاسخگویی را کمی کاهش می‌دهد.
            </p>
        </div>

        <div class="settings-actions">
            <button 
                class="btn-save" 
                on:click={saveSettings}
                disabled={isSavingSettings}
            >
                {isSavingSettings ? '⏳ در حال ذخیره...' : '💾 ذخیره تنظیمات'}
            </button>
            {#if settingsStatus}
                <span class="settings-success-msg" class:error-msg={settingsStatus.includes('❌')}>{settingsStatus}</span>
            {/if}
        </div>
    </div>

    <div class="upload-section">
        <h3>📤 آپلود سند جدید</h3>
        <div class="upload-form">
            <input 
                type="file" 
                accept=".pdf,.docx,.txt" 
                on:change={handleFileChange}
                bind:this={fileInputElement}
                disabled={loading}
            />
            <button 
                on:click={handleUpload} 
                disabled={loading || !uploadFile}
                class="btn-primary"
                title={!uploadFile ? 'ابتدا یک فایل انتخاب کنید' : 'کلیک کنید تا آپلود شود'}
            >
                {loading ? '⏳ در حال پردازش...' : '📤 آپلود فایل'}
            </button>
        </div>
        {#if uploadStatus}
            <div class="status-message" class:error={uploadStatus.includes('❌')} class:success={uploadStatus.includes('✅')}>
                {uploadStatus}
            </div>
        {/if}
        <div class="upload-hint">
            💡 فرمت‌های مجاز: PDF, DOCX, TXT (حداکثر 10 MB)
        </div>
    </div>

    <div class="documents-section">
        <h3>📄 اسناد موجود برای {groups.find(g => g.id === selectedGroupId)?.name}</h3>
        
        {#if loading}
            <div class="loading-spinner">⏳ در حال بارگذاری...</div>
        {:else if !Array.isArray(documents) || documents.length === 0}
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>هیچ سندی برای این گروه آپلود نشده است</p>
            </div>
        {:else}
            <div class="documents-table">
                <table>
                    <thead>
                        <tr>
                            <th>نام فایل</th>
                            <th>نوع</th>
                            <th>حجم</th>
                            <th>تعداد چانک</th>
                            <th>تاریخ آپلود</th>
                            <th>عملیات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each documents as doc}
                            <tr>
                                <td>
                                    <div class="file-name">
                                        {#if doc.file_type === 'pdf'}
                                            📕
                                        {:else if doc.file_type === 'docx'}
                                            📘
                                        {:else}
                                            📄
                                        {/if}
                                        {doc.filename}
                                    </div>
                                </td>
                                <td>{doc.file_type?.toUpperCase() || 'N/A'}</td>
                                <td>{formatFileSize(doc.file_size)}</td>
                                <td>{doc.chunk_count || 0}</td>
                                <td>{formatDate(doc.uploaded_at)}</td>
                                <td>
                                    <button 
                                        class="btn-delete" 
                                        on:click={() => deleteDocument(doc.id, doc.filename)}
                                        disabled={loading}
                                    >
                                        🗑️ حذف
                                    </button>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
    </div>
</div>

<style>
    /* استایل‌های پایه */
    .rag-container {
        max-width: 1200px;
        margin: 2rem auto;
        padding: 0 1rem;
        direction: rtl; 
    }

    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .section-header h2 {
        margin: 0 0 0.5rem 0;
        font-size: 1.8rem;
    }

    .section-header p {
        margin: 0;
        opacity: 0.9;
        font-size: 1rem;
    }

    .group-selector {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .group-selector label {
        font-weight: 600;
        color: #374151;
    }

    .group-selector select {
        flex: 1;
        padding: 0.75rem;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 1rem;
        font-family: inherit;
        transition: all 0.3s;
    }

    .group-selector select:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* استایل‌های بخش Top K */
    .settings-section {
        background: white;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .settings-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }

    .settings-header h3 {
        margin: 0;
        color: #374151;
        font-size: 1.25rem;
    }

    .badge {
        background-color: #e0e7ff;
        color: #3730a3;
        font-weight: 600;
        padding: 0.25rem 1rem;
        border-radius: 9999px;
        font-size: 0.9rem;
    }

    .slider-container label {
        display: block;
        margin-bottom: 1rem;
        color: #4b5563;
        font-size: 0.95rem;
    }

    .slider-wrapper {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    .slider-limit {
        font-weight: bold;
        color: #9ca3af;
        min-width: 20px;
        text-align: center;
    }

    .k-slider {
        flex: 1;
        height: 8px;
        background: #e5e7eb;
        border-radius: 8px;
        appearance: none;
        outline: none;
        cursor: pointer;
    }
    
    .k-slider::-webkit-slider-thumb {
        appearance: none;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #667eea;
        cursor: pointer;
        transition: background 0.15s ease-in-out;
    }
    
    .k-slider::-webkit-slider-thumb:hover {
        background: #764ba2;
    }
    
    .k-slider:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .k-slider:disabled::-webkit-slider-thumb {
        cursor: not-allowed;
        background: #9ca3af;
    }

    .hint-text {
        font-size: 0.8rem;
        color: #9ca3af;
        margin: 0.5rem 0 0 0;
    }

    /* استایل‌های مربوط به دکمه ذخیره تنظیمات */
    .settings-actions {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid #f3f4f6;
    }

    .btn-save {
        background: #10b981;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-size: 0.95rem;
        font-family: inherit;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
    }

    .btn-save:hover:not(:disabled) {
        background: #059669;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
    }
    
    .btn-save:disabled {
        background: #9ca3af;
        cursor: not-allowed;
        opacity: 0.7;
    }

    .settings-success-msg {
        color: #059669;
        font-size: 0.95rem;
        font-weight: 500;
        animation: fadeIn 0.3s ease-in;
    }
    
    .error-msg {
        color: #dc2626;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* آپلود فرم */
    .upload-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .upload-section h3 {
        margin: 0 0 1.5rem 0;
        color: #374151;
    }

    .upload-form {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .upload-form input[type="file"] {
        flex: 1;
        padding: 0.75rem;
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        font-family: inherit;
        transition: all 0.3s;
        cursor: pointer;
    }

    .upload-form input[type="file"]:hover:not(:disabled) {
        border-color: #667eea;
        background: #f9fafb;
    }

    .upload-form input[type="file"]:disabled {
        cursor: not-allowed;
        opacity: 0.5;
    }

    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-size: 1rem;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.3s;
        white-space: nowrap;
        font-weight: 600;
    }

    .btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .btn-primary:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background: #9ca3af;
    }

    .status-message {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-weight: 500;
    }

    .status-message.success {
        background: #d1fae5;
        color: #065f46;
        border: 1px solid #6ee7b7;
    }

    .status-message.error {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }

    .upload-hint {
        color: #6b7280;
        font-size: 0.9rem;
    }

    /* جدول اسناد */
    .documents-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .documents-section h3 {
        margin: 0 0 1.5rem 0;
        color: #374151;
    }

    .loading-spinner, .empty-state {
        text-align: center;
        padding: 3rem;
        font-size: 1.2rem;
        color: #6b7280;
    }

    .empty-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    .documents-table {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    thead {
        background: #f9fafb;
    }

    th {
        padding: 1rem;
        text-align: right;
        font-weight: 600;
        color: #374151;
        border-bottom: 2px solid #e5e7eb;
    }

    td {
        padding: 1rem;
        border-bottom: 1px solid #e5e7eb;
    }

    tbody tr:hover {
        background: #f9fafb;
    }

    .file-name {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;
    }

    .btn-delete {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.3s;
        font-weight: 500;
    }

    .btn-delete:hover:not(:disabled) {
        background: #fca5a5;
        transform: translateY(-1px);
    }

    .btn-delete:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>
