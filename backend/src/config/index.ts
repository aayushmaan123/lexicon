import dotenv from 'dotenv';
import { Environment, LogLevel, AppConfig } from '@lexicon/shared';

// Load environment variables
dotenv.config();

/**
 * Application configuration
 * 
 * Loads and validates configuration from environment variables.
 * Provides type-safe access to all configuration values.
 */
class Config {
  private static instance: Config;

  public readonly env: Environment;
  public readonly port: number;
  public readonly logLevel: LogLevel;

  private constructor() {
    this.env = (process.env.NODE_ENV as Environment) || 'development';
    this.port = parseInt(process.env.PORT || '3000', 10);
    this.logLevel = (process.env.LOG_LEVEL as LogLevel) || 'info';

    this.validate();
  }

  private validate(): void {
    const validEnvs: Environment[] = ['development', 'production', 'test'];
    if (!validEnvs.includes(this.env)) {
      throw new Error(`Invalid NODE_ENV: ${this.env}`);
    }

    if (isNaN(this.port) || this.port < 1 || this.port > 65535) {
      throw new Error(`Invalid PORT: ${this.port}`);
    }
  }

  public static getInstance(): Config {
    if (!Config.instance) {
      Config.instance = new Config();
    }
    return Config.instance;
  }

  public toAppConfig(): AppConfig {
    return {
      env: this.env,
      port: this.port,
      logLevel: this.logLevel,
    };
  }
}

export const config = Config.getInstance();
