import { z } from "zod";

/**
 * Validation schemas and utility functions
 */

export const emailSchema = z.string().email("Invalid email address");

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
  .regex(/[a-z]/, "Password must contain at least one lowercase letter")
  .regex(/[0-9]/, "Password must contain at least one number");

export const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: emailSchema,
  password: passwordSchema,
});

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});

export const searchQuerySchema = z.object({
  query: z.string().min(1, "Search query is required"),
  filters: z
    .object({
      category: z.array(z.string()).optional(),
      jurisdiction: z.array(z.string()).optional(),
      dateRange: z
        .object({
          start: z.date(),
          end: z.date(),
        })
        .optional(),
    })
    .optional(),
  options: z
    .object({
      limit: z.number().positive().optional(),
      offset: z.number().nonnegative().optional(),
      sortBy: z.enum(["relevance", "date"]).optional(),
    })
    .optional(),
});
