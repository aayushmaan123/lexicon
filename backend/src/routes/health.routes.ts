import { Router, Request, Response } from 'express';
import { ApiResponse } from '@lexicon/shared';

const router = Router();

/**
 * Health check endpoint
 * Mounted at /api/health/ so this becomes /api/health
 */
router.get('/', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: true,
    data: {
      status: 'ok',
      timestamp: new Date(),
      version: '1.0.0',
    },
  };
  res.json(response);
});

/**
 * Status endpoint with more details
 */
router.get('/status', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: true,
    data: {
      status: 'ok',
      environment: process.env.NODE_ENV || 'development',
      timestamp: new Date(),
      services: {
        api: 'operational',
        agents: 'ready', // TODO Phase 2: Check actual agent status
        database: 'not_configured', // TODO Phase 2: Check database connection
      },
    },
  };
  res.json(response);
});

export default router;
