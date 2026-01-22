/**
 * Environment configuration type
 */
export type Environment = 'development' | 'production' | 'test';

/**
 * Log level types
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Application configuration
 */
export interface AppConfig {
  env: Environment;
  port: number;
  logLevel: LogLevel;
}
