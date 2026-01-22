import { Router } from 'express';
import healthRoutes from './health.routes';
import aiRoutes from './ai.routes';
import authRoutes from './auth.routes';
import documentRoutes from './document.routes';

const router = Router();

// Mount all routes
router.use('/health', healthRoutes);
router.use('/ai', aiRoutes);
router.use('/auth', authRoutes);
router.use('/documents', documentRoutes);

export default router;
