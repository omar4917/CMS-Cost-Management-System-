import { useState, useEffect } from 'react';
import { settingsAPI, currencyAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlineSave } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function SettingsPage() {
    const [settings, setSettings] = useState({});
    const [currencies, setCurrencies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('general');
    const { format } = useCurrency();

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [settRes, currRes] = await Promise.all([
                settingsAPI.getAll(),
                currencyAPI.getAll(),
            ]);
            const map = {};
            (settRes.data.settings || []).forEach(s => { map[s.key] = s.value; });
            setSettings(map);
            setCurrencies(currRes.data.currencies || []);
        } catch { toast.error('Failed to load settings'); }
        finally { setLoading(false); }
    };

    const updateSetting = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const saveSetting = async (key) => {
        try {
            await settingsAPI.update({ key, value: settings[key] });
            toast.success(`${key.replace(/_/g, ' ')} updated!`);
        } catch { toast.error('Save failed'); }
    };

    const updateCurrencyRate = async (curr) => {
        try {
            await currencyAPI.update(curr.id, { exchangeRateToBase: curr.exchangeRateToBase });
            toast.success(`${curr.code} rate updated!`);
        } catch { toast.error('Update failed'); }
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Settings</h1>
                    <p className="page-subtitle">Configure application settings</p>
                </div>
            </div>

            <div className="tabs">
                <button className={`tab ${tab === 'general' ? 'active' : ''}`} onClick={() => setTab('general')}>General</button>
                <button className={`tab ${tab === 'financial' ? 'active' : ''}`} onClick={() => setTab('financial')}>Financial</button>
                <button className={`tab ${tab === 'email' ? 'active' : ''}`} onClick={() => setTab('email')}>Email</button>
                <button className={`tab ${tab === 'currencies' ? 'active' : ''}`} onClick={() => setTab('currencies')}>Currencies</button>
            </div>

            {tab === 'general' && (
                <div className="card">
                    {['company_name', 'company_email', 'company_phone', 'company_address'].map(key => (
                        <div className="form-group" key={key}>
                            <label className="form-label">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</label>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <input className="form-input" value={settings[key] || ''} onChange={(e) => updateSetting(key, e.target.value)} />
                                <button className="btn btn-primary btn-sm" onClick={() => saveSetting(key)}><HiOutlineSave /></button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {tab === 'financial' && (
                <div className="card">
                    {['base_currency', 'tax_rate', 'fiscal_year_start'].map(key => (
                        <div className="form-group" key={key}>
                            <label className="form-label">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</label>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <input className="form-input" value={settings[key] || ''} onChange={(e) => updateSetting(key, e.target.value)} />
                                <button className="btn btn-primary btn-sm" onClick={() => saveSetting(key)}><HiOutlineSave /></button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {tab === 'email' && (
                <div className="card">
                    {['email_notifications', 'auto_email_on_investment', 'payment_reminder_days'].map(key => (
                        <div className="form-group" key={key}>
                            <label className="form-label">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</label>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <input className="form-input" value={settings[key] || ''} onChange={(e) => updateSetting(key, e.target.value)} />
                                <button className="btn btn-primary btn-sm" onClick={() => saveSetting(key)}><HiOutlineSave /></button>
                            </div>
                        </div>
                    ))}
                    <div style={{ padding: '16px', background: 'rgba(59,130,246,0.08)', borderRadius: '8px', marginTop: '16px' }}>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                            <strong>Gmail SMTP Setup:</strong> Configure Gmail credentials in the server <code>.env</code> file:
                            <br />GMAIL_USER=your-email@gmail.com
                            <br />GMAIL_APP_PASSWORD=your-app-password
                        </p>
                    </div>
                </div>
            )}

            {tab === 'currencies' && (
                <div className="card">
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                        Exchange rates are relative to the base currency (BDT). Adjust rates to reflect current market values.
                    </p>
                    <div className="table-container">
                        <table className="data-table">
                            <thead><tr><th>Currency</th><th>Symbol</th><th>Rate (to BDT)</th><th>Base</th><th>Actions</th></tr></thead>
                            <tbody>
                                {currencies.map(c => (
                                    <tr key={c.id}>
                                        <td style={{ fontWeight: 500 }}>{c.code} — {c.name}</td>
                                        <td>{c.symbol}</td>
                                        <td>
                                            <input
                                                className="form-input"
                                                type="number"
                                                step="0.000001"
                                                style={{ width: '140px' }}
                                                value={c.exchangeRateToBase}
                                                onChange={(e) => {
                                                    const updated = currencies.map(cur => cur.id === c.id ? { ...cur, exchangeRateToBase: e.target.value } : cur);
                                                    setCurrencies(updated);
                                                }}
                                            />
                                        </td>
                                        <td>{c.isBase ? <span className="badge badge-emerald">Base</span> : ''}</td>
                                        <td>
                                            <button className="btn btn-primary btn-sm" onClick={() => updateCurrencyRate(c)}><HiOutlineSave /> Save</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
