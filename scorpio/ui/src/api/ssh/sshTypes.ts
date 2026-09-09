export type SshCredentials = {
  hostname: string;
  username: string;
  password: string;
};

export type SshSession = Pick<SshCredentials, "hostname" | "username">;
export type SshResponse = { message: string };
