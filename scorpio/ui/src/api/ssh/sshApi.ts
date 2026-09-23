import { endpoints } from "../endpoints";
import { requestJson } from "../http";
import type { SshCredentials, SshResponse } from "./sshTypes";

export const sshApi = {
  login(credentials: SshCredentials): Promise<SshResponse> {
    return requestJson<SshResponse>(endpoints.ssh.login, {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  },

  logout(): Promise<SshResponse> {
    return requestJson<SshResponse>(endpoints.ssh.logout, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },
};
