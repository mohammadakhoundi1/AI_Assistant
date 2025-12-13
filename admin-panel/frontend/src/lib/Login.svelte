<script>
    import { authStore } from '../stores/auth';
    import { api } from './api';

    let email = '';
    let password = '';
    let error = '';
    let loading = false;

    async function handleLogin() {
        error = '';
        loading = true;

        try {
            // Step 1: Login and get token
            const response = await api.login({ email, password });
            
            // Step 2: Store token in localStorage IMMEDIATELY
            localStorage.setItem('token', response.access_token);
            console.log('Token stored:', response.access_token.substring(0, 20) + '...');
            
            // Step 3: Check if user is approved (from login response)
            if (!response.is_approved) {
                error = 'حساب کاربری شما در انتظار تایید مدیر است.';
                loading = false;
                return;
            }
            
            // Step 4: Now fetch user details (token is now in localStorage)
            const user = await api.getMe();
            console.log('User fetched:', user);
            
            // Step 5: Update auth store
            authStore.login(response.access_token, user);
            
            // Step 6: Redirect based on role
            if (user.role === 'admin') {
                window.location.hash = '#/admin';
            } else if (user.role === 'teacher') {
                window.location.hash = '#/teacher';
            } else {
                window.location.hash = '#/student';
            }
            
        } catch (err) {
            console.error('Login error:', err);
            error = err.message || 'ورود ناموفق بود. لطفاً اطلاعات ورود خود را بررسی کنید.';
        } finally {
            loading = false;
        }
    }
</script>

<div class="auth-container">
    <div class="auth-card">
        <h2>ورود به سیستم</h2>
        
        {#if error}
            <div class="error-message">{error}</div>
        {/if}

        <form on:submit|preventDefault={handleLogin}>
            <div class="form-group">
                <label for="email">ایمیل</label>
                <input 
                    id="email"
                    type="email" 
                    bind:value={email}
                    placeholder="ایمیل خود را وارد کنید"
                    required
                    disabled={loading}
                />
            </div>

            <div class="form-group">
                <label for="password">رمز عبور</label>
                <input 
                    id="password"
                    type="password" 
                    bind:value={password}
                    placeholder="رمز عبور را وارد کنید"
                    required
                    disabled={loading}
                />
            </div>

            <button type="submit" class="btn-primary" disabled={loading}>
                {loading ? 'در حال ورود...' : 'ورود'}
            </button>
        </form>

        <p class="auth-link">
            حساب کاربری ندارید؟ <button on:click={() => window.location.hash = '#/signup'}>ثبت‌نام کنید</button>
        </p>
    </div>
</div>

<style>
    .auth-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        direction: rtl;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    }

    .auth-card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        width: 100%;
        max-width: 400px;
    }

    h2 {
        text-align: center;
        color: #333;
        margin-bottom: 1.5rem;
        font-size: 1.75rem;
    }

    .form-group {
        margin-bottom: 1rem;
    }

    label {
        display: block;
        margin-bottom: 0.5rem;
        color: #555;
        font-weight: 500;
    }

    input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #ddd;
        border-radius: 5px;
        font-size: 1rem;
        transition: border-color 0.3s;
        text-align: right;
        font-family: inherit;
    }

    input:focus {
        outline: none;
        border-color: #667eea;
    }

    input:disabled {
        background-color: #f5f5f5;
        cursor: not-allowed;
    }

    input::placeholder {
        text-align: right;
        color: #aaa;
    }

    .btn-primary {
        width: 100%;
        padding: 0.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s;
        font-family: inherit;
    }

    .btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
    }

    .btn-primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
    }

    .error-message {
        background: #fee;
        color: #c33;
        padding: 0.75rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        text-align: center;
        line-height: 1.6;
    }

    .auth-link {
        text-align: center;
        margin-top: 1rem;
        color: #666;
    }

    .auth-link button {
        background: none;
        border: none;
        color: #667eea;
        cursor: pointer;
        font-weight: 600;
        text-decoration: underline;
        font-family: inherit;
    }
</style>
