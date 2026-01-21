export interface User {
  id: string;
  email: string;
  name: string;
  role: "user" | "admin" | "researcher";
  createdAt: Date;
  updatedAt: Date;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface RegisterData extends AuthCredentials {
  name: string;
}
