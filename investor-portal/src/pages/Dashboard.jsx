import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
    BarChart3, Wallet, TrendingUp, Clock,
    ChevronRight, ArrowUpRight, ArrowDownRight,
    MapPin, Activity, Calendar
} from 'lucide-react';

const Dashboard = () => {
    const { user } = useAuth();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.get('/investor-portal/dashboard');
                setData(res.data);
            } catch (err) {
                console.error('Failed to fetch dashboard data', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return (
        <div className="flex-center" style={{ height: '80vh' }}>
            <div className="animate-spin" style={{ width: '40px', height: '40px', border: '4px solid var(--border-glass)', borderTopColor: 'var(--accent-primary)', borderRadius: '50%' }}></div>
        </div>
    );

    return (
        <div className="animate-fade-in" style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Header */}
            <header style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                    <h1 className="gradient-text" style={{ fontSize: '2.4rem', fontWeight: '800' }}>Welcome, {user.firstName}</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginTop: '4px' }}>
                        Portfolio overview for {data?.investor?.name}
                    </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.9rem' }}>Member since</div>
                    <div style={{ fontWeight: '600' }}>{new Date(data?.investor?.createdAt).toLocaleDateString()}</div>
                </div>
            </header>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '40px' }}>
                <div className="glass-card" style={{ padding: '30px' }}>
                    <div className="flex-center" style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-primary)', marginBottom: '20px' }}>
                        <TrendingUp size={24} />
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '4px' }}>Total Invested</div>
                    <div style={{ fontSize: '2rem', fontWeight: '800' }}>৳{data.summary.totalInvested.toLocaleString()}</div>
                </div>

                <div className="glass-card" style={{ padding: '30px' }}>
                    <div className="flex-center" style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', marginBottom: '20px' }}>
                        <Wallet size={24} />
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '4px' }}>Total Paid</div>
                    <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--success)' }}>৳{data.summary.totalPaid.toLocaleString()}</div>
                </div>

                <div className="glass-card" style={{ padding: '30px' }}>
                    <div className="flex-center" style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)', marginBottom: '20px' }}>
                        <Clock size={24} />
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '4px' }}>Outstanding Balance</div>
                    <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--warning)' }}>৳{data.summary.unpaid.toLocaleString()}</div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
                {/* Latest Investments */}
                <div className="glass-card" style={{ padding: '30px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                        <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Project Investments</h2>
                        <Activity size={20} color="var(--text-dim)" />
                    </div>
                    <div style={{ display: 'grid', gap: '16px' }}>
                        {data.latestInvestments.map(inv => (
                            <div key={inv.id} className="glass" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                                    <div style={{ width: '48px', height: '48px', borderRadius: '10px', background: 'var(--bg-main)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <BarChart3 size={20} color="var(--accent-primary)" />
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: '600' }}>{inv.project.name}</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(inv.date).toLocaleDateString()}</div>
                                    </div>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontWeight: '700', fontSize: '1.1rem' }}>৳{inv.amount.toLocaleString()}</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--success)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                                        <ArrowUpRight size={14} /> Confirmed
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Upcoming Payments */}
                <div className="glass-card" style={{ padding: '30px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                        <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Scheduled Returns</h2>
                        <Calendar size={20} color="var(--text-dim)" />
                    </div>
                    <div style={{ display: 'grid', gap: '16px' }}>
                        {data.upcomingPayments.map(pay => (
                            <div key={pay.id} style={{ display: 'flex', gap: '15px', paddingBottom: '16px', borderBottom: '1px solid var(--border-glass)' }}>
                                <div style={{
                                    minWidth: '50px', height: '50px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)',
                                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                                    border: '1px solid var(--border-glass)'
                                }}>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                                        {new Date(pay.dueDate).toLocaleString('default', { month: 'short' })}
                                    </span>
                                    <span style={{ fontWeight: '700' }}>{new Date(pay.dueDate).getDate()}</span>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.9rem', fontWeight: '600' }}>{pay.project.name}</div>
                                    <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>৳{pay.amount.toLocaleString()}</div>
                                    <div style={{
                                        fontSize: '0.7rem', marginTop: '4px', display: 'inline-block',
                                        padding: '2px 8px', borderRadius: '4px',
                                        background: pay.status === 'overdue' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                                        color: pay.status === 'overdue' ? 'var(--danger)' : 'var(--warning)'
                                    }}>
                                        {pay.status.toUpperCase()}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
