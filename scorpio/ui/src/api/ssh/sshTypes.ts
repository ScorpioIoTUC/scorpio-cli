/** Login payload sent to the server; never persist the password in UI storage. */
export type SshCredentials = {
  hostname: string;
  username: string;
  password: string;
};

/** Browser session stores only host and user after a successful login. */
export type SshSession = Pick<SshCredentials, "hostname" | "username">;
export type SshResponse = { message: string };
