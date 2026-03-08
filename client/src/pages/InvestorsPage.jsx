import { useState, useEffect } from 'react';
import { investorAPI, investorTypeAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlinePlus, HiOutlineSearch, HiOutlinePencil, HiOutlineTrash, HiOutlineEye } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function InvestorsPage() {
    const [investors, setInvestors] = useState([]);
    const [types, setTypes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [typeFilter, setTypeFilter] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editInvestor, setEditInvestor] = useState(null);
    const [selectedInvestor, setSelectedInvestor] = useState(null);
    const [form, setForm] = useState({
        name: '', email: '', phone: '', address: '', typeId: '',
        company: '', nationalId: '', bankAccount: '', bankName: '', notes: '',
    });
    const { format } = useCurrency();

    useEffect(() => { loadData(); }, [search, typeFilter]);

    const loadData = async () => {
        try {
            const [invRes, typeRes] = await Promise.all([
                investorAPI.getAll({ search, typeId: typeFilter || undefined }),
                investorTypeAPI.getAll(),
            ]);
            setInvestors(invRes.data.investors || []);
            setTypes(typeRes.data.types || []);
        } catch (err) {
            toast.error('Failed to load investors');
        } finally {
            setLoading(false);
        }
    };

    const openCreate = () => {
        setEditInvestor(null);
        setForm({ name: '', email: '', phone: '', address: '', typeId: types[0]?.id || '', company: '', nationalId: '', bankAccount: '', bankName: '', notes: '' });
        setShowModal(true);
    };

    const openEdit = (inv) => {
        setEditInvestor(inv);
        setForm({
            name: inv.name || '', email: inv.email || '', phone: inv.phone || '',
            address: inv.address || '', typeId: inv.typeId || '', company: inv.company || '',
            nationalId: inv.nationalId || '', bankAccount: inv.bankAccount || '',
            bankName: inv.bankName || '', notes: inv.notes || '',
        });
        setShowModal(true);
    };

    const viewInvestor = async (id) => {
        try {
            const res = await investorAPI.getById(id);
            setSelectedInvestor(res.data);
        } catch (err) {
            toast.error('Failed to load investor details');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editInvestor) {
                await investorAPI.update(editInvestor.id, form);
                toast.success('Investor updated!');
            } else {
                await investorAPI.create(form);
                toast.success('Investor created!');
            }
            setShowModal(false);
            loadData();
        } catch (err) {
            toast.error(err.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this investor?')) return;
        try {
            await investorAPI.delete(id);
            toast.success('Investor deleted');
            loadData();
        } catch (err) {
            toast.error('Delete failed');
        }
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Investors</h1>
                    <p className="page-subtitle">Manage investor profiles and track investments</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-primary" onClick={openCreate}><HiOutlinePlus /> Add Investor</button>
                </div>
            </div>

            <div className="search-bar">
                <div className="search-input-wrap">
                    <HiOutlineSearch className="search-icon" />
                    <input className="search-input" placeholder="Search investors..." value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
                <select className="filter-select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                    <option value="">All Types</option>
                    {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
            </div>

            {investors.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Type</th>
                                <th>Company</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {investors.map((inv) => (
                                <tr key={inv.id}>
                                    <td style={{ fontWeight: 500 }}>{inv.name}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{inv.email || '—'}</td>
                                    <td>{inv.phone || '—'}</td>
                                    <td>
                                        <span className="badge" style={{
                                            background: `${inv.type?.color || '#3b82f6'}20`,
                                            color: inv.type?.color || '#3b82f6',
                                        }}>
                                            {inv.type?.name || 'N/A'}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{inv.company || '—'}</td>
                                    <td>
                                        <span className={`badge ${inv.isActive ? 'badge-emerald' : 'badge-red'}`}>
                                            {inv.isActive ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
                                            <button className="btn btn-secondary btn-sm" onClick={() => viewInvestor(inv.id)}><HiOutlineEye /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => openEdit(inv)}><HiOutlinePencil /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => handleDelete(inv.id)} style={{ color: 'var(--accent-red)' }}><HiOutlineTrash /></button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="empty-state">
                    <div className="empty-state-icon">👥</div>
                    <h3>No Investors Yet</h3>
                    <p>Add your first investor to start tracking investments.</p>
                    <button className="btn btn-primary" onClick={openCreate} style={{ marginTop: '16px' }}><HiOutlinePlus /> Add Investor</button>
                </div>
            )}

            {/* Investor Detail Modal */}
            {selectedInvestor && (
                <div className="modal-overlay" onClick={() => setSelectedInvestor(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '750px' }}>
                        <div className="modal-header">
                            <h2>{selectedInvestor.investor?.name} — Financial Summary</h2>
                            <button className="modal-close" onClick={() => setSelectedInvestor(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                                <div className="stat-card emerald" style={{ padding: '16px' }}>
                                    <div className="stat-value" style={{ fontSize: '20px' }}>{format(selectedInvestor.summary?.totalInvested)}</div>
                                    <div className="stat-label">Total Invested</div>
                                </div>
                                <div className="stat-card blue" style={{ padding: '16px' }}>
                                    <div className="stat-value" style={{ fontSize: '20px' }}>{format(selectedInvestor.summary?.totalPaid)}</div>
                                    <div className="stat-label">Paid</div>
                                </div>
                                <div className="stat-card red" style={{ padding: '16px' }}>
                                    <div className="stat-value" style={{ fontSize: '20px' }}>{format(selectedInvestor.summary?.unpaid)}</div>
                                    <div className="stat-label">Unpaid / Due</div>
                                </div>
                            </div>

                            {selectedInvestor.investments?.length > 0 && (
                                <>
                                    <h3 style={{ fontSize: '15px', fontWeight: 600, margin: '20px 0 12px' }}>Investment History</h3>
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead><tr><th>Project</th><th>Amount</th><th>Date</th><th>Method</th></tr></thead>
                                            <tbody>
                                                {selectedInvestor.investments.map(inv => (
                                                    <tr key={inv.id}>
                                                        <td>{inv.project?.name}</td>
                                                        <td>{format(inv.amount)}</td>
                                                        <td>{new Date(inv.date).toLocaleDateString()}</td>
                                                        <td><span className="badge badge-gray">{inv.paymentMethod}</span></td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '650px' }}>
                        <div className="modal-header">
                            <h2>{editInvestor ? 'Edit Investor' : 'Add Investor'}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Full Name *</label>
                                        <input className="form-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Investor Type</label>
                                        <select className="form-select" value={form.typeId} onChange={(e) => setForm({ ...form, typeId: e.target.value })}>
                                            <option value="">Select Type</option>
                                            {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Email</label>
                                        <input className="form-input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Phone</label>
                                        <input className="form-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Company</label>
                                        <input className="form-input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">National ID</label>
                                        <input className="form-input" value={form.nationalId} onChange={(e) => setForm({ ...form, nationalId: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Bank Name</label>
                                        <input className="form-input" value={form.bankName} onChange={(e) => setForm({ ...form, bankName: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Bank Account</label>
                                        <input className="form-input" value={form.bankAccount} onChange={(e) => setForm({ ...form, bankAccount: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Address</label>
                                    <textarea className="form-textarea" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Notes</label>
                                    <textarea className="form-textarea" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editInvestor ? 'Update' : 'Add'} Investor</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
