<script>
    import { onMount } from 'svelte';
    import { authStore } from './stores/auth';
    import { api } from './lib/api';
    import Login from './lib/Login.svelte';
    import Signup from './lib/Signup.svelte';
    import Admin from './lib/Admin.svelte';
    import Teacher from './lib/Teacher.svelte';
    import Student from './lib/Student.svelte';

    let currentPage = 'login';
    let authState;
    let isInitializing = true;

    authStore.subscribe(value => {
        authState = value;
    });

    onMount(async () => {
        console.log('=== App.svelte mounted ===');
        
        const token = localStorage.getItem('token');
        console.log('Token from localStorage:', token ? token.substring(0, 20) + '...' : 'NO TOKEN');
        
        if (token) {
            try {
                console.log('Attempting to fetch user with token...');
                const user = await api.getMe();
                console.log('User fetched successfully:', user);
                
                authStore.login(token, user);
                
                // Set page based on user role and hash
                const hash = window.location.hash.slice(1);
                if (hash === '/admin' && user.role === 'admin') {
                    currentPage = 'admin';
                } else if (hash === '/teacher' && user.role === 'teacher') {
                    currentPage = 'teacher';
                } else if (hash === '/student' && user.role === 'student') {
                    currentPage = 'student';
                } else {
                    // Default page based on role
                    if (user.role === 'admin') {
                        currentPage = 'admin';
                        window.location.hash = '/admin';
                    } else if (user.role === 'teacher') {
                        currentPage = 'teacher';
                        window.location.hash = '/teacher';
                    } else if (user.role === 'student') {
                        currentPage = 'student';
                        window.location.hash = '/student';
                    }
                }
            } catch (err) {
                console.error('Token validation failed:', err);
                localStorage.removeItem('token');
                authStore.logout();
                window.location.hash = '';
                currentPage = 'login';
            }
        } else {
            console.log('No token found, showing login');
            const hash = window.location.hash.slice(1);
            currentPage = hash === '/signup' ? 'signup' : 'login';
        }

        isInitializing = false;
        console.log('✅ Initialization complete, currentPage:', currentPage);

        window.addEventListener('hashchange', handleHashChange);

        return () => {
            window.removeEventListener('hashchange', handleHashChange);
        };
    });

    function handleHashChange() {
        if (isInitializing) {
            console.log('⏳ Still initializing, ignoring hash change');
            return;
        }

        const hash = window.location.hash.slice(1);
        console.log('Hash changed to:', hash);
        
        if (authState.isAuthenticated) {
            if (hash === '/admin' && authState.user?.role === 'admin') {
                currentPage = 'admin';
            } else if (hash === '/teacher' && authState.user?.role === 'teacher') {
                currentPage = 'teacher';
            } else if (hash === '/student' && authState.user?.role === 'student') {
                currentPage = 'student';
            } else if (hash === '/dashboard') {
                currentPage = 'dashboard';
            } else {
                if (authState.user?.role === 'admin') {
                    currentPage = 'admin';
                    window.location.hash = '/admin';
                } else if (authState.user?.role === 'teacher') {
                    currentPage = 'teacher';
                    window.location.hash = '/teacher';
                } else if (authState.user?.role === 'student') {
                    currentPage = 'student';
                    window.location.hash = '/student';
                }
            }
        } else {
            if (hash === '/signup') {
                currentPage = 'signup';
            } else {
                currentPage = 'login';
                window.location.hash = '';
            }
        }
    }

    function handleLogout() {
        authStore.logout();
        currentPage = 'login';
        window.location.hash = '';
    }

    // Helper function to get Persian role name
    function getRoleName(role) {
        const roleMap = {
            'admin': 'مدیر',
            'teacher': 'معلم',
            'student': 'دانش‌آموز'
        };
        return roleMap[role] || role;
    }
</script>

<main>
    {#if isInitializing}
        <!-- LOADING SCREEN -->
        <div class="loading-screen">
            <div class="spinner"></div>
            <p>در حال بارگذاری...</p>
        </div>
    {:else if !authState.isAuthenticated}
        <!-- UNAUTHENTICATED PAGES -->
        {#if currentPage === 'signup'}
            <Signup />
        {:else}
            <Login />
        {/if}
    {:else}
        <!-- AUTHENTICATED PAGES -->
        {#if currentPage === 'admin' && authState.user?.role === 'admin'}
            <Admin onLogout={handleLogout} />
        {:else if currentPage === 'teacher' && authState.user?.role === 'teacher'}
            <Teacher onLogout={handleLogout} />
        {:else if currentPage === 'student' && authState.user?.role === 'student'}
            <Student onLogout={handleLogout} />
        {:else}
            <!-- DEFAULT DASHBOARD -->
            <div class="dashboard">
                <nav class="navbar">
                    <div class="nav-right">
                        <span>خوش آمدید، {authState.user?.full_name || 'کاربر'}</span>
                        <span class="role-badge">{getRoleName(authState.user?.role)}</span>
                        <button on:click={handleLogout} class="btn-logout">خروج</button>
                    </div>
                    <h1>داشبورد کاربری</h1>
                </nav>

                <div class="content">
                    {#if authState.user?.is_approved}
                        <h2>داشبورد - {getRoleName(authState.user.role)}</h2>
                        <p>حساب شما تأیید شده است! 🎉</p>
                        <p>به داشبورد شخصی خود خوش آمدید.</p>
                    {:else}
                        <div class="pending-approval">
                            <h2>⏳ در انتظار تأیید</h2>
                            <p>حساب کاربری شما در انتظار تأیید مدیر است.</p>
                            <p>لطفاً بعداً بررسی کنید یا با مدیر سیستم تماس بگیرید.</p>
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
    {/if}
</main>

<style>
    :global(body) {
        margin: 0;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        direction: rtl;
    }

    main {
        min-height: 100vh;
    }

    /* LOADING SCREEN */
    .loading-screen {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    .spinner {
        width: 50px;
        height: 50px;
        border: 5px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .loading-screen p {
        margin-top: 20px;
        font-size: 1.2rem;
    }

    /* DASHBOARD STYLES */
    .dashboard {
        min-height: 100vh;
        background: #f5f5f5;
        direction: rtl;
    }

    .navbar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    .navbar h1 {
        margin: 0;
        font-size: 1.5rem;
        order: 2;
    }

    .nav-right {
        display: flex;
        align-items: center;
        gap: 1rem;
        order: 1;
    }

    .role-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .btn-logout {
        background: white;
        color: #667eea;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        cursor: pointer;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
        font-family: inherit;
    }

    .btn-logout:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .content {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .content h2 {
        color: #333;
        margin-bottom: 1rem;
    }

    .content p {
        color: #666;
        line-height: 1.8;
        font-size: 1.1rem;
    }

    .pending-approval {
        background: white;
        padding: 3rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    .pending-approval h2 {
        color: #ff9800;
        margin-bottom: 1rem;
    }

    .pending-approval p {
        color: #666;
        line-height: 1.8;
        margin: 0.5rem 0;
    }
</style>
