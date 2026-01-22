/**
 * User role types
 */
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest',
}

/**
 * User structure
 * 
 * TODO Phase 2: Implement actual authentication logic
 */
export interface User {
  id: string;
  email: string;
  role: UserRole;
  createdAt: Date;
  lastLoginAt?: Date;
}

/**
 * Authentication request
 */
export interface AuthRequest {
  email: string;
  password: string;
}

/**
 * Authentication response
 */
export interface AuthResponse {
  user: User;
  token: string;
  expiresAt: Date;
}

/**
 * Session information
 */
export interface Session {
  userId: string;
  token: string;
  expiresAt: Date;
  createdAt: Date;
}
