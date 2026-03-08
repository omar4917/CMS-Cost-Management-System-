import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlinePlus, HiOutlineSearch, HiOutlinePencil, HiOutlineTrash, HiOutlineEye } from 'react-icons/hi';
import { toast } from 'react-toastify';

const statusColors = {
    planning: 'badge-blue',
    active: 'badge-emerald',
    paused: 'badge-amber',
    completed: 'badge-purple',
    cancelled: 'badge-red',
};

export default function ProjectsPage() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editProject, setEditProject] = useState(null);
    const [form, setForm] = useState({
        name: '', description: '', location: '', type: 'residential',
        status: 'planning', startDate: '', estimatedEndDate: '', totalBudget: '',
        totalFloors: '', totalUnits: '', landArea: '', buildingArea: '',
    });
    const { format } = useCurrency();
    const navigate = useNavigate();

    useEffect(() => { loadProjects(); }, [search, statusFilter]);

    const loadProjects = async () => {
        try {
            const res = await projectAPI.getAll({ search, status: statusFilter || undefined });
            setProjects(res.data.projects || []);
        } catch (err) {
            toast.error('Failed to load projects');
        } finally {
            setLoading(false);
        }
    };

    const openCreate = () => {
        setEditProject(null);
        setForm({ name: '', description: '', location: '', type: 'residential', status: 'planning', startDate: '', estimatedEndDate: '', totalBudget: '', totalFloors: '', totalUnits: '', landArea: '', buildingArea: '' });
        setShowModal(true);
    };

    const openEdit = (p) => {
        setEditProject(p);
        setForm({
            name: p.name || '', description: p.description || '', location: p.location || '',
            type: p.type || 'residential', status: p.status || 'planning',
            startDate: p.startDate || '', estimatedEndDate: p.estimatedEndDate || '',
            totalBudget: p.totalBudget || '', totalFloors: p.totalFloors || '',
            totalUnits: p.totalUnits || '', landArea: p.landArea || '', buildingArea: p.buildingArea || '',
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editProject) {
                await projectAPI.update(editProject.id, form);
                toast.success('Project updated!');
            } else {
                await projectAPI.create(form);
                toast.success('Project created!');
            }
            setShowModal(false);
            loadProjects();
        } catch (err) {
            toast.error(err.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this project?')) return;
        try {
            await projectAPI.delete(id);
            toast.success('Project deleted');
            loadProjects();
        } catch (err) {
            toast.error('Delete failed');
        }
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Projects</h1>
                    <p className="page-subtitle">Manage your real estate projects</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-primary" onClick={openCreate}>
                        <HiOutlinePlus /> New Project
                    </button>
                </div>
            </div>

            <div className="search-bar">
                <div className="search-input-wrap">
                    <HiOutlineSearch className="search-icon" />
                    <input
                        className="search-input"
                        placeholder="Search projects..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="">All Status</option>
                    <option value="planning">Planning</option>
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>

            {projects.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Project Name</th>
                                <th>Location</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Budget</th>
                                <th>Progress</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {projects.map((p) => (
                                <tr key={p.id}>
                                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{p.location || '—'}</td>
                                    <td><span className="badge badge-gray">{p.type}</span></td>
                                    <td><span className={`badge ${statusColors[p.status] || 'badge-gray'}`}>{p.status}</span></td>
                                    <td>{format(p.totalBudget)}</td>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <div className="progress-bar" style={{ width: '80px' }}>
                                                <div className="progress-fill" style={{ width: `${p.progress || 0}%` }} />
                                            </div>
                                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{parseFloat(p.progress || 0).toFixed(0)}%</span>
                                        </div>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                                        {new Date(p.createdAt).toLocaleDateString()}
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
                                            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/projects/${p.id}`)}><HiOutlineEye /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => openEdit(p)}><HiOutlinePencil /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => handleDelete(p.id)} style={{ color: 'var(--accent-red)' }}><HiOutlineTrash /></button>
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
                    <h3>No Projects Yet</h3>
                    <p>Create your first real estate project to get started.</p>
                    <button className="btn btn-primary" onClick={openCreate} style={{ marginTop: '16px' }}>
                        <HiOutlinePlus /> Create Project
                    </button>
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
                        <div className="modal-header">
                            <h2>{editProject ? 'Edit Project' : 'New Project'}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Project Name *</label>
                                    <input className="form-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea className="form-textarea" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Location</label>
                                        <input className="form-input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Type</label>
                                        <select className="form-select" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                                            <option value="residential">Residential</option>
                                            <option value="commercial">Commercial</option>
                                            <option value="mixed">Mixed Use</option>
                                            <option value="industrial">Industrial</option>
                                            <option value="land_development">Land Development</option>
                                            <option value="renovation">Renovation</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Status</label>
                                        <select className="form-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                                            <option value="planning">Planning</option>
                                            <option value="active">Active</option>
                                            <option value="paused">Paused</option>
                                            <option value="completed">Completed</option>
                                            <option value="cancelled">Cancelled</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Total Budget</label>
                                        <input className="form-input" type="number" step="0.01" value={form.totalBudget} onChange={(e) => setForm({ ...form, totalBudget: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Start Date</label>
                                        <input className="form-input" type="date" value={form.startDate} onChange={(e) => setForm({ ...form, startDate: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Estimated End Date</label>
                                        <input className="form-input" type="date" value={form.estimatedEndDate} onChange={(e) => setForm({ ...form, estimatedEndDate: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Total Floors</label>
                                        <input className="form-input" type="number" value={form.totalFloors} onChange={(e) => setForm({ ...form, totalFloors: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Total Units</label>
                                        <input className="form-input" type="number" value={form.totalUnits} onChange={(e) => setForm({ ...form, totalUnits: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Land Area</label>
                                        <input className="form-input" value={form.landArea} onChange={(e) => setForm({ ...form, landArea: e.target.value })} placeholder="e.g., 5 katha" />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Building Area</label>
                                        <input className="form-input" value={form.buildingArea} onChange={(e) => setForm({ ...form, buildingArea: e.target.value })} placeholder="e.g., 10,000 sqft" />
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editProject ? 'Update' : 'Create'} Project</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
