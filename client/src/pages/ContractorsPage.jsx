import { useState, useEffect } from 'react';
import { contractorAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlinePlus, HiOutlineSearch, HiOutlinePencil, HiOutlineTrash, HiOutlineEye, HiOutlineStar } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function ContractorsPage() {
    const [contractors, setContractors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [showPaymentModal, setShowPaymentModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [selectedContractor, setSelectedContractor] = useState(null);
    const [payments, setPayments] = useState([]);
    const [form, setForm] = useState({
        name: '', email: '', phone: '', company: '', specialization: '',
        address: '', rating: 0, status: 'active',
    });
    const [payForm, setPayForm] = useState({
        amount: '', date: '', description: '', invoiceNo: '', paymentMethod: 'bank_transfer', status: 'pending',
    });
    const { format } = useCurrency();

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const res = await contractorAPI.getAll({ search: search || undefined });
            setContractors(res.data.contractors || []);
        } catch { toast.error('Failed to load contractors'); }
        finally { setLoading(false); }
    };

    useEffect(() => { if (search !== undefined) loadData(); }, [search]);

    const openCreate = () => {
        setEditItem(null);
        setForm({ name: '', email: '', phone: '', company: '', specialization: '', address: '', rating: 0, status: 'active' });
        setShowModal(true);
    };

    const openEdit = (c) => {
        setEditItem(c);
        setForm({
            name: c.name || '', email: c.email || '', phone: c.phone || '',
            company: c.company || '', specialization: c.specialization || '',
            address: c.address || '', rating: c.rating || 0, status: c.status || 'active',
        });
        setShowModal(true);
    };

    const viewPayments = async (c) => {
        try {
            setSelectedContractor(c);
            const res = await contractorAPI.getPayments(c.id);
            setPayments(res.data.payments || []);
            setShowPaymentModal(true);
        } catch { toast.error('Failed to load payments'); }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editItem) {
                await contractorAPI.update(editItem.id, form);
                toast.success('Contractor updated!');
            } else {
                await contractorAPI.create(form);
                toast.success('Contractor added!');
            }
            setShowModal(false);
            loadData();
        } catch (err) { toast.error(err.response?.data?.message || 'Failed'); }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this contractor?')) return;
        try { await contractorAPI.delete(id); toast.success('Deleted'); loadData(); }
        catch { toast.error('Delete failed'); }
    };

    const handleAddPayment = async (e) => {
        e.preventDefault();
        try {
            await contractorAPI.addPayment(selectedContractor.id, payForm);
            toast.success('Payment recorded!');
            const res = await contractorAPI.getPayments(selectedContractor.id);
            setPayments(res.data.payments || []);
            setPayForm({ amount: '', date: new Date().toISOString().split('T')[0], description: '', invoiceNo: '', paymentMethod: 'bank_transfer', status: 'pending' });
        } catch { toast.error('Failed to add payment'); }
    };

    const filtered = contractors.filter(c =>
        c.name?.toLowerCase().includes(search.toLowerCase()) ||
        c.company?.toLowerCase().includes(search.toLowerCase()) ||
        c.specialization?.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Contractors</h1>
                    <p className="page-subtitle">Manage vendors and contractor payments</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-primary" onClick={openCreate}><HiOutlinePlus /> Add Contractor</button>
                </div>
            </div>

            <div className="search-bar">
                <div className="search-input-wrap">
                    <HiOutlineSearch className="search-icon" />
                    <input className="search-input" placeholder="Search contractors..." value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
            </div>

            {filtered.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead><tr><th>Name</th><th>Company</th><th>Specialization</th><th>Phone</th><th>Rating</th><th>Status</th><th>Actions</th></tr></thead>
                        <tbody>
                            {filtered.map((c) => (
                                <tr key={c.id}>
                                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{c.company || '—'}</td>
                                    <td><span className="badge badge-blue">{c.specialization || 'General'}</span></td>
                                    <td>{c.phone || '—'}</td>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                                            {[1, 2, 3, 4, 5].map(star => (
                                                <HiOutlineStar key={star} style={{ color: star <= (c.rating || 0) ? '#f59e0b' : 'var(--text-muted)', fontSize: '14px', fill: star <= (c.rating || 0) ? '#f59e0b' : 'none' }} />
                                            ))}
                                        </div>
                                    </td>
                                    <td><span className={`badge ${c.status === 'active' ? 'badge-emerald' : 'badge-red'}`}>{c.status}</span></td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
                                            <button className="btn btn-secondary btn-sm" onClick={() => viewPayments(c)}><HiOutlineEye /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => openEdit(c)}><HiOutlinePencil /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => handleDelete(c.id)} style={{ color: 'var(--accent-red)' }}><HiOutlineTrash /></button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="empty-state">
                    <div className="empty-state-icon">🏗️</div>
                    <h3>No Contractors</h3>
                    <p>Add contractors and vendors to track payments.</p>
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{editItem ? 'Edit Contractor' : 'Add Contractor'}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Name *</label>
                                        <input className="form-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Company</label>
                                        <input className="form-input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
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
                                        <label className="form-label">Specialization</label>
                                        <input className="form-input" value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} placeholder="e.g., Plumbing, Electrical" />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Rating (1-5)</label>
                                        <input className="form-input" type="number" min="0" max="5" value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Address</label>
                                    <textarea className="form-textarea" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editItem ? 'Update' : 'Add'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Payment History Modal */}
            {showPaymentModal && selectedContractor && (
                <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px' }}>
                        <div className="modal-header">
                            <h2>{selectedContractor.name} — Payments</h2>
                            <button className="modal-close" onClick={() => setShowPaymentModal(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            {payments.length > 0 && (
                                <div className="table-container" style={{ marginBottom: '20px' }}>
                                    <table className="data-table">
                                        <thead><tr><th>Date</th><th>Amount</th><th>Invoice</th><th>Description</th><th>Status</th></tr></thead>
                                        <tbody>
                                            {payments.map(p => (
                                                <tr key={p.id}>
                                                    <td>{p.date ? new Date(p.date).toLocaleDateString() : '—'}</td>
                                                    <td style={{ fontWeight: 600 }}>{format(p.amount)}</td>
                                                    <td>{p.invoiceNo || '—'}</td>
                                                    <td style={{ color: 'var(--text-secondary)' }}>{p.description || '—'}</td>
                                                    <td><span className={`badge ${p.status === 'paid' ? 'badge-emerald' : 'badge-amber'}`}>{p.status}</span></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Add Payment</h3>
                            <form onSubmit={handleAddPayment}>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Amount *</label>
                                        <input className="form-input" type="number" step="0.01" value={payForm.amount} onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Date *</label>
                                        <input className="form-input" type="date" value={payForm.date} onChange={(e) => setPayForm({ ...payForm, date: e.target.value })} required />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Invoice No</label>
                                        <input className="form-input" value={payForm.invoiceNo} onChange={(e) => setPayForm({ ...payForm, invoiceNo: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Description</label>
                                        <input className="form-input" value={payForm.description} onChange={(e) => setPayForm({ ...payForm, description: e.target.value })} />
                                    </div>
                                </div>
                                <button type="submit" className="btn btn-primary"><HiOutlinePlus /> Add Payment</button>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
