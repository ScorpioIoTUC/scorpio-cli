export type ScorpioUpdateStatus = {
  current_version: string;
  latest_version: string;
  upload_time: string;
  need_to_update: boolean;
  error?: string;
};

export type ScorpioUpdateResult = {
  message: string;
  previous_version: string;
  installed_version: string;
  restart_required: boolean;
};

export type ProjectUpdateStatus = {
  current_version: string;
  latest_version: string;
  need_to_update: boolean;
  ssh_active: boolean;
};

export type ProjectUpdateResult = {
  message: string;
  previous_version: string;
  installed_version: string;
  services_recreated: boolean;
};
