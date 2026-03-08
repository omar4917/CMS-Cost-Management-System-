const router = require('express').Router();
const projectController = require('../controllers/projectController');
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

// Projects CRUD
router.get('/', projectController.getAll);
router.get('/:id', projectController.getById);
router.post('/', projectController.create);
router.put('/:id', projectController.update);
router.delete('/:id', projectController.delete);

// Project milestones
router.post('/:id/milestones', projectController.addMilestone);
router.put('/:projectId/milestones/:id', projectController.updateMilestone);
router.delete('/:projectId/milestones/:id', projectController.deleteMilestone);

// Project cost items
router.get('/:projectId/costs', costController.getProjectCosts);
router.post('/:projectId/costs', costController.createCostItem);

module.exports = router;
