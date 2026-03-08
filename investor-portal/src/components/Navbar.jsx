import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, BarChart2, LayoutDashboard } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
    const { user, logout } = useAuth();
    const location = useLocation();

    if (!user) return null;

    return (
        <nav className="glass" style={{ margin: '20px 40px', padding: '12px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '40px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>C</div>
                    <span style={{ fontWeight: '800', letterSpacing: '1px' }}>CMS <span style={{ color: 'var(--text-muted)', fontWeight: '400' }}>PORTAL</span></span>
                </div>

                <div style={{ display: 'flex', gap: '25px' }}>
                    <Link to="/" style={{
                        textDecoration: 'none', color: location.pathname === '/' ? 'var(--accent-primary)' : 'var(--text-muted)',
                        fontSize: '0.9rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px'
                    }}>
                        <LayoutDashboard size={18} /> Dashboard
                    </Link>
                    <Link to="/investments" style={{
                        textDecoration: 'none', color: location.pathname === '/investments' ? 'var(--accent-primary)' : 'var(--text-muted)',
                        fontSize: '0.9rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px'
                    }}>
                        <BarChart2 size={18} /> My Portfolio
                    </Link>
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: '600' }}>{user.firstName} {user.lastName}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Investor ID: {user.investorId}</div>
                </div>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--bg-glass)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-glass)' }}>
                    <User size={20} color="var(--text-muted)" />
                </div>
                <button onClick={logout} className="btn-ghost" style={{ padding: '8px', borderRadius: '10px' }} title="Logout">
                    <LogOut size={18} />
                </button>
            </div>
        </nav>
    );
};

export default Navbar;
