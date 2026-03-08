const express = require('express');
const router = express.Router();
const investorPortalController = require('../controllers/investorPortalController');
const { authenticate, authorize } = require('../middleware/auth');

// All routes in the investor portal require authentication
router.use(authenticate);

// Specific routes for the investor portal
router.get('/dashboard', investorPortalController.getDashboard);
router.get('/investments', investorPortalController.getInvestments);
router.get('/payments', investorPortalController.getPayments);
router.get('/projects/:id', investorPortalController.getProjectDetail);

module.exports = router;
