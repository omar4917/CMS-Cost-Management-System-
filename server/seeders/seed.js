const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });
const bcrypt = require('bcryptjs');
const sequelize = require('../config/database');

// Import all models to ensure associations are set up
const {
    User, CostCategory, InvestorType, Currency, Setting, EmailTemplate,
} = require('../models');

async function seed() {
    try {
        console.log('🌱 Starting database seeding...');

        // Sync database
        await sequelize.sync({ force: true });
        console.log('✅ Database tables created');

        // 1. Create default admin user
        const hashedPassword = await bcrypt.hash('admin123', 10);
        await User.create({
            username: 'admin',
            email: 'admin@cms.local',
            password: hashedPassword,
            firstName: 'System',
            lastName: 'Admin',
            role: 'superadmin',
            isActive: true,
        });
        console.log('✅ Default admin user created (admin / admin123)');

        // 2. Seed Cost Categories
        const categories = [
            { name: 'Land Acquisition & Registration', icon: '🏗️', description: 'Land purchase, registration, stamp duty', isDefault: true, sortOrder: 1 },
            { name: 'Construction - Materials', icon: '🧱', description: 'Cement, steel, bricks, sand, aggregate, timber', isDefault: true, sortOrder: 2 },
            { name: 'Construction - Labor', icon: '👷', description: 'Workers, masons, carpenters, painters wages', isDefault: true, sortOrder: 3 },
            { name: 'Construction - Equipment', icon: '🏗️', description: 'Crane, excavator, concrete mixer rental', isDefault: true, sortOrder: 4 },
            { name: 'Architectural & Engineering Fees', icon: '📐', description: 'Architect, structural engineer, MEP engineer', isDefault: true, sortOrder: 5 },
            { name: 'Interior Design & Finishing', icon: '🎨', description: 'Interior design, flooring, wall finish, ceiling', isDefault: true, sortOrder: 6 },
            { name: 'Electrical Works', icon: '⚡', description: 'Wiring, panels, switches, lighting, generator', isDefault: true, sortOrder: 7 },
            { name: 'Plumbing & Sanitary', icon: '🚿', description: 'Pipes, fittings, bathroom fixtures, water pump', isDefault: true, sortOrder: 8 },
            { name: 'HVAC Systems', icon: '❄️', description: 'Air conditioning, ventilation, heating', isDefault: true, sortOrder: 9 },
            { name: 'Elevator / Lift Installation', icon: '🛗', description: 'Elevator purchase, installation, maintenance', isDefault: true, sortOrder: 10 },
            { name: 'Fire Safety & Security', icon: '🔥', description: 'Fire alarm, sprinklers, CCTV, access control', isDefault: true, sortOrder: 11 },
            { name: 'Legal Fees & Documentation', icon: '⚖️', description: 'Lawyer fees, contracts, agreements, NOCs', isDefault: true, sortOrder: 12 },
            { name: 'Permits & Licenses', icon: '📋', description: 'Building permit, environmental clearance, NOC', isDefault: true, sortOrder: 13 },
            { name: 'Taxes & Duties', icon: '🏛️', description: 'VAT, capital gains tax, stamp duty, property tax', isDefault: true, sortOrder: 14 },
            { name: 'Insurance', icon: '🛡️', description: 'Construction insurance, property insurance, liability', isDefault: true, sortOrder: 15 },
            { name: 'Marketing & Sales', icon: '📢', description: 'Brochures, ads, commission, events, website', isDefault: true, sortOrder: 16 },
            { name: 'Utility Connections', icon: '🔌', description: 'Gas, water, electricity, internet, telephone', isDefault: true, sortOrder: 17 },
            { name: 'Landscaping & Exterior', icon: '🌳', description: 'Garden, walkways, boundary wall, gate', isDefault: true, sortOrder: 18 },
            { name: 'Parking & Common Areas', icon: '🅿️', description: 'Parking structure, lobby, corridors, stairs', isDefault: true, sortOrder: 19 },
            { name: 'Infrastructure', icon: '🛣️', description: 'Internal roads, drainage, sewage, water tank', isDefault: true, sortOrder: 20 },
            { name: 'Environmental & Soil Testing', icon: '🔬', description: 'Soil test, EIA, environmental compliance', isDefault: true, sortOrder: 21 },
            { name: 'Demolition Costs', icon: '💥', description: 'Demolition of existing structures', isDefault: true, sortOrder: 22 },
            { name: 'Project Management', icon: '📊', description: 'PM fees, supervision, site management', isDefault: true, sortOrder: 23 },
            { name: 'Financing Costs', icon: '🏦', description: 'Loan interest, bank charges, processing fees', isDefault: true, sortOrder: 24 },
            { name: 'Contingency Fund', icon: '💰', description: 'Emergency fund, unexpected costs, buffer', isDefault: true, sortOrder: 25 },
            { name: 'Furniture & Fixtures', icon: '🪑', description: 'Furniture, curtains, blinds for furnished units', isDefault: true, sortOrder: 26 },
            { name: 'Transportation & Logistics', icon: '🚛', description: 'Material transport, crane mobilization', isDefault: true, sortOrder: 27 },
            { name: 'Consultant & Advisory', icon: '💼', description: 'Consultants, advisors, specialists fees', isDefault: true, sortOrder: 28 },
            { name: 'Property Management Setup', icon: '🏢', description: 'Management office, staff, software setup', isDefault: true, sortOrder: 29 },
            { name: 'Miscellaneous', icon: '📦', description: 'Other uncategorized expenses', isDefault: true, sortOrder: 30 },
        ];

        await CostCategory.bulkCreate(categories);
        console.log(`✅ ${categories.length} cost categories seeded`);

        // 3. Seed Investor Types
        const investorTypes = [
            { name: 'Flat Investor', description: 'Invests in individual flat units', color: '#3b82f6' },
            { name: 'Building Investor', description: 'Invests in entire buildings', color: '#8b5cf6' },
            { name: 'Partner / Owner', description: 'Company partner or co-owner investing', color: '#f59e0b' },
            { name: 'Big Company', description: 'Corporate or institutional investor', color: '#10b981' },
            { name: 'Land Partner', description: 'Provides land as investment', color: '#ef4444' },
            { name: 'Silent Investor', description: 'Financial investor with no management role', color: '#6366f1' },
            { name: 'Other', description: 'Other investor categories', color: '#94a3b8' },
        ];

        await InvestorType.bulkCreate(investorTypes);
        console.log(`✅ ${investorTypes.length} investor types seeded`);

        // 4. Seed Currencies
        const currencies = [
            { code: 'BDT', name: 'Bangladeshi Taka', symbol: '৳', exchangeRateToBase: 1.000000, isBase: true, isActive: true },
            { code: 'USD', name: 'US Dollar', symbol: '$', exchangeRateToBase: 0.0084, isBase: false, isActive: true },
            { code: 'EUR', name: 'Euro', symbol: '€', exchangeRateToBase: 0.0077, isBase: false, isActive: true },
            { code: 'GBP', name: 'British Pound', symbol: '£', exchangeRateToBase: 0.0066, isBase: false, isActive: true },
            { code: 'INR', name: 'Indian Rupee', symbol: '₹', exchangeRateToBase: 0.70, isBase: false, isActive: true },
            { code: 'SAR', name: 'Saudi Riyal', symbol: '﷼', exchangeRateToBase: 0.031, isBase: false, isActive: true },
            { code: 'AED', name: 'UAE Dirham', symbol: 'د.إ', exchangeRateToBase: 0.031, isBase: false, isActive: true },
            { code: 'MYR', name: 'Malaysian Ringgit', symbol: 'RM', exchangeRateToBase: 0.037, isBase: false, isActive: true },
            { code: 'SGD', name: 'Singapore Dollar', symbol: 'S$', exchangeRateToBase: 0.011, isBase: false, isActive: true },
            { code: 'CNY', name: 'Chinese Yuan', symbol: '¥', exchangeRateToBase: 0.061, isBase: false, isActive: true },
        ];

        await Currency.bulkCreate(currencies);
        console.log(`✅ ${currencies.length} currencies seeded`);

        // 5. Seed Default Settings
        const settings = [
            { key: 'company_name', value: 'Houzez Real Estate', category: 'general', description: 'Company name' },
            { key: 'company_email', value: 'info@houzez.com', category: 'general', description: 'Company email' },
            { key: 'company_phone', value: '+880-1234-567890', category: 'general', description: 'Company phone' },
            { key: 'company_address', value: 'Dhaka, Bangladesh', category: 'general', description: 'Company address' },
            { key: 'base_currency', value: 'BDT', category: 'financial', description: 'Base currency code' },
            { key: 'tax_rate', value: '15', category: 'financial', description: 'Default tax rate (%)' },
            { key: 'fiscal_year_start', value: '07', category: 'financial', description: 'Fiscal year start month' },
            { key: 'email_notifications', value: 'true', category: 'email', description: 'Enable email notifications' },
            { key: 'auto_email_on_investment', value: 'true', category: 'email', description: 'Auto-send email on new investment' },
            { key: 'payment_reminder_days', value: '7', category: 'email', description: 'Days before due date to send reminder' },
        ];

        await Setting.bulkCreate(settings);
        console.log(`✅ ${settings.length} default settings seeded`);

        // 6. Seed Default Email Templates
        const templates = [
            {
                name: 'Investment Received',
                subject: 'Investment Confirmation - {{projectName}}',
                bodyHtml: `<h2>Investment Confirmation</h2>
<p>Dear {{investorName}},</p>
<p>We are pleased to confirm your investment of <strong>{{amount}} {{currency}}</strong> in the project <strong>{{projectName}}</strong>.</p>
<p><strong>Details:</strong></p>
<ul>
<li>Date: {{date}}</li>
<li>Payment Method: {{paymentMethod}}</li>
<li>Reference: {{referenceNo}}</li>
</ul>
<p>Thank you for your trust in us.</p>
<p>Best regards,<br>{{companyName}}</p>`,
                triggerType: 'investment_received',
                variables: ['investorName', 'amount', 'currency', 'projectName', 'date', 'paymentMethod', 'referenceNo', 'companyName'],
                isActive: true,
            },
            {
                name: 'Payment Reminder',
                subject: 'Payment Reminder - {{projectName}}',
                bodyHtml: `<h2>Payment Reminder</h2>
<p>Dear {{investorName}},</p>
<p>This is a friendly reminder that your payment of <strong>{{amount}} {{currency}}</strong> for the project <strong>{{projectName}}</strong> is due on <strong>{{dueDate}}</strong>.</p>
<p>Please ensure timely payment to avoid any delays.</p>
<p>Best regards,<br>{{companyName}}</p>`,
                triggerType: 'payment_reminder',
                variables: ['investorName', 'amount', 'currency', 'projectName', 'dueDate', 'companyName'],
                isActive: true,
            },
            {
                name: 'Project Milestone Reached',
                subject: '🎉 {{projectName}} has reached {{milestone}}%!',
                bodyHtml: `<h2>Project Milestone Update</h2>
<p>Dear {{investorName}},</p>
<p>We are excited to inform you that <strong>{{projectName}}</strong> has reached <strong>{{milestone}}%</strong> completion!</p>
<p>{{milestoneDetails}}</p>
<p>Thank you for your continued support.</p>
<p>Best regards,<br>{{companyName}}</p>`,
                triggerType: 'milestone_reached',
                variables: ['investorName', 'projectName', 'milestone', 'milestoneDetails', 'companyName'],
                isActive: true,
            },
            {
                name: 'Project Plan Changed',
                subject: 'Important Update - {{projectName}}',
                bodyHtml: `<h2>Project Plan Update</h2>
<p>Dear {{investorName}},</p>
<p>We would like to inform you about changes in the project plan for <strong>{{projectName}}</strong>.</p>
<p><strong>Changes:</strong></p>
<p>{{changeDetails}}</p>
<p>Please contact us if you have any questions.</p>
<p>Best regards,<br>{{companyName}}</p>`,
                triggerType: 'plan_changed',
                variables: ['investorName', 'projectName', 'changeDetails', 'companyName'],
                isActive: true,
            },
            {
                name: 'Cost Change Notification',
                subject: 'Cost Update - {{projectName}}',
                bodyHtml: `<h2>Cost Update Notification</h2>
<p>Dear {{recipientName}},</p>
<p>The cost for <strong>{{projectName}}</strong> has been {{changeType}}.</p>
<p><strong>Previous Budget:</strong> {{oldAmount}} {{currency}}</p>
<p><strong>New Budget:</strong> {{newAmount}} {{currency}}</p>
<p><strong>Reason:</strong> {{reason}}</p>
<p>Best regards,<br>{{companyName}}</p>`,
                triggerType: 'cost_increased',
                variables: ['recipientName', 'projectName', 'changeType', 'oldAmount', 'newAmount', 'currency', 'reason', 'companyName'],
                isActive: true,
            },
        ];

        await EmailTemplate.bulkCreate(templates);
        console.log(`✅ ${templates.length} email templates seeded`);

        console.log('\n🎉 Database seeding completed successfully!');
        console.log('📧 Default admin: admin / admin123');
        process.exit(0);
    } catch (error) {
        console.error('❌ Seeding failed:', error);
        process.exit(1);
    }
}

seed();
