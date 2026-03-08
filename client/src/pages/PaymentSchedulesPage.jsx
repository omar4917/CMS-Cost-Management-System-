import { useState, useEffect } from 'react';
import { paymentScheduleAPI, investorAPI, projectAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlinePlus, HiOutlineSearch, HiOutlinePencil, HiOutlineCheck, HiOutlineExclamation } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function PaymentSchedulesPage() {
    const [schedules, setSchedules] = useState([]);
    const [investors, setInvestors] = useState([]);
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({
        investorId: '', projectId: '', amount: '', dueDate: '',
        installmentNumber: '', description: '', status: 'pending',
    });
    const { format } = useCurrency();

    useEffect(() => { loadData(); }, [statusFilter]);

    const loadData = async () => {
        try {
            const [schedRes, invRes, projRes] = await Promise.all([
                paymentScheduleAPI.getAll({ status: statusFilter || undefined }),
                investorAPI.getAll(),
                projectAPI.getAll(),
            ]);
            setSchedules(schedRes.data.schedules || []);
            setInvestors(invRes.data.investors || []);
            setProjects(projRes.data.projects || []);
        } catch (err) { toast.error('Failed to load data'); }
        finally { setLoading(false); }
    };

    const openCreate = () => {
        setEditItem(null);
        setForm({ investorId: '', projectId: '', amount: '', dueDate: '', installmentNumber: '', description: '', status: 'pending' });
        setShowModal(true);
    };

    const openEdit = (item) => {
        setEditItem(item);
        setForm({
            investorId: item.investorId || '', projectId: item.projectId || '',
            amount: item.amount || '', dueDate: item.dueDate?.split('T')[0] || '',
            installmentNumber: item.installmentNumber || '', description: item.description || '',
            status: item.status || 'pending',
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editItem) {
                await paymentScheduleAPI.update(editItem.id, form);
                toast.success('Schedule updated!');
            } else {
                await paymentScheduleAPI.create(form);
                toast.success('Schedule created!');
            }
            setShowModal(false);
            loadData();
        } catch (err) { toast.error(err.response?.data?.message || 'Operation failed'); }
    };

    const markPaid = async (item) => {
        try {
            await paymentScheduleAPI.update(item.id, { ...item, status: 'paid', paidDate: new Date().toISOString().split('T')[0] });
            toast.success('Marked as paid!');
            loadData();
        } catch { toast.error('Update failed'); }
    };

    const isOverdue = (dueDate, status) => {
        if (status === 'paid') return false;
        return new Date(dueDate) < new Date();
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Payment Schedules</h1>
                    <p className="page-subtitle">Track investor installments and due dates</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-primary" onClick={openCreate}><HiOutlinePlus /> Add Schedule</button>
                </div>
            </div>

            <div className="search-bar">
                <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="paid">Paid</option>
                    <option value="overdue">Overdue</option>
                    <option value="partial">Partial</option>
                </select>
            </div>

            {schedules.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Investor</th>
                                <th>Project</th>
                                <th>Amount</th>
                                <th>Due Date</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {schedules.map((s) => (
                                <tr key={s.id} style={isOverdue(s.dueDate, s.status) ? { background: 'rgba(239,68,68,0.05)' } : {}}>
                                    <td style={{ color: 'var(--text-muted)' }}>{s.installmentNumber || '—'}</td>
                                    <td style={{ fontWeight: 500 }}>{s.investor?.name || '—'}</td>
                                    <td>{s.project?.name || '—'}</td>
                                    <td style={{ fontWeight: 600 }}>{format(s.amount)}</td>
                                    <td>
                                        <span style={{ color: isOverdue(s.dueDate, s.status) ? 'var(--accent-red)' : 'var(--text-primary)' }}>
                                            {s.dueDate ? new Date(s.dueDate).toLocaleDateString() : '—'}
                                        </span>
                                        {isOverdue(s.dueDate, s.status) && <HiOutlineExclamation style={{ color: 'var(--accent-red)', marginLeft: '4px' }} />}
                                    </td>
                                    <td>
                                        <span className={`badge ${s.status === 'paid' ? 'badge-emerald' : s.status === 'overdue' ? 'badge-red' : s.status === 'partial' ? 'badge-amber' : 'badge-blue'}`}>
                                            {s.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
                                            {s.status !== 'paid' && (
                                                <button className="btn btn-success btn-sm" onClick={() => markPaid(s)} title="Mark Paid"><HiOutlineCheck /></button>
                                            )}
                                            <button className="btn btn-secondary btn-sm" onClick={() => openEdit(s)}><HiOutlinePencil /></button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="empty-state">
                    <div className="empty-state-icon">📅</div>
                    <h3>No Payment Schedules</h3>
                    <p>Create payment schedules to track investor installments.</p>
                    <button className="btn btn-primary" onClick={openCreate} style={{ marginTop: '16px' }}><HiOutlinePlus /> Add Schedule</button>
                </div>
            )}

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{editItem ? 'Edit Schedule' : 'New Payment Schedule'}</h2>
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
                                        <label className="form-label">Due Date *</label>
                                        <input className="form-input" type="date" value={form.dueDate} onChange={(e) => setForm({ ...form, dueDate: e.target.value })} required />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Installment #</label>
                                        <input className="form-input" type="number" value={form.installmentNumber} onChange={(e) => setForm({ ...form, installmentNumber: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Status</label>
                                        <select className="form-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                                            <option value="pending">Pending</option>
                                            <option value="paid">Paid</option>
                                            <option value="overdue">Overdue</option>
                                            <option value="partial">Partial</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <input className="form-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editItem ? 'Update' : 'Create'} Schedule</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
