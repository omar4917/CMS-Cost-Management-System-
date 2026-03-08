import React, { useState, useEffect } from 'react';
import api from '../api';
import {
    Building2, MapPin, Target, Landmark,
    ArrowRight, ShieldCheck, PieChart, FileText
} from 'lucide-react';

const ProjectPortfolio = () => {
    const [investments, setInvestments] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.get('/investor-portal/investments');
                setInvestments(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return null;

    return (
        <div className="animate-fade-in" style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
            <header style={{ marginBottom: '40px' }}>
                <h1 className="gradient-text" style={{ fontSize: '2rem', fontWeight: '800' }}>Investment Portfolio</h1>
                <p style={{ color: 'var(--text-muted)' }}>Detailed breakdown of your real estate asset holdings</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '30px' }}>
                {investments.map(inv => (
                    <div key={inv.id} className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
                        <div style={{
                            height: '10px',
                            background: inv.project.status === 'active' ? 'var(--accent-primary)' : 'var(--text-dim)',
                            width: '100%'
                        }}></div>

                        <div style={{ padding: '30px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '4px' }}>{inv.project.name}</h3>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                        <MapPin size={14} /> {inv.project.location}
                                    </div>
                                </div>
                                <div style={{
                                    padding: '4px 12px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '700',
                                    background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-primary)',
                                    border: '1px solid var(--border-glass)'
                                }}>
                                    {inv.project.status.toUpperCase()}
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '25px' }}>
                                <div className="glass" style={{ padding: '15px' }}>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Your Stake</div>
                                    <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>৳{inv.amount.toLocaleString()}</div>
                                </div>
                                <div className="glass" style={{ padding: '15px' }}>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase' }}>Completion</div>
                                    <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>{inv.project.progress}%</div>
                                </div>
                            </div>

                            {/* Progress Bar */}
                            <div style={{ marginBottom: '25px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                    <span>Project Progress</span>
                                    <span>{inv.project.progress}%</span>
                                </div>
                                <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%', width: `${inv.project.progress}%`,
                                        background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
                                        boxShadow: '0 0 10px var(--accent-glow)'
                                    }}></div>
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '15px' }}>
                                <button className="btn-primary" style={{ flex: 1, padding: '10px' }}>
                                    <FileText size={18} /> View Statement
                                </button>
                                <button className="btn-ghost" style={{ flex: 1, padding: '10px' }}>
                                    Details <ChevronRight size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}

                {investments.length === 0 && (
                    <div className="glass-card flex-center" style={{ padding: '60px', gridColumn: '1 / -1', flexDirection: 'column', gap: '20px' }}>
                        <Target size={48} color="var(--text-dim)" />
                        <p style={{ color: 'var(--text-muted)' }}>No investments found in your portfolio yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProjectPortfolio;
