<script>
    import { onMount } from 'svelte';
    import { api } from './api.js';

    let users = [];
    let stats = { total: 0, admins: 0, teachers: 0, students: 0, pending: 0 };
    let loading = true;
    let error = '';

    onMount(async () => {
        await loadData();
    });

    async function loadData() {
        try {
            loading = true;
            
            // Load users first
            users = await api.getAllUsers();
            
            // Try to get stats from API, fallback to calculation
            try {
                stats = await api.getAdminStats();
            } catch (statsError) {
                console.warn('Stats endpoint failed, calculating manually:', statsError);
                // Calculate stats manually from users array
                stats = {
                    total: users.length,
                    admins: users.filter(u => u.role === 'admin').length,
                    teachers: users.filter(u => u.role === 'teacher').length,
                    students: users.filter(u => u.role === 'student').length,
                    pending: users.filter(u => !u.is_approved).length
                };
            }
            
            loading = false;
        } catch (err) {
            error = 'خطا در بارگذاری اطلاعات: ' + err.message;
            loading = false;
            console.error('Load error:', err);
        }
    }

    async function updateUser(userId, field, value) {
        try {
            const data = { [field]: value };
            await api.updateUser(userId, data);
            await loadData();
        } catch (err) {
            alert('خطا در به‌روزرسانی: ' + err.message);
        }
    }

    async function deleteUser(userId) {
        if (!confirm('آیا از حذف این کاربر مطمئن هستید؟')) return;
        
        try {
            await api.deleteUser(userId);
            await loadData();
        } catch (err) {
            alert('خطا در حذف: ' + err.message);
        }
    }
</script>

<div class="user-management">
    {#if loading}
        <div class="loading">در حال بارگذاری کاربران...</div>
    {:else if error}
        <div class="error">{error}</div>
    {:else}
        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card purple">
                <div class="stat-value">{stats.total}</div>
                <div class="stat-label">کل کاربران</div>
            </div>
            <div class="stat-card blue">
                <div class="stat-value">{stats.admins}</div>
                <div class="stat-label">مدیران</div>
            </div>
            <div class="stat-card green">
                <div class="stat-value">{stats.teachers}</div>
                <div class="stat-label">معلمان</div>
            </div>
            <div class="stat-card orange">
                <div class="stat-value">{stats.students}</div>
                <div class="stat-label">دانش‌آموزان</div>
            </div>
            <div class="stat-card red">
                <div class="stat-value">{stats.pending}</div>
                <div class="stat-label">در انتظار تأیید</div>
            </div>
        </div>

        <!-- Users Table -->
        <div class="table-container">
            <h2>مدیریت کاربران</h2>
            <table>
                <thead>
                    <tr>
                        <th>شناسه</th>
                        <th>نام</th>
                        <th>ایمیل</th>
                        <th>نقش</th>
                        <th>تأیید شده</th>
                        <th>تاریخ ایجاد</th>
                        <th>عملیات</th>
                    </tr>
                </thead>
                <tbody>
                    {#each users as user}
                        <tr>
                            <td>{user.id}</td>
                            <td>{user.full_name}</td>
                            <td>{user.email}</td>
                            <td>
                                <select
                                    value={user.role}
                                    on:change={(e) => updateUser(user.id, 'role', e.target.value)}
                                    class="role-select {user.role}"
                                >
                                    <option value="student">دانش‌آموز</option>
                                    <option value="teacher">معلم</option>
                                    <option value="admin">مدیر</option>
                                </select>
                            </td>
                            <td>
                                <label class="switch">
                                    <input
                                        type="checkbox"
                                        checked={user.is_approved}
                                        on:change={(e) => updateUser(user.id, 'is_approved', e.target.checked)}
                                    />
                                    <span class="slider"></span>
                                </label>
                            </td>
                            <td>{new Date(user.created_at).toLocaleDateString('fa-IR')}</td>
                            <td>
                                <button
                                    class="delete-btn"
                                    on:click={() => deleteUser(user.id)}
                                >
                                    حذف
                                </button>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<style>
    .user-management {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
        direction: rtl;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    }

    .loading, .error {
        text-align: center;
        padding: 2rem;
        font-size: 1.2rem;
    }

    .error {
        color: #c33;
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        border-right: 4px solid;
        transition: transform 0.3s, box-shadow 0.3s;
    }

    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }

    .stat-card.purple { border-color: #667eea; background: linear-gradient(135deg, #667eea15, #764ba215); }
    .stat-card.blue { border-color: #3b82f6; background: linear-gradient(135deg, #3b82f615, #2563eb15); }
    .stat-card.green { border-color: #10b981; background: linear-gradient(135deg, #10b98115, #059e6915); }
    .stat-card.orange { border-color: #f59e0b; background: linear-gradient(135deg, #f59e0b15, #d9770615); }
    .stat-card.red { border-color: #ef4444; background: linear-gradient(135deg, #ef444415, #dc262615); }

    .stat-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
    }

    .stat-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }

    /* Table Container */
    .table-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    h2 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: #333;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    thead {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    th {
        padding: 1rem;
        text-align: right;
        font-weight: 600;
    }

    td {
        padding: 1rem;
        border-bottom: 1px solid #eee;
        text-align: right;
    }

    tbody tr:hover {
        background: #f9fafb;
    }

    /* Role Select */
    .role-select {
        padding: 0.5rem;
        border: 2px solid #ddd;
        border-radius: 5px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        font-family: inherit;
        text-align: right;
    }

    .role-select.admin {
        color: #ef4444;
        border-color: #ef4444;
    }

    .role-select.teacher {
        color: #3b82f6;
        border-color: #3b82f6;
    }

    .role-select.student {
        color: #10b981;
        border-color: #10b981;
    }

    /* Toggle Switch */
    .switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: 0.4s;
        border-radius: 24px;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        right: 3px;
        bottom: 3px;
        background-color: white;
        transition: 0.4s;
        border-radius: 50%;
    }

    input:checked + .slider {
        background-color: #10b981;
    }

    input:checked + .slider:before {
        transform: translateX(-26px);
    }

    /* Delete Button */
    .delete-btn {
        background: #ef4444;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        transition: background 0.3s;
        font-family: inherit;
    }

    .delete-btn:hover {
        background: #dc2626;
    }
</style>
