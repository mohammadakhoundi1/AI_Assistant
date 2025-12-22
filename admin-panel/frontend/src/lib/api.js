const API_URL = 'http://localhost:8000';

async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Only add Authorization header if not a login/signup request
    if (!endpoint.includes('/auth/login') && !endpoint.includes('/auth/signup')) {
        const token = localStorage.getItem('token');
        if (token) {
            console.log('Sending request with token:', token.substring(0, 20) + '...');
            headers['Authorization'] = `Bearer ${token}`;
        } else {
            console.log('No token found in localStorage');
        }
    }

    const url = `${API_URL}${endpoint}`;
    console.log('Request URL:', url);
    console.log('Request headers:', headers);

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

export const api = {
    signup: (data) => apiRequest('/auth/signup', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    login: (data) => apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    getMe: () => apiRequest('/auth/me'),

    // Admin CRUD functions
    getAllUsers: () => apiRequest('/admin/users'),

    getUser: (userId) => apiRequest(`/admin/users/${userId}`),

    updateUser: (userId, data) => apiRequest(`/admin/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    }),

    deleteUser: (userId) => apiRequest(`/admin/users/${userId}`, {
        method: 'DELETE',
    }),

    getAdminStats: () => apiRequest('/admin/stats'),

    // ✨ LLM Settings Methods
    getLLMSettings: () => apiRequest('/admin/llm-settings', {
        method: 'GET',
    }),

    updateLLMSettings: (data) => apiRequest('/admin/llm-settings', {
        method: 'PUT',
        body: JSON.stringify(data),
    }),

    fetchModels: (baseUrl, apiKey) => apiRequest('/admin/llm-settings/models', {
        method: 'POST',
        body: JSON.stringify({
            base_url: baseUrl,
            api_key: apiKey,
        }),
    }),

    // ============= 📚 RAG API Methods (NEW) =============

    /**
     * آپلود سند به سیستم RAG
     * @param {number} groupId - شماره گروه (1-8)
     * @param {File} file - فایل PDF, DOCX یا TXT
     */
    uploadRAGDocument: async (groupId, file) => {
        const token = localStorage.getItem('token');
        const formData = new FormData();
        formData.append('file', file);

        const url = `${API_URL}/admin/rag/upload/${groupId}`;
        console.log('📤 Uploading file to:', url);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                    // Note: Don't set Content-Type for FormData, browser will set it automatically with boundary
                },
                body: formData
            });

            console.log('Upload response status:', response.status);

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `خطا در آپلود: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('❌ Upload failed:', error);
            throw error;
        }
    },

    /**
     * دریافت لیست اسناد یک گروه
     * @param {number} groupId - شماره گروه (1-8)
     */
    getRAGDocuments: (groupId) => apiRequest(`/admin/rag/documents/${groupId}`, {
        method: 'GET',
    }),

    /**
     * حذف یک سند از سیستم RAG
     * @param {number} documentId - شناسه سند
     */
    deleteRAGDocument: (documentId) => apiRequest(`/admin/rag/documents/${documentId}`, {
        method: 'DELETE',
    }),
};
