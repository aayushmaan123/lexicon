import { Router, Request, Response } from 'express';
import { ApiResponse, AgentQuery } from '@lexicon/shared';
import { aiService } from '../services/ai.service';

const router = Router();

/**
 * POST /api/ai/deepseek
 * 
 * Query DeepSeek AI agent
 */
router.post('/deepseek', async (req: Request, res: Response) => {
  try {
    const query: AgentQuery = {
      query: req.body.query,
      context: req.body.context,
      metadata: req.body.metadata,
    };

    if (!query.query) {
      const response: ApiResponse = {
        success: false,
        error: {
          code: 'INVALID_REQUEST',
          message: 'Query is required',
        },
      };
      return res.status(400).json(response);
    }

    const result = await aiService.queryDeepSeek(query);

    const response: ApiResponse = {
      success: true,
      data: result,
      metadata: {
        timestamp: new Date(),
      },
    };

    res.json(response);
  } catch (error) {
    const response: ApiResponse = {
      success: false,
      error: {
        code: 'AI_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
    };
    res.status(500).json(response);
  }
});

/**
 * POST /api/ai/search
 * 
 * Query Google RAG agent for document search
 */
router.post('/search', async (req: Request, res: Response) => {
  try {
    const query: AgentQuery = {
      query: req.body.query,
      context: req.body.context,
      metadata: req.body.metadata,
    };

    if (!query.query) {
      const response: ApiResponse = {
        success: false,
        error: {
          code: 'INVALID_REQUEST',
          message: 'Query is required',
        },
      };
      return res.status(400).json(response);
    }

    const result = await aiService.queryGoogleRAG(query);

    const response: ApiResponse = {
      success: true,
      data: result,
      metadata: {
        timestamp: new Date(),
      },
    };

    res.json(response);
  } catch (error) {
    const response: ApiResponse = {
      success: false,
      error: {
        code: 'SEARCH_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
    };
    res.status(500).json(response);
  }
});

export default router;
