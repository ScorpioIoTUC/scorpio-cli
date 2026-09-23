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
