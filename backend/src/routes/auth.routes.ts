import { Router, Request, Response } from 'express';
import { ApiResponse } from '@lexicon/shared';

const router = Router();

/**
 * POST /api/auth/login
 * 
 * TODO Phase 2: Implement actual authentication
 */
router.post('/login', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Authentication not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

/**
 * POST /api/auth/register
 * 
 * TODO Phase 2: Implement user registration
 */
router.post('/register', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Registration not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

/**
 * POST /api/auth/logout
 * 
 * TODO Phase 2: Implement logout
 */
router.post('/logout', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Logout not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

export default router;
