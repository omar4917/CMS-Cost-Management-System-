/**
 * Email Automation Cron Job
 * Runs on a schedule to:
 * 1. Send payment reminders for upcoming due dates
 * 2. Mark overdue payments
 * 3. Process automation rules
 */

const cron = require('node-cron');
const { Op } = require('sequelize');
const { PaymentSchedule, Investor, Project, Setting, EmailAutomationRule } = require('../models');
const { sendPaymentReminder } = require('./emailService');

function startEmailCron() {
    // Run every day at 8:00 AM
    cron.schedule('0 8 * * *', async () => {
        console.log('⏰ Running daily email automation...');
        await processPaymentReminders();
        await markOverduePayments();
    });

    console.log('📧 Email automation cron scheduled (daily at 8:00 AM)');
}

/**
 * Send reminders for payments due within X days
 */
async function processPaymentReminders() {
    try {
        // Get reminder days setting
        let reminderDays = 7;
        try {
            const setting = await Setting.findOne({ where: { key: 'payment_reminder_days' } });
            if (setting) reminderDays = parseInt(setting.value) || 7;
        } catch { }

        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + reminderDays);

        // Find pending payments due within reminder window
        const upcomingPayments = await PaymentSchedule.findAll({
            where: {
                status: 'pending',
                dueDate: { [Op.between]: [new Date(), futureDate] },
                reminderSent: { [Op.or]: [false, null] },
            },
            include: [
                { model: Investor, as: 'investor' },
                { model: Project, as: 'project' },
            ],
        });

        console.log(`  📬 Found ${upcomingPayments.length} upcoming payments to remind`);

        for (const payment of upcomingPayments) {
            if (!payment.investor?.email) continue;

            try {
                await sendPaymentReminder({
                    investor: payment.investor,
                    project: payment.project,
                    amount: payment.amount,
                    dueDate: payment.dueDate,
                });

                // Mark reminder as sent
                await payment.update({ reminderSent: true });
                console.log(`  ✅ Reminder sent to ${payment.investor.email}`);
            } catch (err) {
                console.error(`  ❌ Failed to send reminder: ${err.message}`);
            }
        }
    } catch (error) {
        console.error('Payment reminder error:', error.message);
    }
}

/**
 * Automatically mark overdue payments
 */
async function markOverduePayments() {
    try {
        const [count] = await PaymentSchedule.update(
            { status: 'overdue' },
            {
                where: {
                    status: 'pending',
                    dueDate: { [Op.lt]: new Date() },
                },
            }
        );
        if (count > 0) {
            console.log(`  ⚠️ Marked ${count} payments as overdue`);
        }
    } catch (error) {
        console.error('Mark overdue error:', error.message);
    }
}

module.exports = { startEmailCron, processPaymentReminders, markOverduePayments };
