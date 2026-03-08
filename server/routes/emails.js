const router = require('express').Router();
const { auth } = require('../middleware/auth');
const { EmailTemplate, EmailLog, EmailAutomationRule, User } = require('../models');
const { sendEmail, sendTemplateEmail } = require('../services/emailService');

router.use(auth);

// ============ SEND EMAIL ============

// Send a custom email
router.post('/send', async (req, res) => {
    try {
        const { to, subject, body, templateId } = req.body;

        if (!to) return res.status(400).json({ message: 'Recipient email is required' });

        let result;
        if (templateId) {
            result = await sendTemplateEmail({
                templateId,
                to: to.split(',').map(e => e.trim()),
                variables: req.body.variables || {},
                userId: req.user.id,
            });
        } else {
            if (!subject) return res.status(400).json({ message: 'Subject is required' });
            result = await sendEmail({
                to: to.split(',').map(e => e.trim()),
                subject,
                html: body,
                userId: req.user.id,
            });
        }

        res.json({ message: `Email ${result.status}`, result });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// ============ TEMPLATES ============

// Get all templates
router.get('/templates', async (req, res) => {
    const templates = await EmailTemplate.findAll({ order: [['name', 'ASC']] });
    res.json({ templates });
});

// Create template
router.post('/templates', async (req, res) => {
    try {
        const template = await EmailTemplate.create(req.body);
        res.status(201).json({ template });
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
});

// Update template
router.put('/templates/:id', async (req, res) => {
    try {
        const template = await EmailTemplate.findByPk(req.params.id);
        if (!template) return res.status(404).json({ message: 'Template not found' });
        await template.update(req.body);
        res.json({ template });
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
});

// Delete template
router.delete('/templates/:id', async (req, res) => {
    const template = await EmailTemplate.findByPk(req.params.id);
    if (!template) return res.status(404).json({ message: 'Template not found' });
    await template.destroy();
    res.json({ message: 'Template deleted' });
});

// ============ LOGS ============

// Get email logs
router.get('/logs', async (req, res) => {
    const { page = 1, limit = 50, status } = req.query;
    const where = {};
    if (status) where.status = status;

    const offset = (parseInt(page) - 1) * parseInt(limit);
    const { rows: logs, count: total } = await EmailLog.findAndCountAll({
        where,
        order: [['createdAt', 'DESC']],
        limit: parseInt(limit),
        offset,
    });
    res.json({ logs, total, page: parseInt(page), pages: Math.ceil(total / parseInt(limit)) });
});

// ============ AUTOMATION RULES ============

// Get all automation rules
router.get('/automation-rules', async (req, res) => {
    const rules = await EmailAutomationRule.findAll({
        include: [{ model: EmailTemplate, as: 'template', attributes: ['name', 'subject'] }],
        order: [['createdAt', 'DESC']],
    });
    res.json({ rules });
});

// Create automation rule
router.post('/automation-rules', async (req, res) => {
    try {
        const rule = await EmailAutomationRule.create(req.body);
        res.status(201).json({ rule });
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
});

// Update automation rule
router.put('/automation-rules/:id', async (req, res) => {
    try {
        const rule = await EmailAutomationRule.findByPk(req.params.id);
        if (!rule) return res.status(404).json({ message: 'Rule not found' });
        await rule.update(req.body);
        res.json({ rule });
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
});

// Toggle automation rule active/inactive
router.patch('/automation-rules/:id/toggle', async (req, res) => {
    const rule = await EmailAutomationRule.findByPk(req.params.id);
    if (!rule) return res.status(404).json({ message: 'Rule not found' });
    await rule.update({ isActive: !rule.isActive });
    res.json({ rule, message: `Rule ${rule.isActive ? 'activated' : 'deactivated'}` });
});

// Delete automation rule
router.delete('/automation-rules/:id', async (req, res) => {
    const rule = await EmailAutomationRule.findByPk(req.params.id);
    if (!rule) return res.status(404).json({ message: 'Rule not found' });
    await rule.destroy();
    res.json({ message: 'Rule deleted' });
});

module.exports = router;
