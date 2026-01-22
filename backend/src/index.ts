import { createApp } from './app';
import { config } from './config';
import { logger } from './utils/logger';

/**
 * Main server entry point
 */
async function startServer(): Promise<void> {
  try {
    const app = createApp();

    const server = app.listen(config.port, () => {
      logger.info(`Server started on port ${config.port}`);
      logger.info(`Environment: ${config.env}`);
      logger.info(`API available at: http://localhost:${config.port}/api`);
    });

    // Graceful shutdown
    const shutdown = (): void => {
      logger.info('Shutting down server...');
      server.close(() => {
        logger.info('Server closed');
        process.exit(0);
      });
    };

    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server
startServer();
