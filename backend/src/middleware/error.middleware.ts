import { Request, Response, NextFunction } from 'express';
import { ApiResponse } from '@lexicon/shared';
import { logger } from '../utils/logger';

/**
 * Global error handler middleware
 * 
 * Catches all errors and returns a standardized API response
 */
export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  logger.error('Error occurred:', err);

  const response: ApiResponse = {
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: err.message || 'An unexpected error occurred',
    },
    metadata: {
      timestamp: new Date(),
    },
  };

  res.status(500).json(response);
}

/**
 * 404 handler middleware
 * 
 * Returns a standardized not found response
 */
export function notFoundHandler(_req: Request, res: Response): void {
  const response: ApiResponse = {
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: 'The requested resource was not found',
    },
    metadata: {
      timestamp: new Date(),
    },
  };

  res.status(404).json(response);
}

/**
 * Request logger middleware
 * 
 * Logs all incoming requests
 */
export function requestLogger(req: Request, _res: Response, next: NextFunction): void {
  logger.info(`${req.method} ${req.path}`);
  next();
}
