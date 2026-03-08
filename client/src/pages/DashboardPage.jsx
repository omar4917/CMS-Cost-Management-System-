import { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';
import {
    HiOutlineOfficeBuilding, HiOutlineCash, HiOutlineUserGroup,
    HiOutlineTrendingUp, HiOutlineTrendingDown, HiOutlineClock,
    HiOutlineExclamation, HiOutlineCheckCircle,
} from 'react-icons/hi';
import {
    PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, LineChart, Line, CartesianGrid, Legend,
} from 'recharts';

const CHART_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#6366f1', '#f43f5e'];

export default function DashboardPage() {
    const [summary, setSummary] = useState(null);
    const [projectProgress, setProjectProgress] = useState([]);
    const [costBreakdown, setCostBreakdown] = useState([]);
    const [investmentOverview, setInvestmentOverview] = useState({ byType: [], recentInvestments: [] });
    const [upcomingPayments, setUpcomingPayments] = useState([]);
    const [recentActivity, setRecentActivity] = useState([]);
    const [loading, setLoading] = useState(true);
    const { format } = useCurrency();

    useEffect(() => {
        loadDashboard();
    }, []);

    const loadDashboard = async () => {
        try {
            const [summaryRes, progressRes, costRes, investRes, paymentRes, activityRes] = await Promise.all([
                dashboardAPI.getSummary(),
                dashboardAPI.getProjectProgress(),
                dashboardAPI.getCostBreakdown(),
                dashboardAPI.getInvestmentOverview(),
                dashboardAPI.getUpcomingPayments(),
                dashboardAPI.getRecentActivity(),
            ]);

            setSummary(summaryRes.data);
            setProjectProgress(progressRes.data.projects || []);
            setCostBreakdown(costRes.data.breakdown || []);
            setInvestmentOverview(investRes.data || { byType: [], recentInvestments: [] });
            setUpcomingPayments(paymentRes.data.payments || []);
            setRecentActivity(activityRes.data.activities || []);
        } catch (error) {
            console.error('Dashboard load error:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="loading-spinner"><div className="spinner"></div></div>;
    }

    const s = summary;

    const costChartData = costBreakdown.map((item, i) => ({
        name: item.category?.name || 'Unknown',
        value: parseFloat(item.dataValues?.totalActual || item.totalActual || 0),
        color: CHART_COLORS[i % CHART_COLORS.length],
    })).filter(d => d.value > 0);

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Dashboard</h1>
                    <p className="page-subtitle">Overview of your real estate operations</p>
                </div>
            </div>

            {/* Stat Cards */}
            <div className="stats-grid">
                <div className="stat-card blue">
                    <div className="stat-icon blue"><HiOutlineOfficeBuilding /></div>
                    <div className="stat-value">{s?.projects?.total || 0}</div>
                    <div className="stat-label">Total Projects</div>
                    <div className="stat-change positive">
                        {s?.projects?.active || 0} Active • {s?.projects?.completed || 0} Completed
                    </div>
                </div>

                <div className="stat-card emerald">
                    <div className="stat-icon emerald"><HiOutlineCash /></div>
                    <div className="stat-value">{format(s?.financials?.totalInvestments || 0)}</div>
                    <div className="stat-label">Total Investments</div>
                </div>

                <div className="stat-card purple">
                    <div className="stat-icon purple"><HiOutlineTrendingUp /></div>
                    <div className="stat-value">{format(s?.financials?.totalBudget || 0)}</div>
                    <div className="stat-label">Total Budget</div>
                    <div className={`stat-change ${(s?.financials?.budgetVariance || 0) >= 0 ? 'positive' : 'negative'}`}>
                        {(s?.financials?.budgetVariance || 0) >= 0 ? <HiOutlineTrendingUp /> : <HiOutlineTrendingDown />}
                        {format(Math.abs(s?.financials?.budgetVariance || 0))} variance
                    </div>
                </div>

                <div className="stat-card amber">
                    <div className="stat-icon amber"><HiOutlineUserGroup /></div>
                    <div className="stat-value">{s?.people?.totalInvestors || 0}</div>
                    <div className="stat-label">Active Investors</div>
                </div>

                <div className="stat-card red">
                    <div className="stat-icon red"><HiOutlineExclamation /></div>
                    <div className="stat-value">{s?.payments?.overduePayments || 0}</div>
                    <div className="stat-label">Overdue Payments</div>
                </div>

                <div className="stat-card blue">
                    <div className="stat-icon cyan"><HiOutlineCheckCircle /></div>
                    <div className="stat-value">{format(s?.financials?.cashBalance || 0)}</div>
                    <div className="stat-label">Cash Balance</div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid-2" style={{ marginBottom: '20px' }}>
                {/* Cost Breakdown Chart */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <h3 className="card-title">Cost Breakdown</h3>
                            <p className="card-subtitle">Spending by category</p>
                        </div>
                    </div>
                    {costChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={costChartData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={3}
                                    dataKey="value"
                                >
                                    {costChartData.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        background: '#1e293b',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px',
                                        color: '#f1f5f9',
                                    }}
                                    formatter={(value) => format(value)}
                                />
                                <Legend
                                    verticalAlign="bottom"
                                    iconType="circle"
                                    iconSize={8}
                                    wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="empty-state">
                            <p>No cost data yet</p>
                        </div>
                    )}
                </div>

                {/* Project Progress */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <h3 className="card-title">Project Progress</h3>
                            <p className="card-subtitle">Active projects completion</p>
                        </div>
                    </div>
                    {projectProgress.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {projectProgress.map((p) => (
                                <div key={p.id}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                        <span style={{ fontSize: '14px', fontWeight: 500 }}>{p.name}</span>
                                        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{parseFloat(p.progress || 0).toFixed(0)}%</span>
                                    </div>
                                    <div className="progress-bar">
                                        <div
                                            className={`progress-fill ${parseFloat(p.progress) >= 80 ? 'emerald' : parseFloat(p.progress) >= 50 ? '' : 'amber'}`}
                                            style={{ width: `${Math.min(parseFloat(p.progress || 0), 100)}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>No active projects yet</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Row */}
            <div className="grid-2">
                {/* Upcoming Payments */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <h3 className="card-title">Upcoming Payments</h3>
                            <p className="card-subtitle">Due in the next 30 days</p>
                        </div>
                    </div>
                    {upcomingPayments.length > 0 ? (
                        <div className="table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Investor</th>
                                        <th>Project</th>
                                        <th>Amount</th>
                                        <th>Due Date</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {upcomingPayments.slice(0, 5).map((p) => (
                                        <tr key={p.id}>
                                            <td>{p.investor?.name}</td>
                                            <td>{p.project?.name}</td>
                                            <td>{format(p.amount)}</td>
                                            <td>{new Date(p.dueDate).toLocaleDateString()}</td>
                                            <td>
                                                <span className={`badge ${p.status === 'overdue' ? 'badge-red' : 'badge-amber'}`}>
                                                    {p.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="empty-state" style={{ padding: '30px' }}>
                            <p>No upcoming payments</p>
                        </div>
                    )}
                </div>

                {/* Recent Activity */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <h3 className="card-title">Recent Activity</h3>
                            <p className="card-subtitle">Latest actions in the system</p>
                        </div>
                    </div>
                    {recentActivity.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflow: 'auto' }}>
                            {recentActivity.slice(0, 10).map((a) => (
                                <div key={a.id} style={{
                                    display: 'flex', alignItems: 'center', gap: '12px',
                                    padding: '8px', borderRadius: '8px', background: 'var(--bg-glass)',
                                }}>
                                    <div style={{
                                        width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0,
                                        background: a.action === 'create' ? '#10b981' : a.action === 'delete' ? '#ef4444' : '#3b82f6',
                                    }} />
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: '13px', fontWeight: 500 }}>{a.description}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                            {a.user?.username || 'System'} • {new Date(a.createdAt).toLocaleString()}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state" style={{ padding: '30px' }}>
                            <p>No activity yet</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
