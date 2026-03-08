/**
 * Email Service — Nodemailer Gmail SMTP
 * Handles sending individual and template-based emails,
 * variable substitution, and logging all sent/failed emails.
 */

const nodemailer = require('nodemailer');
const { EmailLog, EmailTemplate, Setting } = require('../models');

// Create transporter
let transporter = null;

function getTransporter() {
    if (!transporter) {
        const user = process.env.GMAIL_USER;
        const pass = process.env.GMAIL_APP_PASSWORD;

        if (!user || !pass) {
            console.warn('⚠️  Gmail credentials not set in .env — emails will be logged but not sent');
            return null;
        }

        transporter = nodemailer.createTransport({
            service: 'gmail',
            auth: { user, pass },
        });
    }
    return transporter;
}

/**
 * Replace template variables like {{investorName}} with actual values
 */
function substituteVariables(text, variables = {}) {
    if (!text) return '';
    return text.replace(/\{\{(\w+)\}\}/g, (match, key) => {
        return variables[key] !== undefined ? variables[key] : match;
    });
}

/**
 * Send a raw email (not template-based)
 */
async function sendEmail({ to, subject, html, text, userId }) {
    const transport = getTransporter();
    const recipients = Array.isArray(to) ? to.join(', ') : to;

    const logData = {
        recipientEmail: recipients,
        subject,
        bodyHtml: html || text,
        sentBy: userId,
        status: 'pending',
    };

    try {
        if (transport) {
            await transport.sendMail({
                from: `"${process.env.COMPANY_NAME || 'CMS'}" <${process.env.GMAIL_USER}>`,
                to: recipients,
                subject,
                html: html || undefined,
                text: text || undefined,
            });
            logData.status = 'sent';
            logData.sentAt = new Date();
        } else {
            // No SMTP configured — log only
            logData.status = 'logged';
            logData.errorMessage = 'SMTP not configured — email logged but not sent';
        }
    } catch (error) {
        logData.status = 'failed';
        logData.errorMessage = error.message;
        console.error('Email send error:', error.message);
    }

    // Log email
    try {
        await EmailLog.create(logData);
    } catch (e) {
        console.error('Email log error:', e.message);
    }

    return logData;
}

/**
 * Send a template-based email with variable substitution
 */
async function sendTemplateEmail({ templateId, templateName, to, variables = {}, userId }) {
    // Find template
    let template;
    if (templateId) {
        template = await EmailTemplate.findByPk(templateId);
    } else if (templateName) {
        template = await EmailTemplate.findOne({ where: { name: templateName } });
    }

    if (!template) {
        throw new Error(`Email template not found: ${templateId || templateName}`);
    }

    // Add company settings to variables
    try {
        const companyName = await Setting.findOne({ where: { key: 'company_name' } });
        if (companyName) variables.companyName = companyName.value;
    } catch { }

    // Substitute variables
    const subject = substituteVariables(template.subject, variables);
    const html = substituteVariables(template.bodyHtml, variables);

    return sendEmail({ to, subject, html, userId });
}

/**
 * Send investment notification emails
 * Called automatically when a new investment is recorded
 */
async function sendInvestmentNotification({ investor, project, amount, paymentMethod, referenceNo, userId }) {
    const variables = {
        investorName: investor.name,
        projectName: project.name,
        amount: parseFloat(amount).toLocaleString(),
        currency: 'BDT',
        date: new Date().toLocaleDateString(),
        paymentMethod: paymentMethod || 'N/A',
        referenceNo: referenceNo || 'N/A',
    };

    const recipients = [];
    if (investor.email) recipients.push(investor.email);

    // Also send to company email
    try {
        const companyEmail = await Setting.findOne({ where: { key: 'company_email' } });
        if (companyEmail?.value) recipients.push(companyEmail.value);
    } catch { }

    if (recipients.length === 0) return null;

    return sendTemplateEmail({
        templateName: 'Investment Received',
        to: recipients,
        variables,
        userId,
    });
}

/**
 * Send payment reminder emails
 * Called by cron job for upcoming/overdue payments
 */
async function sendPaymentReminder({ investor, project, amount, dueDate, userId }) {
    if (!investor.email) return null;

    return sendTemplateEmail({
        templateName: 'Payment Reminder',
        to: investor.email,
        variables: {
            investorName: investor.name,
            projectName: project.name,
            amount: parseFloat(amount).toLocaleString(),
            currency: 'BDT',
            dueDate: new Date(dueDate).toLocaleDateString(),
        },
        userId,
    });
}

/**
 * Send milestone notification
 */
async function sendMilestoneNotification({ project, milestone, milestoneDetails, investorEmails, userId }) {
    if (!investorEmails || investorEmails.length === 0) return null;

    return sendTemplateEmail({
        templateName: 'Project Milestone Reached',
        to: investorEmails,
        variables: {
            projectName: project.name,
            milestone: String(milestone),
            milestoneDetails: milestoneDetails || `Project has reached ${milestone}% completion.`,
            investorName: 'Valued Investor',
        },
        userId,
    });
}

module.exports = {
    sendEmail,
    sendTemplateEmail,
    sendInvestmentNotification,
    sendPaymentReminder,
    sendMilestoneNotification,
    substituteVariables,
};
