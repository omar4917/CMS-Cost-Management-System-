import { useState, useEffect } from 'react';
import { costCategoryAPI } from '../services/api';
import { HiOutlinePlus, HiOutlinePencil } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function CostCategoriesPage() {
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({ name: '', description: '', icon: '', sortOrder: '' });

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const res = await costCategoryAPI.getAll();
            setCategories(res.data.categories || []);
        } catch { toast.error('Failed to load categories'); }
        finally { setLoading(false); }
    };

    const openCreate = () => {
        setEditItem(null);
        setForm({ name: '', description: '', icon: '📦', sortOrder: categories.length + 1 });
        setShowModal(true);
    };

    const openEdit = (cat) => {
        setEditItem(cat);
        setForm({ name: cat.name, description: cat.description || '', icon: cat.icon || '', sortOrder: cat.sortOrder || '' });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editItem) {
                await costCategoryAPI.update(editItem.id, form);
                toast.success('Category updated!');
            } else {
                await costCategoryAPI.create(form);
                toast.success('Category created!');
            }
            setShowModal(false);
            loadData();
        } catch (err) { toast.error(err.response?.data?.message || 'Failed'); }
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Cost Categories</h1>
                    <p className="page-subtitle">Organize project expenses into categories</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-primary" onClick={openCreate}><HiOutlinePlus /> Add Category</button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                {categories.map((cat) => (
                    <div key={cat.id} className="card" style={{ cursor: 'pointer', position: 'relative' }} onClick={() => openEdit(cat)}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontSize: '28px' }}>{cat.icon || '📦'}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text-white)' }}>{cat.name}</div>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{cat.description}</div>
                            </div>
                            <button className="btn btn-secondary btn-sm" onClick={(e) => { e.stopPropagation(); openEdit(cat); }}>
                                <HiOutlinePencil />
                            </button>
                        </div>
                        {cat.isDefault && (
                            <span className="badge badge-blue" style={{ position: 'absolute', top: '10px', right: '10px', fontSize: '10px' }}>Default</span>
                        )}
                    </div>
                ))}
            </div>

            {categories.length === 0 && (
                <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <h3>No Categories</h3>
                    <p>Add cost categories to organize your expenses.</p>
                </div>
            )}

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{editItem ? 'Edit Category' : 'New Category'}</h2>
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
                                        <label className="form-label">Icon (emoji)</label>
                                        <input className="form-input" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} placeholder="e.g. 🏗️" />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea className="form-textarea" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Sort Order</label>
                                    <input className="form-input" type="number" value={form.sortOrder} onChange={(e) => setForm({ ...form, sortOrder: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editItem ? 'Update' : 'Create'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
