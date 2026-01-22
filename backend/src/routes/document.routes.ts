import { Router, Request, Response } from 'express';
import { ApiResponse } from '@lexicon/shared';

const router = Router();

/**
 * POST /api/documents/upload
 * 
 * TODO Phase 2: Implement document upload and ingestion
 */
router.post('/upload', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Document upload not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

/**
 * GET /api/documents/search
 * 
 * TODO Phase 2: Implement document search
 */
router.get('/search', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Document search not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

/**
 * GET /api/documents/:id
 * 
 * TODO Phase 2: Implement document retrieval
 */
router.get('/:id', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Document retrieval not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

/**
 * DELETE /api/documents/:id
 * 
 * TODO Phase 2: Implement document deletion
 */
router.delete('/:id', (_req: Request, res: Response) => {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_IMPLEMENTED',
      message: 'Document deletion not implemented - Phase 2',
    },
  };
  res.status(501).json(response);
});

export default router;
