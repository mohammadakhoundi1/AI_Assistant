<script>
    import { onMount } from 'svelte';
    import { api } from './api.js';

    let groups = [
        { id: 1, name: 'گروه 1' },
        { id: 2, name: 'گروه 2' },
        { id: 3, name: 'گروه 3' },
        { id: 4, name: 'گروه 4' },
        { id: 5, name: 'گروه 5' },
        { id: 6, name: 'گروه 6' },
        { id: 7, name: 'گروه 7' },
        { id: 8, name: 'گروه 8' }
    ];

    let selectedGroupId = 1;
    let documents = [];
    let loading = false;
    let uploadFile = null;
    let uploadStatus = '';
    let fileInputElement;

    onMount(() => {
        loadDocuments();
    });

    async function loadDocuments() {
        loading = true;
        uploadStatus = '';
        try {
            const response = await api.getRAGDocuments(selectedGroupId);
            console.log('📦 Raw response:', response);
            console.log('📦 Response type:', typeof response);
            console.log('📦 Is Array?', Array.isArray(response));
            
            // ✅ اگر response یک object است که documents دارد:
            if (response && response.documents && Array.isArray(response.documents)) {
                documents = response.documents;
            } 
            // ✅ اگر response خودش یک array است:
            else if (Array.isArray(response)) {
                documents = response;
            }
            // ⚠️ اگر response یک object است ولی key دیگری دارد:
            else if (response && typeof response === 'object') {
                // شاید key دیگری دارد؟
                const firstKey = Object.keys(response)[0];
                if (Array.isArray(response[firstKey])) {
                    documents = response[firstKey];
                } else {
                    console.error('❌ Response format unknown:', response);
                    documents = [];
                }
            }
            // ❌ اگر هیچکدام نبود:
            else {
                console.error('❌ Unexpected response format:', response);
                documents = [];
            }
            
            console.log('✅ اسناد بارگذاری شد:', documents);
        } catch (error) {
            console.error('❌ خطا در بارگذاری اسناد:', error);
            uploadStatus = '❌ خطا در بارگذاری لیست اسناد: ' + error.message;
            documents = [];
        } finally {
            loading = false;
        }
    }

    async function handleUpload() {
        console.log('🔵 handleUpload called');
        console.log('📁 uploadFile:', uploadFile);
        console.log('🎯 selectedGroupId:', selectedGroupId);

        if (!uploadFile) {
            uploadStatus = '⚠️ لطفاً یک فایل انتخاب کنید';
            console.warn('⚠️ فایلی انتخاب نشده');
            return;
        }

        const allowedTypes = [
            'application/pdf', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
            'text/plain'
        ];
        
        console.log('📋 File type:', uploadFile.type);
        console.log('📋 File name:', uploadFile.name);
        console.log('📋 File size:', uploadFile.size);

        if (!allowedTypes.includes(uploadFile.type)) {
            uploadStatus = '❌ فقط فایل‌های PDF، DOCX و TXT مجاز هستند';
            console.error('❌ نوع فایل نامعتبر:', uploadFile.type);
            return;
        }

        if (uploadFile.size > 10 * 1024 * 1024) {
            uploadStatus = '❌ حجم فایل نباید بیشتر از 10 مگابایت باشد';
            console.error('❌ فایل خیلی بزرگ است:', uploadFile.size);
            return;
        }

        loading = true;
        uploadStatus = '📤 در حال آپلود...';

        try {
            console.log('📤 شروع آپلود به گروه:', selectedGroupId);
            const response = await api.uploadRAGDocument(selectedGroupId, uploadFile);
            console.log('✅ پاسخ سرور:', response);
            
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
            console.log('🗑️ حذف سند با ID:', docId);
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
        console.log('📂 فایل انتخاب شد:', file);
        
        if (file) {
            uploadFile = file;
            uploadStatus = `✅ فایل "${file.name}" آماده آپلود است`;
            console.log('✅ uploadFile به‌روزرسانی شد:', uploadFile);
        } else {
            uploadFile = null;
            uploadStatus = '';
            console.log('⚠️ هیچ فایلی انتخاب نشد');
        }
    }

    function handleGroupChange() {
        console.log('🔄 گروه تغییر کرد به:', selectedGroupId);
        uploadStatus = '';
        uploadFile = null;
        if (fileInputElement) {
            fileInputElement.value = '';
        }
        loadDocuments();
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

<!-- بقیه HTML مثل قبل -->
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
        
        {#if uploadFile}
            <div class="debug-info">
                🐛 فایل انتخاب شده: {uploadFile.name} ({formatFileSize(uploadFile.size)})
            </div>
        {/if}
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
    /* همان استایل‌های قبلی */
    .rag-container {
        max-width: 1200px;
        margin: 2rem auto;
        padding: 0 1rem;
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

    .debug-info {
        background: #fef3c7;
        border: 1px solid #fbbf24;
        color: #92400e;
        padding: 0.75rem;
        border-radius: 6px;
        margin-top: 1rem;
        font-size: 0.9rem;
    }

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

    .loading-spinner {
        text-align: center;
        padding: 3rem;
        font-size: 1.2rem;
        color: #6b7280;
    }

    .empty-state {
        text-align: center;
        padding: 3rem;
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
