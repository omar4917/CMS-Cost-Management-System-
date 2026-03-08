import { HiOutlineClock } from 'react-icons/hi';

export default function PlaceholderPage({ title, icon, description }) {
    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">{title}</h1>
                    <p className="page-subtitle">{description}</p>
                </div>
            </div>
            <div className="card">
                <div className="empty-state">
                    <div className="empty-state-icon"><HiOutlineClock /></div>
                    <h3>Coming Soon</h3>
                    <p>This section is being built and will be available shortly. All backend APIs are ready — the UI is being developed in phases.</p>
                </div>
            </div>
        </div>
    );
}
