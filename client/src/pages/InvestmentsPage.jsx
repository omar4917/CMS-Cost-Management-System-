import { useState, useEffect } from 'react';
import { investmentAPI, projectAPI, investorAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlinePlus, HiOutlineSearch, HiOutlinePencil, HiOutlineTrash } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function InvestmentsPage() {
    const [investments, setInvestments] = useState([]);
    const [projects, setProjects] = useState([]);
    const [investors, setInvestors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({
        investorId: '', projectId: '', amount: '', date: '',
        paymentMethod: 'bank_transfer', referenceNo: '', description: '', status: 'confirmed',
    });
    const { format } = useCurrency();

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [invRes, projRes, investorRes] = await Promise.all([
                investmentAPI.getAll(),
                projectAPI.getAll(),
                investorAPI.getAll(),
            ]);
            setInvestments(invRes.data.investments || []);
            setProjects(projRes.data.projects || []);
            setInvestors(investorRes.data.investors || []);
        } catch (err) { toast.error('Failed to load data'); }
        finally { setLoading(false); }
    };

    const openCreate = () => {
        setEditItem(null);
        setForm({ investorId: '', projectId: '', amount: '', date: new Date().toISOString().split('T')[0], paymentMethod: 'bank_transfer', referenceNo: '', description: '', status: 'confirmed' });
        setShowModal(true);
    };

    const openEdit = (item) => {
        setEditItem(item);
        setForm({
            investorId: item.investorId || '', projectId: item.projectId || '',
            amount: item.amount || '', date: item.date?.split('T')[0] || '',
            paymentMethod: item.paymentMethod || 'bank_transfer',
            referenceNo: item.referenceNo || '', description: item.description || '',
            status: item.status || 'confirmed',
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editItem) {
                await investmentAPI.update(editItem.id, form);
                toast.success('Investment updated!');
            } else {
                await investmentAPI.create(form);
                toast.success('Investment recorded!');
            }
            setShowModal(false);
            loadData();
        } catch (err) { toast.error(err.response?.data?.message || 'Operation failed'); }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this investment record?')) return;
        try { await investmentAPI.delete(id); toast.success('Deleted'); loadData(); }
        catch { toast.error('Delete failed'); }
    };

    const filtered = investments.filter(i =>
        i.investor?.name?.toLowerCase().includes(search.toLowerCase()) ||
        i.project?.name?.toLowerCase().includes(search.toLowerCase()) ||
        i.referenceNo?.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Investments</h1>
                    <p className="page-subtitle">Track all investment transactions</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-primary" onClick={openCreate}><HiOutlinePlus /> Record Investment</button>
                </div>
            </div>

            <div className="search-bar">
                <div className="search-input-wrap">
                    <HiOutlineSearch className="search-icon" />
                    <input className="search-input" placeholder="Search by investor, project, or reference..." value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
            </div>

            {filtered.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Investor</th>
                                <th>Project</th>
                                <th>Amount</th>
                                <th>Date</th>
                                <th>Method</th>
                                <th>Reference</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((inv) => (
                                <tr key={inv.id}>
                                    <td style={{ fontWeight: 500 }}>{inv.investor?.name || '—'}</td>
                                    <td>{inv.project?.name || '—'}</td>
                                    <td style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>{format(inv.amount)}</td>
                                    <td>{inv.date ? new Date(inv.date).toLocaleDateString() : '—'}</td>
                                    <td><span className="badge badge-gray">{inv.paymentMethod?.replace('_', ' ')}</span></td>
                                    <td style={{ color: 'var(--text-muted)' }}>{inv.referenceNo || '—'}</td>
                                    <td>
                                        <span className={`badge ${inv.status === 'confirmed' ? 'badge-emerald' : inv.status === 'pending' ? 'badge-amber' : 'badge-red'}`}>
                                            {inv.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
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
                    <div className="empty-state-icon">💰</div>
                    <h3>No Investments Yet</h3>
                    <p>Record your first investment transaction.</p>
                    <button className="btn btn-primary" onClick={openCreate} style={{ marginTop: '16px' }}><HiOutlinePlus /> Record Investment</button>
                </div>
            )}

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '650px' }}>
                        <div className="modal-header">
                            <h2>{editItem ? 'Edit Investment' : 'Record Investment'}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Investor *</label>
                                        <select className="form-select" value={form.investorId} onChange={(e) => setForm({ ...form, investorId: e.target.value })} required>
                                            <option value="">Select Investor</option>
                                            {investors.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Project *</label>
                                        <select className="form-select" value={form.projectId} onChange={(e) => setForm({ ...form, projectId: e.target.value })} required>
                                            <option value="">Select Project</option>
                                            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Amount *</label>
                                        <input className="form-input" type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Date *</label>
                                        <input className="form-input" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Payment Method</label>
                                        <select className="form-select" value={form.paymentMethod} onChange={(e) => setForm({ ...form, paymentMethod: e.target.value })}>
                                            <option value="bank_transfer">Bank Transfer</option>
                                            <option value="cash">Cash</option>
                                            <option value="cheque">Cheque</option>
                                            <option value="mobile_banking">Mobile Banking</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Reference No</label>
                                        <input className="form-input" value={form.referenceNo} onChange={(e) => setForm({ ...form, referenceNo: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Status</label>
                                        <select className="form-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                                            <option value="pending">Pending</option>
                                            <option value="confirmed">Confirmed</option>
                                            <option value="cancelled">Cancelled</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Description</label>
                                        <input className="form-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editItem ? 'Update' : 'Record'} Investment</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
