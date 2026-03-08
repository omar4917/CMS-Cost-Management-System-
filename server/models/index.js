const sequelize = require('../config/database');

// Import all models
const User = require('./User');
const Project = require('./Project');
const ProjectMilestone = require('./ProjectMilestone');
const CostCategory = require('./CostCategory');
const CostItem = require('./CostItem');
const InvestorType = require('./InvestorType');
const Investor = require('./Investor');
const Investment = require('./Investment');
const PaymentSchedule = require('./PaymentSchedule');
const Contractor = require('./Contractor');
const ContractorPayment = require('./ContractorPayment');
const Currency = require('./Currency');
const Document = require('./Document');
const EmailTemplate = require('./EmailTemplate');
const EmailLog = require('./EmailLog');
const EmailAutomationRule = require('./EmailAutomationRule');
const AuditLog = require('./AuditLog');
const Note = require('./Note');
const Setting = require('./Setting');

// ==================== ASSOCIATIONS ====================

// --- User associations ---
User.hasMany(Project, { foreignKey: 'createdBy', as: 'projects' });
User.hasMany(AuditLog, { foreignKey: 'userId', as: 'auditLogs' });
User.belongsTo(Investor, { foreignKey: 'investorId', as: 'investor' });

// --- Project associations ---
Project.belongsTo(User, { foreignKey: 'createdBy', as: 'creator' });
Project.hasMany(ProjectMilestone, { foreignKey: 'projectId', as: 'milestones', onDelete: 'CASCADE' });
Project.hasMany(CostItem, { foreignKey: 'projectId', as: 'costItems', onDelete: 'CASCADE' });
Project.hasMany(Investment, { foreignKey: 'projectId', as: 'investments', onDelete: 'CASCADE' });
Project.hasMany(PaymentSchedule, { foreignKey: 'projectId', as: 'paymentSchedules', onDelete: 'CASCADE' });
Project.hasMany(ContractorPayment, { foreignKey: 'projectId', as: 'contractorPayments', onDelete: 'CASCADE' });

// --- ProjectMilestone associations ---
ProjectMilestone.belongsTo(Project, { foreignKey: 'projectId', as: 'project' });

// --- CostCategory associations (self-referencing for hierarchy) ---
CostCategory.hasMany(CostCategory, { foreignKey: 'parentId', as: 'children' });
CostCategory.belongsTo(CostCategory, { foreignKey: 'parentId', as: 'parent' });
CostCategory.hasMany(CostItem, { foreignKey: 'categoryId', as: 'costItems' });

// --- CostItem associations ---
CostItem.belongsTo(Project, { foreignKey: 'projectId', as: 'project' });
CostItem.belongsTo(CostCategory, { foreignKey: 'categoryId', as: 'category' });
CostItem.belongsTo(User, { foreignKey: 'createdBy', as: 'creator' });
CostItem.belongsTo(User, { foreignKey: 'approvedBy', as: 'approver' });

// --- InvestorType associations ---
InvestorType.hasMany(Investor, { foreignKey: 'typeId', as: 'investors' });

// --- Investor associations ---
Investor.belongsTo(InvestorType, { foreignKey: 'typeId', as: 'type' });
Investor.hasMany(Investment, { foreignKey: 'investorId', as: 'investments', onDelete: 'CASCADE' });
Investor.hasMany(PaymentSchedule, { foreignKey: 'investorId', as: 'paymentSchedules', onDelete: 'CASCADE' });

// --- Investment associations ---
Investment.belongsTo(Investor, { foreignKey: 'investorId', as: 'investor' });
Investment.belongsTo(Project, { foreignKey: 'projectId', as: 'project' });
Investment.belongsTo(User, { foreignKey: 'createdBy', as: 'creator' });

// --- PaymentSchedule associations ---
PaymentSchedule.belongsTo(Investor, { foreignKey: 'investorId', as: 'investor' });
PaymentSchedule.belongsTo(Project, { foreignKey: 'projectId', as: 'project' });

// --- Contractor associations ---
Contractor.hasMany(ContractorPayment, { foreignKey: 'contractorId', as: 'payments', onDelete: 'CASCADE' });

// --- ContractorPayment associations ---
ContractorPayment.belongsTo(Contractor, { foreignKey: 'contractorId', as: 'contractor' });
ContractorPayment.belongsTo(Project, { foreignKey: 'projectId', as: 'project' });

// --- EmailTemplate associations ---
EmailTemplate.hasMany(EmailLog, { foreignKey: 'templateId', as: 'logs' });
EmailTemplate.hasMany(EmailAutomationRule, { foreignKey: 'templateId', as: 'automationRules' });

// --- EmailLog associations ---
EmailLog.belongsTo(EmailTemplate, { foreignKey: 'templateId', as: 'template' });
EmailLog.belongsTo(User, { foreignKey: 'sentBy', as: 'sender' });

// --- EmailAutomationRule associations ---
EmailAutomationRule.belongsTo(EmailTemplate, { foreignKey: 'templateId', as: 'template' });

// --- AuditLog associations ---
AuditLog.belongsTo(User, { foreignKey: 'userId', as: 'user' });

// --- Note associations ---
Note.belongsTo(User, { foreignKey: 'createdBy', as: 'author' });

module.exports = {
    sequelize,
    User,
    Project,
    ProjectMilestone,
    CostCategory,
    CostItem,
    InvestorType,
    Investor,
    Investment,
    PaymentSchedule,
    Contractor,
    ContractorPayment,
    Currency,
    Document,
    EmailTemplate,
    EmailLog,
    EmailAutomationRule,
    AuditLog,
    Note,
    Setting,
};
