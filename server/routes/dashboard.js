const router = require('express').Router();
const dashboardController = require('../controllers/dashboardController');
const { auth } = require('../middleware/auth');

router.use(auth);
router.get('/summary', dashboardController.getSummary);
router.get('/recent-activity', dashboardController.getRecentActivity);
router.get('/project-progress', dashboardController.getProjectProgress);
router.get('/cost-breakdown', dashboardController.getCostBreakdown);
router.get('/investment-overview', dashboardController.getInvestmentOverview);
router.get('/upcoming-payments', dashboardController.getUpcomingPayments);

module.exports = router;
