<script>
    /* ================== SIDEBAR ================== */
    let navItems = [
        { id: 'group1', label: 'گروه ۱', icon: '📚', description: 'رمزگذاری حافظه ضعف' },
        { id: 'group2', label: 'گروه ۲', icon: '🎓', description: 'عدم تمرکز پایدار' },
        { id: 'group3', label: 'گروه ۳', icon: '👩‍🏫', description: 'بار شناختی بالا' },
        { id: 'group4', label: 'گروه ۴', icon: '📝', description: 'خطا در تصمیم‌گیری' },
        { id: 'group5', label: 'گروه ۵', icon: '🧠', description: 'پرسه‌زنی ذهنی' },
        { id: 'group6', label: 'گروه ۶', icon: '💡', description: 'ویژه ریاضیات' },
        { id: 'group7', label: 'گروه ۷', icon: '💡', description: 'ELISS' }
    ];

    let activeId = 'group1';
    const setActive = (id) => (activeId = id);

    
    /* ================== CHAT ================== */
let subject = "";
let favoriteSubject = "";
let streamingText = "";
let loading = false;
let socket = null;

function sendMessage() {
    if (!subject || !favoriteSubject || loading) return;

    loading = true;
    streamingText = "";

    const prompt = `
    گروه: ${activeId}
    موضوع: ${subject}
    مبحث مورد علاقه: ${favoriteSubject}
    `.trim();

    socket = new WebSocket("ws://localhost:8000/ws/chat/student");

    socket.onopen = () => {
        socket.send(prompt);
    };

    socket.onmessage = (event) => {
        try {
            // ✅ پارس کردن JSON
            const message = JSON.parse(event.data);
            
            if (message.type === "token") {
                // ✅ نمایش توکن
                streamingText += message.content;
            } 
            else if (message.type === "end") {
                // ✅ پایان استریم (بدون نمایش چیزی)
                console.log("استریم تمام شد");
            }
            else if (message.type === "error") {
                // ✅ نمایش خطا
                streamingText = message.content;
            }
        } catch (error) {
            // اگر JSON نبود (برای backward compatibility)
            console.error("خطا در پارس JSON:", error);
            streamingText += event.data;
        }
    };

    socket.onerror = () => {
        streamingText = "❌ خطا در اتصال با سرور";
        loading = false;
    };

    socket.onclose = () => {
        loading = false;
        subject = "";
        favoriteSubject = "";
        socket = null;
    };
}

</script>

<!-- ================== LAYOUT ================== -->
<div class="container" dir="rtl">

    <!-- ===== Sidebar (Right) ===== -->
    <aside class="sidebar">
        <div class="logo">پنل دستیار</div>

        {#each navItems as item}
            <div
                class="item {item.id === activeId ? 'active' : ''}"
                on:click={() => setActive(item.id)}
            >
                <div class="texts">
                    <div class="label">{item.label}</div>
                    <div class="description">{item.description}</div>
                </div>
                <div class="icon">{item.icon}</div>
            </div>
        {/each}
    </aside>

    <!-- ===== Chat Area (Left) ===== -->
    <main class="chatbox">
        <h2>دستیار هوش مصنوعی دانش‌آموز</h2>

        <div class="inputs-row">
            <div class="fancy-input">
                <span class="input-icon">♡</span>
                <input bind:value={subject} placeholder=" " />
                <label class="fancy-label">موضوع</label>
            </div>

            <div class="fancy-input">
                <span class="input-icon">★</span>
                <input bind:value={favoriteSubject} placeholder=" " />
                <label class="fancy-label">مبحث مورد علاقه</label>
            </div>
        </div>

        <button
            class="btn"
            disabled={loading}
            on:click={sendMessage}
        >
            {loading ? "⏳ در حال پردازش..." : "🚀 ارسال اطلاعات"}
        </button>

        <textarea
            class="output"
            dir="rtl"
            readonly
            bind:value={streamingText}
        />
    </main>
</div>

<style>
/* ================== LAYOUT ================== */
.container {
    display: flex;
    height: 100vh;
    font-family: "Vazirmatn", sans-serif;
}

/* ================== SIDEBAR ================== */
.sidebar {
    width: 260px;
    background: rgba(245,245,245,0.8);
    backdrop-filter: blur(12px);
    padding: 25px 18px;
    border-left: 1px solid rgba(0,0,0,0.08);
}

.logo {
    font-size: 20px;
    font-weight: bold;
    padding: 14px;
    border-radius: 12px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    text-align: center;
    margin-bottom: 25px;
}

.item {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 14px;
    cursor: pointer;
    border: 1px solid rgba(200,200,200,0.3);
    background: rgba(255,255,255,0.6);
    transition: 0.3s ease;
    direction: ltr;
    position: relative;
}

.item:hover {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    transform: translateX(-4px);
}

.item.active::before {
    content: '';
    position: absolute;
    right: 0;
    width: 5px;
    height: 100%;
    background: #667eea;
    border-radius: 5px;
}

.icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 12px;
    background: rgba(200,200,200,0.3);
}

.texts {
    text-align: right;
}

.label {
    font-size: 14px;
    font-weight: 600;
}

.description {
    font-size: 12px;
    color: #666;
}

/* ================== CHAT ================== */
.chatbox {
    flex: 1;
    padding: 2.5rem 3rem;
    display: flex;
    flex-direction: column;
}

h2 {
    text-align: center;
    margin-bottom: 2rem;
}

.inputs-row {
    display: flex;
    gap: 1.2rem;
    margin-bottom: 2rem;
}

.fancy-input {
    position: relative;
    flex: 1;
    padding: 1.2rem;
    border-radius: 16px;
    background: rgba(255,255,255,0.85);
    border: 2px solid #e7e7e7;
}

.fancy-input input {
    width: 100%;
    border: none;
    outline: none;
    background: transparent;
}

.btn {
    width: 45%;
    margin: 0 auto 1.4rem;
    padding: 1rem;
    border-radius: 16px;
    border: none;
    background: #4b32ff;
    color: #fff;
    font-weight: 700;
    font-size: 16px;
    cursor: pointer;
}

.btn:disabled {
    opacity: 0.6;
}

.output {
    flex: 1;
    border-radius: 16px;
    padding: 1.2rem;
    border: 2px solid #dedede;
    resize: none;
    line-height: 1.7;
}
</style>
