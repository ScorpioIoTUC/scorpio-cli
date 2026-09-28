export type ComponentUpdateStatus = {
  installed_version: string;
  latest_version: string;
  need_to_update: boolean;
};

export type InfraUpdateStatus = {
  scorpio_cli: ComponentUpdateStatus;
  scorpio_project: ComponentUpdateStatus;
  ssh_active: boolean;
};

export type UpdatedComponentStatus = ComponentUpdateStatus & {
  updated: boolean;
};

export type InfraUpdateResult = {
  message: string;
  scorpio_cli: UpdatedComponentStatus;
  scorpio_project: UpdatedComponentStatus & {
    services_recreated: boolean;
  };
  ssh_active: boolean;
};
