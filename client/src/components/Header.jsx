import { useAuth } from '../context/AuthContext';
import { useCurrency } from '../context/CurrencyContext';
import { HiOutlineLogout, HiOutlineBell } from 'react-icons/hi';
import { useLocation, useNavigate } from 'react-router-dom';

const pageTitles = {
    '/': 'Dashboard',
    '/projects': 'Projects',
    '/investors': 'Investors',
    '/investments': 'Investments',
    '/payment-schedules': 'Payment Schedules',
    '/cost-categories': 'Cost Categories',
    '/contractors': 'Contractors',
    '/documents': 'Documents',
    '/emails': 'Email System',
    '/reports': 'Reports & Analytics',
    '/audit-logs': 'Audit Trail',
    '/backup': 'Database Backup',
    '/settings': 'Settings',
    '/users': 'User Management',
};

export default function Header() {
    const { user, logout } = useAuth();
    const { currencies, selectedCurrency, changeCurrency } = useCurrency();
    const location = useLocation();
    const navigate = useNavigate();

    const title = pageTitles[location.pathname] || 'CMS';
    const initials = user ? (user.firstName?.[0] || user.username[0]).toUpperCase() : 'A';

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <header className="header">
            <div className="header-left">
                <h2 className="header-title">{title}</h2>
            </div>

            <div className="header-right">
                <select
                    className="currency-select"
                    value={selectedCurrency}
                    onChange={(e) => changeCurrency(e.target.value)}
                >
                    {currencies.map(c => (
                        <option key={c.code} value={c.code}>
                            {c.symbol} {c.code}
                        </option>
                    ))}
                    {currencies.length === 0 && (
                        <>
                            <option value="BDT">৳ BDT</option>
                            <option value="USD">$ USD</option>
                            <option value="EUR">€ EUR</option>
                        </>
                    )}
                </select>

                <button className="header-btn">
                    <HiOutlineBell />
                </button>

                <div className="header-user">
                    <div className="header-avatar">{initials}</div>
                    <div>
                        <div className="header-user-name">{user?.firstName || user?.username}</div>
                        <div className="header-user-role">{user?.role}</div>
                    </div>
                </div>

                <button className="header-btn" onClick={handleLogout} title="Logout">
                    <HiOutlineLogout />
                </button>
            </div>
        </header>
    );
}
