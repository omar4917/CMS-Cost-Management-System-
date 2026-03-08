import { NavLink, useLocation } from 'react-router-dom';
import {
    HiOutlineHome, HiOutlineOfficeBuilding, HiOutlineCash,
    HiOutlineUserGroup, HiOutlineMail, HiOutlineDocumentText,
    HiOutlineCog, HiOutlineChartBar, HiOutlineClipboardList,
    HiOutlineTruck, HiOutlineCreditCard, HiOutlineClock,
    HiOutlineDatabase, HiOutlineShieldCheck,
} from 'react-icons/hi';

const sidebarLinks = [
    { section: 'Main' },
    { to: '/', icon: HiOutlineHome, label: 'Dashboard' },
    { to: '/projects', icon: HiOutlineOfficeBuilding, label: 'Projects' },

    { section: 'Financial' },
    { to: '/investors', icon: HiOutlineUserGroup, label: 'Investors' },
    { to: '/investments', icon: HiOutlineCash, label: 'Investments' },
    { to: '/payment-schedules', icon: HiOutlineCreditCard, label: 'Payment Schedules' },
    { to: '/cost-categories', icon: HiOutlineClipboardList, label: 'Cost Categories' },

    { section: 'Operations' },
    { to: '/contractors', icon: HiOutlineTruck, label: 'Contractors' },
    { to: '/documents', icon: HiOutlineDocumentText, label: 'Documents' },

    { section: 'Communication' },
    { to: '/emails', icon: HiOutlineMail, label: 'Email System' },

    { section: 'Reports & Tools' },
    { to: '/reports', icon: HiOutlineChartBar, label: 'Reports & Analytics' },
    { to: '/audit-logs', icon: HiOutlineClock, label: 'Audit Trail' },
    { to: '/backup', icon: HiOutlineDatabase, label: 'Backup' },

    { section: 'Administration' },
    { to: '/settings', icon: HiOutlineCog, label: 'Settings' },
    { to: '/users', icon: HiOutlineShieldCheck, label: 'User Management' },
];

export default function Sidebar() {
    const location = useLocation();

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">C</div>
                <div>
                    <div className="sidebar-logo-text">CMS</div>
                    <div className="sidebar-logo-sub">Cost Management</div>
                </div>
            </div>

            <nav className="sidebar-nav">
                {sidebarLinks.map((item, i) => {
                    if (item.section) {
                        return <div key={i} className="sidebar-section-title">{item.section}</div>;
                    }

                    const Icon = item.icon;
                    const isActive = location.pathname === item.to ||
                        (item.to !== '/' && location.pathname.startsWith(item.to));

                    return (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={`sidebar-link ${isActive ? 'active' : ''}`}
                        >
                            <span className="sidebar-link-icon"><Icon /></span>
                            <span>{item.label}</span>
                        </NavLink>
                    );
                })}
            </nav>
        </aside>
    );
}
