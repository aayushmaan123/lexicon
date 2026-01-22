import {
  AIAgent,
  AgentType,
  AgentConfig,
  AgentQuery,
  AgentResponse,
} from '@lexicon/shared';
import { logger } from '../utils/logger';

/**
 * Base abstract class for all AI agents
 * 
 * Provides common functionality and enforces the AIAgent interface
 */
export abstract class BaseAgent implements AIAgent {
  public readonly agentType: AgentType;
  protected ready: boolean = false;
  protected config?: AgentConfig;

  constructor(agentType: AgentType) {
    this.agentType = agentType;
  }

  public abstract initialize(config: AgentConfig): Promise<void>;
  public abstract execute(query: AgentQuery): Promise<AgentResponse>;

  public isReady(): boolean {
    return this.ready;
  }

  protected validateConfig(config: AgentConfig): void {
    if (!config) {
      throw new Error('Agent configuration is required');
    }
  }

  protected logExecution(query: AgentQuery): void {
    logger.debug(`[${this.agentType}] Executing query:`, query.query);
  }
}
