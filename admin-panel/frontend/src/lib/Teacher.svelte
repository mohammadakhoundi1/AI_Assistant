<script>
    export let onLogout;
    
    let activeTab = 'dashboard';
    let isSidebarOpen = true;

    const menuItems = [
        { id: 'dashboard', label: 'داشبورد', icon: '📊', color: '#667eea' },
        { id: 'courses', label: 'دوره‌های من', icon: '📚', color: '#3b82f6' },
        { id: 'students', label: 'دانش‌آموزان', icon: '👥', color: '#10b981' },
        { id: 'exams', label: 'آزمون‌ها', icon: '📝', color: '#f59e0b' },
        { id: 'grades', label: 'نمرات', icon: '📈', color: '#ec4899' },
        { id: 'schedule', label: 'برنامه کلاسی', icon: '📅', color: '#8b5cf6' },
        { id: 'resources', label: 'منابع آموزشی', icon: '🗂️', color: '#06b6d4' }
    ];

    function toggleSidebar() {
        isSidebarOpen = !isSidebarOpen;
    }
</script>

<div class="teacher-layout">
    <!-- SIDEBAR -->
    <aside class="sidebar" class:collapsed={!isSidebarOpen}>
        <div class="sidebar-header">
            <h2>{isSidebarOpen ? 'پنل معلم' : '📚'}</h2>
            <button class="toggle-btn" on:click={toggleSidebar}>
                {isSidebarOpen ? '◀' : '▶'}
            </button>
        </div>

        <nav class="sidebar-nav">
            {#each menuItems as item}
                <button
                    class="nav-item"
                    class:active={activeTab === item.id}
                    style="--item-color: {item.color}"
                    on:click={() => activeTab = item.id}
                >
                    <span class="icon">{item.icon}</span>
                    {#if isSidebarOpen}
                        <span class="label">{item.label}</span>
                    {/if}
                </button>
            {/each}
        </nav>

        <button class="logout-sidebar" on:click={onLogout}>
            <span class="icon">🚪</span>
            {#if isSidebarOpen}<span>خروج</span>{/if}
        </button>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="main-content">
        <header class="top-bar">
            <div class="breadcrumb">
                <span class="current-page">{menuItems.find(m => m.id === activeTab)?.label}</span>
            </div>
            <div class="user-info">
                <span class="welcome">خوش آمدید، استاد</span>
                <div class="avatar">👨‍🏫</div>
            </div>
        </header>

        <div class="content-area">
            {#if activeTab === 'dashboard'}
                <div class="dashboard-grid">
                    <div class="stat-card purple">
                        <div class="stat-icon">📚</div>
                        <div class="stat-details">
                            <h3>۵</h3>
                            <p>دوره‌های فعال</p>
                        </div>
                    </div>
                    <div class="stat-card blue">
                        <div class="stat-icon">👥</div>
                        <div class="stat-details">
                            <h3>۱۲۳</h3>
                            <p>دانش‌آموز</p>
                        </div>
                    </div>
                    <div class="stat-card green">
                        <div class="stat-icon">✅</div>
                        <div class="stat-details">
                            <h3>۴۲</h3>
                            <p>تکلیف تصحیح‌شده</p>
                        </div>
                    </div>
                    <div class="stat-card orange">
                        <div class="stat-icon">⏳</div>
                        <div class="stat-details">
                            <h3>۸</h3>
                            <p>تکلیف در انتظار</p>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2>آخرین فعالیت‌ها</h2>
                    <div class="activity-feed">
                        <div class="activity-item">
                            <span class="activity-icon">📝</span>
                            <div class="activity-text">
                                <strong>تکلیف جدید</strong> در درس «ریاضیات پیشرفته» ثبت شد
                                <span class="time">۲ ساعت پیش</span>
                            </div>
                        </div>
                        <div class="activity-item">
                            <span class="activity-icon">✅</span>
                            <div class="activity-text">
                                <strong>۱۵ دانش‌آموز</strong> آزمون میان‌ترم را تکمیل کردند
                                <span class="time">۵ ساعت پیش</span>
                            </div>
                        </div>
                        <div class="activity-item">
                            <span class="activity-icon">💬</span>
                            <div class="activity-text">
                                <strong>پیام جدید</strong> از دانش‌آموز در تالار گفتگو
                                <span class="time">دیروز</span>
                            </div>
                        </div>
                    </div>
                </div>
            {:else}
                <div class="placeholder">
                    <div class="placeholder-icon">{menuItems.find(m => m.id === activeTab)?.icon}</div>
                    <h2>بخش {menuItems.find(m => m.id === activeTab)?.label}</h2>
                    <p>این بخش به زودی راه‌اندازی می‌شود...</p>
                </div>
            {/if}
        </div>
    </main>
</div>

<style>
    .teacher-layout {
        display: flex;
        min-height: 100vh;
        background: #f5f7fa;
        direction: rtl;
        font-family: 'Vazirmatn', sans-serif;
    }

    .sidebar {
        width: 280px;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
        transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
        position: relative;
        z-index: 100;
    }

    .sidebar.collapsed {
        width: 80px;
    }

    .sidebar-header {
        padding: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .sidebar-header h2 {
        margin: 0;
        font-size: 1.3rem;
        font-weight: 700;
    }

    .toggle-btn {
        background: rgba(255, 255, 255, 0.2);
        border: none;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        cursor: pointer;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .toggle-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: scale(1.1);
    }

    .sidebar-nav {
        flex: 1;
        padding: 1rem 0;
        overflow-y: auto;
    }

    .nav-item {
        width: 100%;
        background: transparent;
        border: none;
        color: white;
        padding: 1rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        cursor: pointer;
        transition: all 0.3s;
        border-right: 4px solid transparent;
        font-family: inherit;
        text-align: right;
    }

    .nav-item:hover {
        background: rgba(255, 255, 255, 0.1);
        border-right-color: white;
    }

    .nav-item.active {
        background: rgba(255, 255, 255, 0.15);
        border-right-color: var(--item-color);
        font-weight: 600;
    }

    .nav-item .icon {
        font-size: 1.5rem;
        min-width: 30px;
        text-align: center;
    }

    .nav-item .label {
        font-size: 1rem;
        white-space: nowrap;
    }

    .logout-sidebar {
        margin: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        justify-content: center;
        transition: all 0.3s;
        font-family: inherit;
    }

    .logout-sidebar:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }

    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    .top-bar {
        background: white;
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }

    .breadcrumb .current-page {
        font-size: 1.3rem;
        font-weight: 600;
        color: #333;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .welcome {
        color: #666;
        font-size: 0.95rem;
    }

    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
    }

    .content-area {
        flex: 1;
        padding: 2rem;
        overflow-y: auto;
    }

    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        transition: transform 0.3s, box-shadow 0.3s;
    }

    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }

    .stat-card.purple { border-right: 4px solid #667eea; }
    .stat-card.blue { border-right: 4px solid #3b82f6; }
    .stat-card.green { border-right: 4px solid #10b981; }
    .stat-card.orange { border-right: 4px solid #f59e0b; }

    .stat-icon {
        font-size: 3rem;
        opacity: 0.9;
    }

    .stat-details h3 {
        margin: 0;
        font-size: 2rem;
        color: #333;
    }

    .stat-details p {
        margin: 0.3rem 0 0;
        color: #666;
        font-size: 0.9rem;
    }

    .section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }

    .section h2 {
        margin-top: 0;
        color: #333;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }

    .activity-feed {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem;
        background: #f9fafb;
        border-radius: 10px;
        border-right: 3px solid #667eea;
    }

    .activity-icon {
        font-size: 1.8rem;
    }

    .activity-text {
        flex: 1;
    }

    .activity-text strong {
        color: #667eea;
    }

    .time {
        display: block;
        font-size: 0.85rem;
        color: #999;
        margin-top: 0.3rem;
    }

    .placeholder {
        text-align: center;
        padding: 4rem 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }

    .placeholder-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
    }

    .placeholder h2 {
        color: #333;
        margin-bottom: 0.5rem;
    }

    .placeholder p {
        color: #666;
    }
</style>
