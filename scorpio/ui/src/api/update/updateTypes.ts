/** PyPI lookup result; unknown versions and optional errors are valid responses. */
export type ScorpioUpdateStatus = {
  current_version: string;
  latest_version: string;
  upload_time: string;
  need_to_update: boolean;
  error?: string;
};

/** Local CLI upgrade result; restart_required instructs the user to restart the UI. */
export type ScorpioUpdateResult = {
  message: string;
  previous_version: string;
  installed_version: string;
  restart_required: boolean;
};
