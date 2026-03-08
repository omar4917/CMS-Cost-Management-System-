import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LogIn, ShieldCheck, Mail, Lock, Loader2 } from 'lucide-react';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(username, password);
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.message || err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex-center animate-fade-in" style={{ minHeight: '100vh', padding: '20px' }}>
            <div className="glass-card" style={{ width: '100%', maxWidth: '420px', padding: '40px' }}>
                <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                    <div className="flex-center" style={{
                        width: '64px', height: '64px', borderRadius: '16px',
                        background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        margin: '0 auto 20px auto',
                        boxShadow: '0 0 30px var(--accent-glow)'
                    }}>
                        <ShieldCheck size={32} color="white" />
                    </div>
                    <h1 className="gradient-text" style={{ fontSize: '1.8rem', fontWeight: '800' }}>Investor Portal</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '8px' }}>
                        Secure read-only access to your real estate portfolio
                    </p>
                </div>

                {error && (
                    <div className="glass" style={{
                        padding: '12px', marginBottom: '25px',
                        borderColor: 'var(--danger)', color: 'var(--danger)',
                        fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px'
                    }}>
                        <span style={{ fontWeight: 'bold' }}>!</span> {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label className="input-label">Username</label>
                        <div style={{ position: 'relative' }}>
                            <LogIn size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                            <input
                                type="text"
                                className="input-field"
                                style={{ paddingLeft: '48px' }}
                                placeholder="Enter your username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label">Password</label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                            <input
                                type="password"
                                className="input-field"
                                style={{ paddingLeft: '48px' }}
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '10px' }} disabled={loading}>
                        {loading ? <Loader2 className="animate-spin" /> : 'Log In Securely'}
                    </button>
                </form>

                <div style={{ marginTop: '30px', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    Powered by CMS Real Estate v2.0
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
