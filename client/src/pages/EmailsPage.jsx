import { useState, useEffect } from 'react';
import { emailAPI } from '../services/api';
import { HiOutlineMail, HiOutlinePaperAirplane, HiOutlineTemplate, HiOutlineClock, HiOutlineLightningBolt } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function EmailsPage() {
    const [tab, setTab] = useState('send');
    const [templates, setTemplates] = useState([]);
    const [logs, setLogs] = useState([]);
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sendForm, setSendForm] = useState({ to: '', subject: '', body: '', templateId: '' });
    const [sending, setSending] = useState(false);

    useEffect(() => { loadData(); }, [tab]);

    const loadData = async () => {
        setLoading(true);
        try {
            if (tab === 'templates' || tab === 'send') {
                const res = await emailAPI.getTemplates();
                setTemplates(res.data.templates || []);
            }
            if (tab === 'logs') {
                const res = await emailAPI.getLogs();
                setLogs(res.data.logs || []);
            }
            if (tab === 'automation') {
                const res = await emailAPI.getAutomationRules();
                setRules(res.data.rules || []);
            }
        } catch { /* API might not be fully ready */ }
        finally { setLoading(false); }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        setSending(true);
        try {
            await emailAPI.send(sendForm);
            toast.success('Email sent!');
            setSendForm({ to: '', subject: '', body: '', templateId: '' });
        } catch (err) { toast.error(err.response?.data?.message || 'Send failed — configure Gmail SMTP in .env'); }
        finally { setSending(false); }
    };

    const selectTemplate = (t) => {
        setSendForm({ ...sendForm, subject: t.subject, body: t.bodyHtml, templateId: t.id });
        setTab('send');
    };

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Email System</h1>
                    <p className="page-subtitle">Send emails, manage templates, and automation rules</p>
                </div>
            </div>

            <div className="tabs">
                <button className={`tab ${tab === 'send' ? 'active' : ''}`} onClick={() => setTab('send')}>
                    <HiOutlinePaperAirplane style={{ marginRight: '6px' }} /> Compose
                </button>
                <button className={`tab ${tab === 'templates' ? 'active' : ''}`} onClick={() => setTab('templates')}>
                    <HiOutlineTemplate style={{ marginRight: '6px' }} /> Templates
                </button>
                <button className={`tab ${tab === 'logs' ? 'active' : ''}`} onClick={() => setTab('logs')}>
                    <HiOutlineClock style={{ marginRight: '6px' }} /> Sent Logs
                </button>
                <button className={`tab ${tab === 'automation' ? 'active' : ''}`} onClick={() => setTab('automation')}>
                    <HiOutlineLightningBolt style={{ marginRight: '6px' }} /> Automation
                </button>
            </div>

            {/* Compose Tab */}
            {tab === 'send' && (
                <div className="card">
                    <form onSubmit={handleSend}>
                        <div className="form-group">
                            <label className="form-label">To (email addresses, comma separated) *</label>
                            <input className="form-input" type="text" value={sendForm.to} onChange={(e) => setSendForm({ ...sendForm, to: e.target.value })} placeholder="investor@email.com, owner@company.com" required />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Subject *</label>
                            <input className="form-input" value={sendForm.subject} onChange={(e) => setSendForm({ ...sendForm, subject: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Body (HTML supported)</label>
                            <textarea className="form-textarea" style={{ minHeight: '200px' }} value={sendForm.body} onChange={(e) => setSendForm({ ...sendForm, body: e.target.value })} />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={sending}>
                            <HiOutlinePaperAirplane /> {sending ? 'Sending...' : 'Send Email'}
                        </button>
                    </form>
                </div>
            )}

            {/* Templates Tab */}
            {tab === 'templates' && (
                <div style={{ display: 'grid', gap: '16px' }}>
                    {templates.map(t => (
                        <div key={t.id} className="card" style={{ cursor: 'pointer' }} onClick={() => selectTemplate(t)}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text-white)' }}>{t.name}</div>
                                    <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>Subject: {t.subject}</div>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                        Trigger: <span className="badge badge-blue">{t.triggerType?.replace(/_/g, ' ')}</span>
                                        {t.variables?.length > 0 && <span style={{ marginLeft: '8px' }}>Variables: {(Array.isArray(t.variables) ? t.variables : JSON.parse(t.variables || '[]')).join(', ')}</span>}
                                    </div>
                                </div>
                                <span className={`badge ${t.isActive ? 'badge-emerald' : 'badge-red'}`}>{t.isActive ? 'Active' : 'Inactive'}</span>
                            </div>
                        </div>
                    ))}
                    {templates.length === 0 && <div className="empty-state"><p>No email templates configured.</p></div>}
                </div>
            )}

            {/* Logs Tab */}
            {tab === 'logs' && (
                logs.length > 0 ? (
                    <div className="table-container">
                        <table className="data-table">
                            <thead><tr><th>To</th><th>Subject</th><th>Status</th><th>Sent At</th></tr></thead>
                            <tbody>
                                {logs.map(l => (
                                    <tr key={l.id}>
                                        <td>{l.recipientEmail}</td>
                                        <td>{l.subject}</td>
                                        <td><span className={`badge ${l.status === 'sent' ? 'badge-emerald' : 'badge-red'}`}>{l.status}</span></td>
                                        <td style={{ color: 'var(--text-muted)' }}>{new Date(l.createdAt).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : <div className="empty-state"><div className="empty-state-icon">📧</div><h3>No Emails Sent</h3><p>Sent email logs will appear here.</p></div>
            )}

            {/* Automation Tab */}
            {tab === 'automation' && (
                rules.length > 0 ? (
                    <div style={{ display: 'grid', gap: '12px' }}>
                        {rules.map(r => (
                            <div key={r.id} className="card">
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{r.name}</div>
                                        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                            Event: <span className="badge badge-purple">{r.triggerEvent?.replace(/_/g, ' ')}</span>
                                        </div>
                                    </div>
                                    <span className={`badge ${r.isActive ? 'badge-emerald' : 'badge-red'}`}>{r.isActive ? 'Active' : 'Disabled'}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="empty-state">
                        <div className="empty-state-icon">⚡</div>
                        <h3>No Automation Rules</h3>
                        <p>Automation rules will send emails automatically when events occur (e.g., new investment, milestone reached).</p>
                    </div>
                )
            )}
        </div>
    );
}
