<script>
    import { onMount } from 'svelte';

    /* ================== PROPS ================== */
    export let onLogout = () => {
        localStorage.removeItem("token");
        goto('/login');
    };

    /* ================== STATE MANAGEMENT ================== */
    let activeId = 'group1';
    let subject = "";
    let favoriteSubject = "";
    let emotionalMessage = "";
    let streamingText = "";
    let loading = false;
    let socket = null;
    let token = localStorage.getItem("token");
    let userRole = "استاد";

    /* ================== GROUPS DATA ================== */
    const groups = [
        { 
            id: 'group1', 
            name: 'رمزگذاری حافظه', 
            icon: '🧠',
            description: 'تمرین‌های سقراطی برای تقویت حافظه'
        },
        { 
            id: 'group2', 
            name: 'تمرکز پایدار', 
            icon: '🎯',
            description: 'پرسش‌های کوتاه برای حفظ توجه'
        },
        { 
            id: 'group3', 
            name: 'بار شناختی', 
            icon: '⚡',
            description: 'مسائل ساده و گام‌به‌گام'
        },
        { 
            id: 'group4', 
            name: 'تصمیم‌گیری', 
            icon: '🎲',
            description: 'تمرین قضاوت و تحلیل'
        },
        { 
            id: 'group5', 
            name: 'سرگردانی ذهن', 
            icon: '🌊',
            description: 'پرسش‌های داستانی و جذاب'
        },
        { 
            id: 'group6', 
            name: 'ریاضی تعاملی', 
            icon: '🔢',
            description: 'حل مسائل ریاضی سقراطی'
        },
        { 
            id: 'group7', 
            name: 'حمایت عاطفی', 
            icon: '💚',
            description: 'پشتیبانی روانی و هیجانی'
        }
    ];

    /* ================== PROMPTS ================== */
    const prompts = {
        group1: `شما یک معلم سقراطی هستید که با پرسیدن سوالات راهنمایی‌کننده به دانش‌آموز کمک می‌کنید تا مطالب را عمیق‌تر یاد بگیرد و در حافظه رمزگذاری کند.

موضوع درسی: {subject}
علاقه دانش‌آموز: {favoriteSubject}

رویکرد شما:
- از مثال‌ها و تشبیهات مرتبط با علاقه دانش‌آموز استفاده کنید
- سوالاتی بپرسید که دانش‌آموز را به فکر کردن وادار کند
- به او کمک کنید تا ارتباط بین مفاهیم را پیدا کند
- تشویق کنید که مطالب را با کلمات خودش توضیح دهد`,

        group2: `شما یک معلم سقراطی هستید که با پرسیدن سوالات کوتاه و جذاب به دانش‌آموز کمک می‌کنید تمرکزش را حفظ کند.

موضوع درسی: {subject}
علاقه دانش‌آموز: {favoriteSubject}

رویکرد شما:
- سوالات کوتاه و مشخص بپرسید
- از حواس‌پرتی جلوگیری کنید
- به دانش‌آموز فیدبک فوری بدهید
- موضوع را به بخش‌های کوچک تقسیم کنید`,

        group3: `شما یک معلم سقراطی هستید که مسائل پیچیده را به قطعات ساده و قابل هضم تبدیل می‌کنید.

موضوع درسی: {subject}
علاقه دانش‌آموز: {favoriteSubject}

رویکرد شما:
- هر مفهوم را به اجزای کوچکتر تقسیم کنید
- از زبان ساده استفاده کنید
- گام به گام پیش بروید
- اطمینان حاصل کنید که دانش‌آموز هر مرحله را فهمیده است`,

        group4: `شما یک معلم سقراطی هستید که به دانش‌آموز کمک می‌کنید تصمیم‌گیری و قضاوت بهتری داشته باشد.

موضوع درسی: {subject}
علاقه دانش‌آموز: {favoriteSubject}

رویکرد شما:
- سناریوها و موقعیت‌های واقعی ارائه دهید
- از دانش‌آموز بخواهید گزینه‌های مختلف را بررسی کند
- سوالاتی بپرسید که او را به تفکر انتقادی وادار کند
- به او کمک کنید تا پیامدهای تصمیمات را بسنجد`,

        group5: `شما یک معلم سقراطی هستید که با داستان‌ها و سوالات جذاب، ذهن دانش‌آموز را درگیر می‌کنید و از سرگردانی ذهن جلوگیری می‌کنید.

موضوع درسی: {subject}
علاقه دانش‌آموز: {favoriteSubject}

رویکرد شما:
- از داستان‌ها و مثال‌های جذاب استفاده کنید
- سوالات هیجان‌انگیز بپرسید
- موضوع را به علایق دانش‌آموز مرتبط کنید
- فضای یادگیری را سرگرم‌کننده نگه دارید`,

        group6: `شما یک معلم ریاضی سقراطی هستید که به جای دادن پاسخ مستقیم، با پرسیدن سوالات راهنما به دانش‌آموز کمک می‌کنید خودش به حل مسئله برسد.

موضوع درسی: {subject}
علاقه دانش‌آموز: {favoriteSubject}

رویکرد شما:
- مسئله را به مراحل کوچکتر تقسیم کنید
- از دانش‌آموز بخواهید فرآیند فکری خود را توضیح دهد
- در صورت اشتباه، او را با سوالات هدایت کنید
- تشویق کنید که روش‌های مختلف را امتحان کند`,

        group7: `شما یک روان‌شناس و مشاور حمایت‌کننده هستید که با همدلی و درک به دانش‌آموز گوش می‌دهید.

پیام دانش‌آموز: {emotionalMessage}

رویکرد شما:
- با همدلی و بدون قضاوت گوش دهید
- احساسات دانش‌آموز را تایید کنید
- کمک کنید تا احساسات خود را بهتر درک کند
- راهکارهای سازنده پیشنهاد دهید
- به او یادآوری کنید که تنها نیست`
    };

    /* ================== FUNCTIONS ================== */
    function setActiveGroup(groupId) {
        activeId = groupId;
        streamingText = "";
    }

    function sendMessage() {
        if (loading) return;
        
        // Validation
        if (activeId === 'group7') {
            if (!emotionalMessage.trim()) {
                streamingText = "⚠️ لطفاً پیام خود را وارد کنید";
                return;
            }
        } else {
            if (!subject.trim() || !favoriteSubject.trim()) {
                streamingText = "⚠️ لطفاً موضوع و مبحث مورد علاقه را وارد کنید";
                return;
            }
        }

        // ساخت Prompt
        let prompt = prompts[activeId];
        if (!prompt) {
            streamingText = "⚠️ لطفاً ابتدا یک گروه از نوار کناری انتخاب کنید";
            return;
        }

        // جایگزینی متغیرها
        prompt = prompt
            .replace(/{subject}/g, subject)
            .replace(/{favoriteSubject}/g, favoriteSubject)
            .replace(/{emotionalMessage}/g, emotionalMessage);
        
        console.log("📤 Prompt ارسالی به LLM:", prompt);

        // شروع ارسال
        loading = true;
        streamingText = "";

        socket = new WebSocket(`ws://localhost:8000/ws/chat/student?token=${token}`);

        socket.onopen = () => {
            socket.send(prompt);
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                
                if (message.type === "token") {
                    streamingText += message.content;
                } 
                else if (message.type === "end") {
                    console.log("✅ استریم تمام شد");
                }
                else if (message.type === "error") {
                    streamingText = "❌ " + message.content;
                }
            } catch (error) {
                const chunk = event.data;
                if (chunk === "[[END]]") return;
                if (chunk.includes("[[END]]")) {
                    streamingText += chunk.replace("[[END]]", "");
                    return;
                }
                streamingText += chunk;
            }
        };

        socket.onerror = () => {
            streamingText = "❌ خطا در اتصال با سرور";
            loading = false;
        };

        socket.onclose = () => {
            loading = false;
            socket = null;
            
            // پاکسازی input‌ها
            if (activeId === 'group7') {
                emotionalMessage = "";
            } else {
                subject = "";
                favoriteSubject = "";
            }
        };
    }

    function stopStream() {
        if (socket) {
            socket.close();
            loading = false;
            socket = null;
        }
    }

    onMount(() => {
        return () => {
            if (socket) socket.close();
        };
    });
</script>

<!-- ================== HTML ================== -->
<div class="student-container">
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-header">
            <h2 class="sidebar-title">📚 دسته‌بندی‌ها</h2>
            <button class="logout-btn" on:click={onLogout}>
                🚪 خروج
            </button>
        </div>
        
        <!-- Role Badge -->
        <div class="role-badge">
            <span class="role-icon">🎓</span>
            <div class="role-info">
                <span class="role-label">نقش شما:</span>
                <span class="role-name">{userRole}</span>
            </div>
        </div>

        <ul class="groups-list">
            {#each groups as group}
                <li>
                    <button
                        class="group-button"
                        class:active={activeId === group.id}
                        on:click={() => setActiveGroup(group.id)}
                        disabled={loading}
                    >
                        <span class="group-icon">{group.icon}</span>
                        <div class="group-info">
                            <span class="group-name">{group.name}</span>
                            <span class="group-desc">{group.description}</span>
                        </div>
                    </button>
                </li>
            {/each}
        </ul>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
        <div class="content-header">
            <h1>
                {groups.find(g => g.id === activeId)?.icon || '📖'} 
                {groups.find(g => g.id === activeId)?.name || 'انتخاب کنید'}
            </h1>
            <p class="content-description">
                {groups.find(g => g.id === activeId)?.description || ''}
            </p>
        </div>

        <!-- Form Section -->
        <div class="form-section">
            {#if activeId === 'group7'}
                <!-- Input برای حمایت عاطفی -->
                <div class="emotional-input-container">
                    <div class="fancy-textarea">
                        
                        <textarea 
                            bind:value={emotionalMessage}
                            placeholder="چه اتفاقی افتاده؟ با من در میان بگذار..."
                            disabled={loading}
                            rows="6"
                        ></textarea>
                        
                    </div>
                </div>
            {:else}
                <!-- Input های معمولی -->
                <div class="fancy-inputs-container">
                    <div class="fancy-input">
                        
                        <input 
                            bind:value={subject} 
                            placeholder=" " 
                            disabled={loading}
                        />
                        <label class="fancy-label">موضوع</label>
                    </div>

                    <div class="fancy-input">
                        
                        <input 
                            bind:value={favoriteSubject} 
                            placeholder=" " 
                            disabled={loading}
                        />
                        <label class="fancy-label">مبحث مورد علاقه</label>
                    </div>
                </div>
            {/if}

            <div class="button-group">
                <button 
                    on:click={sendMessage} 
                    disabled={loading}
                    class="btn btn-primary"
                >
                    {loading ? '⏳ در حال ارسال...' : '📤 ارسال پیام'}
                </button>

                {#if loading}
                    <button 
                        on:click={stopStream} 
                        class="btn btn-danger"
                    >
                        ⛔ توقف
                    </button>
                {/if}
            </div>
        </div>

        <!-- Response Section -->
        {#if streamingText}
            <div class="response-section">
                <div class="response-header">
                    <span class="response-icon">💬</span>
                    <h3>پاسخ معلم سقراطی</h3>
                </div>
                <div class="response-content">
                    <p>{streamingText}</p>
                </div>
            </div>
        {/if}
    </main>
</div>

<!-- ================== STYLES ================== -->
<style>
    .student-container {
        display: flex;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Vazirmatn', sans-serif;
        direction: rtl;
    }

    /* ====== SIDEBAR ====== */
    .sidebar {
        width: 300px;
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem 1rem;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
        overflow-y: auto;
    }

    .sidebar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        gap: 1rem;
    }

    .sidebar-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }

    .logout-btn {
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        white-space: nowrap;
    }

    .logout-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
    }

    /* ====== ROLE BADGE ====== */
    .role-badge {
        display: flex;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        animation: fadeInUp 0.5s ease;
    }

    .role-icon {
        font-size: 2rem;
        animation: bounce 2s infinite;
    }

    .role-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .role-label {
        font-size: 0.85rem;
        font-weight: 500;
        opacity: 0.9;
    }

    .role-name {
        font-size: 1.2rem;
        font-weight: 800;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes bounce {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-5px);
        }
    }

    /* ====== GROUPS LIST ====== */
    .groups-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .groups-list li {
        margin-bottom: 0.5rem;
    }

    .group-button {
        width: 100%;
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: white;
        border: 2px solid transparent;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: right;
    }

    .group-button:hover:not(:disabled) {
        transform: translateX(-5px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        border-color: #667eea;
    }

    .group-button.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
    }

    .group-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .group-icon {
        font-size: 2rem;
    }

    .group-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .group-name {
        font-weight: 700;
        font-size: 1.1rem;
    }

    .group-desc {
        font-size: 0.9rem;
        font-weight: 500;
        opacity: 0.8;
    }

    .group-button.active .group-desc {
        opacity: 0.9;
    }

    /* ====== MAIN CONTENT ====== */
    .main-content {
        flex: 1;
        padding: 2rem;
        overflow-y: auto;
    }

    .content-header {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    .content-header h1 {
        margin: 0 0 0.5rem 0;
        color: #667eea;
        font-size: 2.5rem;
        font-weight: 800;
    }

    .content-description {
        margin: 0;
        color: #666;
        font-size: 1.3rem;
        font-weight: 600;
    }

    /* ====== FORM SECTION ====== */
    .form-section {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    .fancy-inputs-container {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .fancy-input {
        flex: 1;
        position: relative;
    }

    .input-icon {
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5rem;
        color: #667eea;
        pointer-events: none;
        z-index: 1;
    }

    .fancy-input input {
        width: 100%;
        padding: 1rem;
        padding-inline-end: 3.5rem;
        padding-inline-start: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        background: white;
    }

    .fancy-input input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .fancy-input input:disabled {
        background: #f5f5f5;
        cursor: not-allowed;
    }

    .fancy-label {
        position: absolute;
        right: 3.5rem;
        top: 50%;
        transform: translateY(-50%);
        background: white;
        padding: 0 0.5rem;
        color: #999;
        font-weight: 600;
        pointer-events: none;
        transition: all 0.3s ease;
    }

    .fancy-input input:focus + .fancy-label,
    .fancy-input input:not(:placeholder-shown) + .fancy-label {
        top: 0;
        font-size: 0.9rem;
        color: #667eea;
    }

    /* ====== TEXTAREA FOR GROUP 7 ====== */
    .emotional-input-container {
        margin-bottom: 1.5rem;
    }

    .fancy-textarea {
        position: relative;
    }

    .fancy-textarea .input-icon {
        top: 20px;
    }

    .fancy-textarea textarea {
        width: 100%;
        padding: 1rem;
        padding-inline-end: 3.5rem;
        padding-inline-start: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Vazirmatn', sans-serif;
        transition: all 0.3s ease;
        background: white;
        resize: vertical;
        min-height: 150px;
    }

    .fancy-textarea textarea:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .fancy-textarea textarea:disabled {
        background: #f5f5f5;
        cursor: not-allowed;
    }

    .fancy-textarea .fancy-label {
        top: 20px;
    }

    .fancy-textarea textarea:focus + .fancy-label,
    .fancy-textarea textarea:not(:placeholder-shown) + .fancy-label {
        top: 0;
        font-size: 0.9rem;
        color: #667eea;
    }

    /* ====== BUTTONS ====== */
    .button-group {
        display: flex;
        gap: 1rem;
    }

    .btn {
        padding: 1.2rem 2.5rem;
        border: none;
        border-radius: 12px;
        font-size: 1.2rem;
        font-weight: 800;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        flex: 1;
    }

    .btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }

    .btn-primary:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
    }

    .btn-danger {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }

    .btn-danger:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(245, 87, 108, 0.4);
    }

    /* ====== RESPONSE SECTION ====== */
    .response-section {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }

    .response-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .response-icon {
        font-size: 1.8rem;
    }

    .response-header h3 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 800;
    }

    .response-content {
        padding: 2rem;
        line-height: 2;
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
    }

    .response-content p {
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    /* ====== RESPONSIVE ====== */
    @media (max-width: 768px) {
        .student-container {
            flex-direction: column;
        }

        .sidebar {
            width: 100%;
            padding: 1rem;
        }

        .sidebar-header {
            flex-direction: column;
            align-items: stretch;
        }

        .logout-btn {
            width: 100%;
        }

        .fancy-inputs-container {
            flex-direction: column;
        }

        .button-group {
            flex-direction: column;
        }

        .content-header h1 {
            font-size: 2rem;
        }

        .content-description {
            font-size: 1.1rem;
        }
    }
</style>
